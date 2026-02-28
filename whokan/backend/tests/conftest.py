"""
Test configuration and shared fixtures.

Sets required environment variables BEFORE any app modules are imported so the
SQLAlchemy engine and settings objects pick up the test database URL and secret key.
"""
import os

# Must be set before importing any app modules
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-whokan-ci-testing-32chars!")
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/whokan_test",
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.db.models import Base
from main import app  # noqa: E402 – imported after env vars are set

_engine = create_engine(os.environ["DATABASE_URL"])
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


# ---------------------------------------------------------------------------
# Session-level fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def client():
    """Single TestClient for the whole test session (triggers startup once)."""
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Function-level fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_db():
    """Truncate all tables before every test so each test starts fresh."""
    db = _SessionLocal()
    try:
        db.execute(text("DELETE FROM chat_messages"))
        db.execute(text("DELETE FROM post_votes"))
        db.execute(text("DELETE FROM post_comments"))
        db.execute(text("DELETE FROM forum_posts"))
        db.execute(text("DELETE FROM help_requests"))
        db.execute(text("DELETE FROM user_skills"))
        db.execute(text("DELETE FROM app_users"))
        db.execute(text("DELETE FROM skills"))
        db.commit()
    finally:
        db.close()


@pytest.fixture()
def db():
    """Expose a raw DB session for tests that need to query the database directly."""
    session = _SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# User / auth payload fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def user_payload():
    return {
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "testpassword123",
        "title": "Software Engineer",
        "company": "TestCorp",
    }


@pytest.fixture()
def second_user_payload():
    return {
        "email": "second@example.com",
        "name": "Second User",
        "password": "secondpassword456",
        "title": "Designer",
        "company": "DesignCorp",
    }


@pytest.fixture()
def registered_user(client, user_payload):
    resp = client.post("/api/v1/users/", json=user_payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture()
def auth_headers(client, user_payload, registered_user):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture()
def registered_second_user(client, second_user_payload):
    resp = client.post("/api/v1/users/", json=second_user_payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def skill_names(user_data: dict) -> list:
    """Return the list of skill name strings from a User response dict."""
    return [s["name"] for s in user_data.get("skills", [])]


@pytest.fixture()
def second_auth_headers(client, second_user_payload, registered_second_user):
    resp = client.post(
        "/api/v1/auth/login",
        data={
            "username": second_user_payload["email"],
            "password": second_user_payload["password"],
        },
    )
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
