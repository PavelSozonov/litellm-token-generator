"""
Token‑generator micro‑service
─────────────────────────────
 * LDAP authentication
 * LiteLLM user / key management + team membership
 * Local Postgres cache (single token per LDAP account)
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ldap3 import ALL, SUBTREE, Connection, Server
from pydantic import BaseModel
from sqlalchemy import Column, DateTime, String, DDL, event, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Session

# ───────────────────  LOGGING  ────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("token-generator")

# ───────────────────  ENV VARS  ───────────────────
LDAP_HOST = os.getenv("LDAP_SERVER_HOST", "ldap")
LDAP_PORT = int(os.getenv("LDAP_SERVER_PORT", "389"))
LDAP_BIND_DN = os.getenv("LDAP_BIND_DN")
LDAP_BIND_PASSWORD = os.getenv("LDAP_BIND_PASSWORD")
LDAP_SEARCH_BASE = os.getenv("LDAP_SEARCH_BASE", "ou=users,dc=example,dc=com")

LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL", "http://litellm:4000")
LITELLM_MASTER_KEY = os.getenv("LITELLM_MASTER_KEY", "sk-1234")
TEAM_ID = TEAM_ALIAS = "All_Company"

DB_TOKEN_URL = os.getenv(
    "DB_TOKEN_URL", "postgresql://admin:pass@db-token:5432/token_db"
)

# ────────────────  SQLAlchemy setup  ──────────────
class Base(DeclarativeBase):
    """SQLAlchemy 2.x base."""
    pass


class TokenRow(Base):
    __tablename__ = "issued_tokens"

    uuid = Column(String, primary_key=True)
    username = Column(String, nullable=False, unique=True)  # <= UNIQUE
    email = Column(String, nullable=False)
    department = Column(String, nullable=False, index=True)
    token = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)


# ──────────────────────────────────────────────────────────────────────────────
# fire a CREATE INDEX IF NOT EXISTS after the table is created
event.listen(
    TokenRow.__table__,
    'after_create',
    DDL(
        "CREATE INDEX IF NOT EXISTS ix_issued_tokens_department "
        "ON issued_tokens (department)"
    )
)


engine = create_engine(DB_TOKEN_URL, pool_pre_ping=True)

# ────────────────  FastAPI wiring  ────────────────
app = FastAPI(title="Token Generator")


class AuthRequest(BaseModel):
    login: str
    password: str


class AuthResponse(BaseModel):
    sAMAccountName: str
    email: str
    department: str

# ─────── CORS ───────
# read an env var (set this in your docker-compose.dev.yml or on your host)
APP_ENV = os.getenv("APP_ENV", "production").lower()

if APP_ENV == "development":
    # allow only your React dev server
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ────────────────────  LDAP  ──────────────────────
def get_ldap_connection() -> Connection:
    server = Server(LDAP_HOST, port=LDAP_PORT, get_info=ALL)
    return Connection(server, LDAP_BIND_DN, LDAP_BIND_PASSWORD, auto_bind=True)


def authenticate_user(login: str, password: str) -> AuthResponse:
    """Bind against LDAP; return core attributes or raise HTTP errors."""
    conn = get_ldap_connection()
    identifier = login.strip()

    conn.search(
        search_base=LDAP_SEARCH_BASE,
        search_filter=f"(|(uid={identifier})(mail={identifier}))",
        search_scope=SUBTREE,
        attributes=["uid", "mail", "departmentNumber"],
    )
    if not conn.entries:
        raise HTTPException(404, "User not found")

    entry = conn.entries[0]

    # verify credentials
    try:
        Connection(
            Server(LDAP_HOST, port=LDAP_PORT, get_info=ALL),
            user=entry.entry_dn,
            password=password,
            auto_bind=True,
        )
    except Exception:  # pragma: no cover
        raise HTTPException(401, "Invalid credentials")

    # normalize multi-valued LDAP attributes
    def _first(val):
        return val[0] if isinstance(val, (list, tuple)) else val

    return AuthResponse(
        sAMAccountName=_first(entry.uid.value),
        email=_first(entry.mail.value),
        department=_first(entry.departmentNumber.value),
    )


# ─────────────  START-UP TASKS (idempotent)  ─────────────
@app.on_event("startup")
def startup_tasks() -> None:
    Base.metadata.create_all(engine)

    headers = {"Authorization": f"Bearer {LITELLM_MASTER_KEY}"}
    team_info = f"{LITELLM_BASE_URL}/team/info"
    team_new = f"{LITELLM_BASE_URL}/team/new"
    models_ep = f"{LITELLM_BASE_URL}/v1/models"
    add_models = f"{LITELLM_BASE_URL}/team/model/add"

    try:
        r = httpx.get(team_info, headers=headers, params={"team_id": TEAM_ID}, timeout=5)
    except Exception as exc:  # pragma: no cover
        logger.error("LiteLLM unreachable on startup: %s", exc)
        return

    if r.status_code == 404:
        logger.info("Creating default team %s", TEAM_ID)
        httpx.post(
            team_new,
            headers=headers,
            json={"team_id": TEAM_ID, "team_alias": TEAM_ALIAS},
            timeout=5,
        ).raise_for_status()
        r = httpx.get(team_info, headers=headers, params={"team_id": TEAM_ID}, timeout=5)

    if r.status_code != 200:  # pragma: no cover
        logger.warning("Unexpected /team/info %s: %s", r.status_code, r.text)
        return

    current_models = set(
        r.json().get("models", []) or r.json().get("allowed_models", [])
    )

    try:
        all_models = {
            m["id"]
            for m in httpx.get(models_ep, headers=headers, timeout=5)
            .json()
            .get("data", [])
        }
    except Exception as exc:  # pragma: no cover
        logger.error("Couldn't fetch model list: %s", exc)
        return

    missing = [m for m in all_models if m.startswith("GenAI/") and m not in current_models]
    if missing:
        httpx.post(
            add_models,
            headers=headers,
            json={"team_id": TEAM_ID, "models": sorted(missing)},
            timeout=5,
        ).raise_for_status()
        logger.info("Added %d GenAI/* models to %s", len(missing), TEAM_ID)


# ─────────────────  ROUTES  ───────────────────
@app.post("/authenticate", response_model=AuthResponse)
def authenticate(req: AuthRequest):
    logger.info("AUTH %s", req.login)
    return authenticate_user(req.login, req.password)


@app.post("/token")
def issue_token(req: AuthRequest):
    """
    Single‑token guarantee:

    * If a row for `username` exists → return it.
    * Otherwise create LiteLLM key, store row (unique constraint
      protects against race conditions), return new key.
    """
    user = authenticate_user(req.login, req.password)

    # 1. Try cache first
    with Session(engine) as db:
        token_row = db.execute(
            select(TokenRow).where(TokenRow.username == user.sAMAccountName)
        ).scalar_one_or_none()
        if token_row:
            logger.info("Token reuse for %s", user.sAMAccountName)
            return {"token": token_row.token, "user": user.dict()}

    # 2. Mint key via LiteLLM
    headers = {
        "Authorization": f"Bearer {LITELLM_MASTER_KEY}",
        "Content-Type": "application/json",
    }
    with httpx.Client() as cli:
        r = cli.post(
            f"{LITELLM_BASE_URL}/user/new",
            headers=headers,
            json={"user_id": user.sAMAccountName},
            timeout=10,
        )
        if r.status_code not in (200, 201):  # pragma: no cover
            raise HTTPException(500, "LiteLLM user/key failure")

        token_key = r.json().get("key")
        if not token_key:  # pragma: no cover
            raise HTTPException(500, "No token from LiteLLM")

        # Add user to team (ignore duplicates)
        cli.post(
            f"{LITELLM_BASE_URL}/team/member_add",
            headers=headers,
            json={"team_id": TEAM_ID, "member": {"user_id": user.sAMAccountName, "role": "user"}},
            timeout=10,
        )

    # 3. Persist (handle duplicate row gracefully)
    try:
        with Session(engine) as db:
            db.add(
                TokenRow(
                    uuid=str(uuid.uuid4()),
                    username=user.sAMAccountName,
                    email=user.email,
                    department=user.department,
                    token=token_key,
                    created_at=datetime.utcnow(),
                )
            )
            db.commit()
    except IntegrityError:
        # Another concurrent request inserted the row first – fetch it
        with Session(engine) as db:
            token_key = db.execute(
                select(TokenRow.token).where(TokenRow.username == user.sAMAccountName)
            ).scalar_one()

    logger.info("Issued token for %s", user.sAMAccountName)
    return {"token": token_key, "user": user.dict()}


@app.get("/health")
def health():
    return {"status": "ok"}
