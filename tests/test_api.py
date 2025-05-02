import time
import uuid
import pytest
import httpx
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://token-generator:8000"

# --------------------------------------------------------------------------- #
#                                FIXTURES                                     #
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session", autouse=True)
def wait_for_service():
    """
    Wait up to 30s for the FastAPI container to report healthy.
    (Executed once per test session.)
    """
    for _ in range(15):
        try:
            if httpx.get(f"{BASE_URL}/health", timeout=1.0).status_code == 200:
                return
        except Exception:
            pass
        time.sleep(2)
    pytest.fail("FastAPI app did not start in time")

# Helper for token endpoint
def _request_token(login: str, password: str) -> str:
    r = httpx.post(f"{BASE_URL}/token", json={"login": login, "password": password})
    assert r.status_code == 200
    return r.json()["token"]


# --------------------------------------------------------------------------- #
#                               AUTH TESTS                                    #
# --------------------------------------------------------------------------- #
def test_auth_by_username_lowercase():
    r = httpx.post(f"{BASE_URL}/authenticate",
                   json={"login": "user1", "password": "pass1"})
    assert r.status_code == 200
    data = r.json()
    assert data["sAMAccountName"] == "user1"
    assert data["email"].lower() == "username1@example.com"
    assert data["department"] == "dep1"


def test_auth_by_username_uppercase():
    r = httpx.post(f"{BASE_URL}/authenticate",
                   json={"login": "USER1", "password": "pass1"})
    assert r.status_code == 200
    assert r.json()["sAMAccountName"] == "user1"


def test_auth_by_email_mixedcase():
    r = httpx.post(f"{BASE_URL}/authenticate",
                   json={"login": "UserName2@Example.com", "password": "pass2"})
    assert r.status_code == 200
    data = r.json()
    assert data["sAMAccountName"] == "user2"
    assert data["department"] == "dep2"


def test_auth_by_partial_email_mixedcase():
    r = httpx.post(f"{BASE_URL}/authenticate",
                   json={"login": "UserName2@Example", "password": "pass2"})
    assert r.status_code == 404


def test_user_not_found():
    r = httpx.post(f"{BASE_URL}/authenticate",
                   json={"login": str(uuid.uuid4()), "password": "whatever"})
    assert r.status_code == 404


def test_wrong_password():
    r = httpx.post(f"{BASE_URL}/authenticate",
                   json={"login": "user1", "password": "wrong"})
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
#                     TOKEN ENDPOINT TESTS  (reuse validation)                #
# --------------------------------------------------------------------------- #

_first_token = None          # module‑level cache


def test_token_issued_once():
    """
    First call for user1 → should mint (or fetch) a token and cache it.
    """
    global _first_token
    token = _request_token("user1", "pass1")
    _first_token = token
    assert token.startswith("sk-")


def test_token_reuse():
    """
    Second call must return *exactly* the same token.
    """
    assert _first_token, "First token was not set by test_token_issued_once"
    token = _request_token("user1", "pass1")
    assert token == _first_token


def test_token_reuse_between_uid_and_email():
    """
    A token obtained via uid‑login must be identical to one obtained
    via e‑mail login for the same account.
    """
    token_by_uid = _request_token("user2", "pass2")
    token_by_mail = _request_token("UserName2@Example.com", "pass2")
    assert token_by_uid == token_by_mail


# --------------------------------------------------------------------------- #
#                    CONCURRENCY / RACE‑CONDITION TEST                        #
# --------------------------------------------------------------------------- #
def test_concurrent_token_requests_single_row():
    """
    Fire 10 concurrent `/token` requests for **user3** and assert that:
      • every call returns the same key
      • the endpoint is free from race‑condition duplicates
    """
    creds = ("user3", "pass3")
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = [pool.submit(_request_token, *creds) for _ in range(10)]
        tokens = [f.result() for f in as_completed(futures)]

    assert len(set(tokens)) == 1, "Different tokens returned under concurrency"
