"""Tests for input validation constraints on all API endpoints."""
import pytest
from app.db.models import Skill


# ---------------------------------------------------------------------------
# User registration validation
# ---------------------------------------------------------------------------

def test_register_name_too_long_returns_422(client, user_payload):
    payload = {**user_payload, "email": "long@example.com", "name": "x" * 101}
    assert client.post("/api/v1/users/", json=payload).status_code == 422


def test_register_title_too_long_returns_422(client, user_payload):
    payload = {**user_payload, "email": "long@example.com", "title": "x" * 201}
    assert client.post("/api/v1/users/", json=payload).status_code == 422


def test_register_company_too_long_returns_422(client, user_payload):
    payload = {**user_payload, "email": "long@example.com", "company": "x" * 201}
    assert client.post("/api/v1/users/", json=payload).status_code == 422


# ---------------------------------------------------------------------------
# Skill validation
# ---------------------------------------------------------------------------

def test_add_skill_name_too_long_returns_422(client, auth_headers, registered_user):
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": "x" * 101},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_add_skill_empty_name_returns_422(client, auth_headers, registered_user):
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": ""},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_add_skill_whitespace_only_returns_422(client, auth_headers, registered_user):
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": "   "},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Help request validation
# ---------------------------------------------------------------------------

@pytest.fixture()
def skill_uuid(client, auth_headers, db):
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    skill = db.query(Skill).filter(Skill.name == "Python").first()
    return str(skill.id)


def test_help_request_description_too_long_returns_422(
    client, auth_headers, registered_user, skill_uuid
):
    resp = client.post(
        "/api/v1/help-requests",
        json={"skill_id": skill_uuid, "description": "x" * 2001},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Forum validation
# ---------------------------------------------------------------------------

def test_forum_post_title_too_long_returns_422(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "x" * 201, "body": "Some content"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_forum_post_body_too_long_returns_422(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "Valid title", "body": "x" * 10001},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_forum_post_empty_title_returns_422(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "", "body": "Some content"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_forum_post_empty_body_returns_422(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "Valid title", "body": ""},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_forum_comment_body_too_long_returns_422(client, auth_headers, skill_uuid):
    # Create a post first
    post_resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "Test post", "body": "Content"},
        headers=auth_headers,
    )
    post_id = post_resp.json()["id"]
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}/comments",
        json={"body": "x" * 2001},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_forum_comment_empty_body_returns_422(client, auth_headers, skill_uuid):
    post_resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "Test post", "body": "Content"},
        headers=auth_headers,
    )
    post_id = post_resp.json()["id"]
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}/comments",
        json={"body": ""},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Cross-user isolation: user B cannot delete user A's skills
# ---------------------------------------------------------------------------

def test_other_user_cannot_delete_my_skill(
    client, auth_headers, second_auth_headers, registered_second_user, db
):
    # Add skill as user 1
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": "Go"},
        headers=auth_headers,
    )
    skill = db.query(Skill).filter(Skill.name == "Go").first()
    assert skill is not None

    # Try to delete as user 2 — should fail (403 or 404, not 200)
    del_resp = client.delete(
        f"/api/v1/users/me/skills/{skill.id}",
        headers=second_auth_headers,
    )
    assert del_resp.status_code in (403, 404)

    # Skill should still belong to user 1
    me_resp = client.get("/api/v1/users/me", headers=auth_headers)
    skill_names = [s["name"] for s in me_resp.json()["skills"]]
    assert "Go" in skill_names
