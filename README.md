# Token Generator Micro‑Service

A full‑stack reference project that demonstrates:

* **FastAPI** micro‑service that authenticates against LDAP, mints one LiteLLM API‑key per user and caches it in Postgres.
* **Next.js 15** front‑end (React 19, Tailwind 4, TypeScript) for self‑service token retrieval.
* **Docker‑Compose** orchestration for LDAP, LiteLLM gateway, both Postgres instances, pgAdmin, back‑end, front‑end and an automated test‑runner.
* **Pytest** integration tests checking authentication flow, single‑token guarantee and race‑condition safety.

The stack is completely vendor‑neutral – you can point it at *any* LDAP directory, host it on ARM or x86, run it locally with Compose or ship the images to Kubernetes.

---

## Quick Start (local Docker Desktop)

```bash
git clone <repo>
cd token-generator

# build & start everything
docker-compose up --build -d

# run the smoke‑tests
docker compose run --rm test
```

Open http://localhost:3000 – create a token, copy it, call the gateway:

```bash
curl -H "Authorization: Bearer <TOKEN>" http://localhost:4000/v1/models
```

---

## Directory layout

| Path | What lives here |
|------|-----------------|
| `token-generator/` | FastAPI service (+ Dockerfile) |
| `frontend/` | Next.js app (+ Tailwind config, Dockerfile) |
| `litellm/` | Pre‑configured LiteLLM gateway |
| `ldap/` | OpenLDAP image + seed users |
| `pgadmin/` | pgAdmin desktop for both Postgres instances |
| `tests/` | Pytest docker image & suites |
| `docker-compose.yml` | one‑shot dev orchestration |

---

## Environment variables (excerpt)

| Service | Variable | Default | Description |
|---------|----------|---------|-------------|
| back‑end | `LDAP_SERVER_HOST` | `ldap` | host of LDAP directory |
| back‑end | `LITELLM_BASE_URL` | `http://litellm:4000` | REST endpoint of LiteLLM |
| back‑end | `LITELLM_MASTER_KEY` | `sk-1234` | admin key used to issue user keys |
| front‑end | `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | back‑end HTTP origin |

Edit **`docker‑compose.override.yml`** or pass `-e` overrides when deploying.

---

## Development tips

* The front‑end supports **hot‑reload** – `npm run dev` outside Docker is fastest.
* Run unit tests with `pytest -q` in **token‑generator/**.
* Use pgAdmin (http://localhost:5050) to inspect both databases.
* LDAP users are declared in `ldap/ldif/users.ldif`; restart the LDAP container after editing.
