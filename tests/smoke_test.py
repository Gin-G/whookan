#!/usr/bin/env python3
"""
Post-deployment smoke tests for WhoKan.

Runs against the live application URL to verify core functionality is working
after a new image has been deployed.  Retries for up to TIMEOUT_SECONDS to
allow Kubernetes time to roll out the new pods.

Usage:
    SMOKE_TEST_URL=https://whokan.nickknows.net python tests/smoke_test.py

Exit codes:
    0 – all checks passed
    1 – one or more checks failed
"""
import os
import sys
import time
import uuid
import requests

BASE_URL = os.environ.get("SMOKE_TEST_URL", "https://whokan.nickknows.net").rstrip("/")
API = f"{BASE_URL}/api/v1"
TIMEOUT_SECONDS = int(os.environ.get("SMOKE_TIMEOUT", "300"))
RETRY_INTERVAL = 10

PASSED = []
FAILED = []


def log(msg: str) -> None:
    print(msg, flush=True)


def record(name: str, ok: bool, detail: str = "") -> None:
    if ok:
        PASSED.append(name)
        log(f"  [PASS] {name}")
    else:
        FAILED.append(name)
        log(f"  [FAIL] {name}" + (f": {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------

def wait_for_health() -> bool:
    """Poll /health until it reports healthy or we exceed TIMEOUT_SECONDS."""
    deadline = time.time() + TIMEOUT_SECONDS
    log(f"Waiting up to {TIMEOUT_SECONDS}s for {BASE_URL}/health to become healthy…")
    while time.time() < deadline:
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=10)
            if r.status_code == 200 and r.json().get("status") == "healthy":
                log("  App is healthy.")
                return True
        except Exception:
            pass
        time.sleep(RETRY_INTERVAL)
    return False


# ---------------------------------------------------------------------------
# Individual smoke checks
# ---------------------------------------------------------------------------

def check_health() -> None:
    """GET /health returns healthy."""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        ok = r.status_code == 200 and r.json().get("status") == "healthy"
        record("health_check", ok, f"status={r.status_code} body={r.text[:120]}")
    except Exception as exc:
        record("health_check", False, str(exc))


def check_openapi() -> None:
    """OpenAPI schema endpoint is reachable."""
    try:
        r = requests.get(f"{API}/openapi.json", timeout=10)
        record("openapi_schema", r.status_code == 200)
    except Exception as exc:
        record("openapi_schema", False, str(exc))


def check_register_and_login() -> tuple[str | None, dict | None]:
    """Register a fresh smoke-test user and log in; return (token, user_data)."""
    uid = uuid.uuid4().hex[:8]
    email = f"smoketest_{uid}@whokan-ci.invalid"
    payload = {
        "email": email,
        "name": "Smoke Test User",
        "password": "SmokeTest!123",
        "title": "CI Bot",
        "company": "GitHub Actions",
    }
    try:
        r = requests.post(f"{API}/users/", json=payload, timeout=10)
        record("user_registration", r.status_code == 200, r.text[:120])
        if r.status_code != 200:
            return None, None
        user = r.json()
    except Exception as exc:
        record("user_registration", False, str(exc))
        return None, None

    try:
        r = requests.post(
            f"{API}/auth/login",
            data={"username": email, "password": payload["password"]},
            timeout=10,
        )
        ok = r.status_code == 200 and "access_token" in r.json()
        record("user_login", ok, r.text[:120])
        if not ok:
            return None, user
        return r.json()["access_token"], user
    except Exception as exc:
        record("user_login", False, str(exc))
        return None, user


def check_get_profile(token: str) -> None:
    """GET /users/me returns the authenticated user's profile."""
    try:
        r = requests.get(
            f"{API}/users/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        ok = r.status_code == 200 and "email" in r.json()
        record("get_profile", ok, r.text[:120])
    except Exception as exc:
        record("get_profile", False, str(exc))


def check_add_skill(token: str) -> str | None:
    """POST /users/me/skills adds a skill to the profile; returns skill_id."""
    try:
        r = requests.post(
            f"{API}/users/me/skills",
            json={"name": "SmokeTestSkill"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        skills = r.json().get("skills", [])
        skill_names = [s["name"] if isinstance(s, dict) else s for s in skills]
        ok = r.status_code == 200 and "SmokeTestSkill" in skill_names
        record("add_skill", ok, r.text[:120])
        if ok:
            for s in skills:
                if isinstance(s, dict) and s.get("name") == "SmokeTestSkill":
                    return s.get("id")
        return None
    except Exception as exc:
        record("add_skill", False, str(exc))
        return None


def check_search_users(token: str) -> None:
    """GET /users/?skill=… returns a list."""
    try:
        r = requests.get(
            f"{API}/users/?skill=SmokeTestSkill",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        ok = r.status_code == 200 and isinstance(r.json(), list)
        record("search_users_by_skill", ok, r.text[:120])
    except Exception as exc:
        record("search_users_by_skill", False, str(exc))


def check_list_help_requests(token: str) -> None:
    """GET /help-requests returns a list."""
    try:
        r = requests.get(
            f"{API}/help-requests",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        ok = r.status_code == 200 and isinstance(r.json(), list)
        record("list_help_requests", ok, r.text[:120])
    except Exception as exc:
        record("list_help_requests", False, str(exc))


def check_forum(token: str, skill_id: str) -> None:
    """Forum: create post, list posts, post detail."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # Create a post
        r = requests.post(
            f"{API}/skills/{skill_id}/forum",
            json={"title": "Smoke test post", "body": "CI smoke test body"},
            headers=headers,
            timeout=10,
        )
        ok = r.status_code == 200 and "id" in r.json()
        record("forum_create_post", ok, r.text[:120])
        if not ok:
            return
        post_id = r.json()["id"]

        # List posts
        r = requests.get(f"{API}/skills/{skill_id}/forum", headers=headers, timeout=10)
        ok = r.status_code == 200 and len(r.json()) >= 1
        record("forum_list_posts", ok, r.text[:120])

        # Get post detail
        r = requests.get(f"{API}/skills/{skill_id}/forum/{post_id}", headers=headers, timeout=10)
        ok = r.status_code == 200 and "comments" in r.json()
        record("forum_get_post", ok, r.text[:120])
    except Exception as exc:
        record("forum_create_post", False, str(exc))


def check_chat_history(token: str, skill_id: str) -> None:
    """Chat: GET history endpoint returns expected shape."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(
            f"{API}/skills/{skill_id}/chat/history",
            headers=headers,
            timeout=10,
        )
        ok = r.status_code == 200 and "messages" in r.json()
        record("chat_history", ok, r.text[:120])
    except Exception as exc:
        record("chat_history", False, str(exc))


def check_frontend_reachable() -> None:
    """The root URL serves an HTML page."""
    try:
        r = requests.get(BASE_URL, timeout=10)
        ok = r.status_code == 200 and "text/html" in r.headers.get("content-type", "")
        record("frontend_reachable", ok, f"status={r.status_code}")
    except Exception as exc:
        record("frontend_reachable", False, str(exc))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    log(f"\n{'='*60}")
    log(f"WhoKan smoke tests  →  {BASE_URL}")
    log(f"{'='*60}\n")

    if not wait_for_health():
        log("\nApp did not become healthy within the timeout window.")
        return 1

    log("\nRunning smoke checks…")
    check_health()
    check_openapi()
    check_frontend_reachable()

    token, _ = check_register_and_login()
    if token:
        check_get_profile(token)
        skill_id = check_add_skill(token)
        check_search_users(token)
        check_list_help_requests(token)
        if skill_id:
            check_forum(token, skill_id)
            check_chat_history(token, skill_id)
        else:
            for name in ("forum_create_post", "forum_list_posts", "forum_get_post", "chat_history"):
                record(name, False, "skipped – no skill_id")
    else:
        for name in ("get_profile", "add_skill", "search_users_by_skill", "list_help_requests",
                     "forum_create_post", "forum_list_posts", "forum_get_post", "chat_history"):
            record(name, False, "skipped – login failed")

    log(f"\n{'='*60}")
    log(f"Results: {len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        log(f"Failed checks: {', '.join(FAILED)}")
    log(f"{'='*60}\n")

    return 0 if not FAILED else 1


if __name__ == "__main__":
    sys.exit(main())
