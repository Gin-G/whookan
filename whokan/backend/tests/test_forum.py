"""Tests for forum endpoints.

Endpoints (prefix /api/v1/skills/{skill_id}/forum):
  GET  /info               – skill metadata
  GET  ""                  – list posts
  POST ""                  – create post
  GET  /{post_id}          – post detail with comments
  POST /{post_id}/comments – add comment
  POST /{post_id}/vote     – toggle upvote
"""
import pytest
from app.db.models import Skill


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def skill_uuid(client, auth_headers, db):
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    skill = db.query(Skill).filter(Skill.name == "Python").first()
    return str(skill.id)


@pytest.fixture()
def post_id(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "How do I use async?", "body": "I need help with asyncio."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Skill info  GET /info
# ---------------------------------------------------------------------------

def test_get_skill_info_returns_200(client, auth_headers, skill_uuid):
    resp = client.get(f"/api/v1/skills/{skill_uuid}/forum/info", headers=auth_headers)
    assert resp.status_code == 200


def test_get_skill_info_returns_name(client, auth_headers, skill_uuid):
    data = client.get(f"/api/v1/skills/{skill_uuid}/forum/info", headers=auth_headers).json()
    assert data["name"] == "Python"
    assert data["id"] == skill_uuid


def test_get_skill_info_not_found_returns_404(client, auth_headers):
    resp = client.get(
        "/api/v1/skills/00000000-0000-0000-0000-000000000001/forum/info",
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_get_skill_info_unauthorized_returns_401(client, skill_uuid):
    assert client.get(f"/api/v1/skills/{skill_uuid}/forum/info").status_code == 401


# ---------------------------------------------------------------------------
# List posts  GET ""
# ---------------------------------------------------------------------------

def test_list_posts_returns_200(client, auth_headers, skill_uuid):
    assert client.get(f"/api/v1/skills/{skill_uuid}/forum", headers=auth_headers).status_code == 200


def test_list_posts_empty_when_no_posts(client, auth_headers, skill_uuid):
    assert client.get(f"/api/v1/skills/{skill_uuid}/forum", headers=auth_headers).json() == []


def test_list_posts_returns_created_post(client, auth_headers, skill_uuid, post_id):
    posts = client.get(f"/api/v1/skills/{skill_uuid}/forum", headers=auth_headers).json()
    assert len(posts) == 1
    assert posts[0]["id"] == post_id


def test_list_posts_unauthorized_returns_401(client, skill_uuid):
    assert client.get(f"/api/v1/skills/{skill_uuid}/forum").status_code == 401


# ---------------------------------------------------------------------------
# Create post  POST ""
# ---------------------------------------------------------------------------

def test_create_post_returns_200(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "Tips for Python", "body": "Here are my tips..."},
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_create_post_response_fields(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "Tips", "body": "Content"},
        headers=auth_headers,
    )
    data = resp.json()
    for field in ("id", "skill_id", "author_id", "author_name", "title", "body",
                  "vote_count", "comment_count", "created_at"):
        assert field in data, f"Missing field: {field}"
    assert data["skill_id"] == skill_uuid
    assert data["vote_count"] == 0
    assert data["comment_count"] == 0


def test_create_post_missing_title_returns_422(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"body": "No title here"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_post_missing_body_returns_422(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "No body"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_create_post_unknown_skill_returns_404(client, auth_headers):
    resp = client.post(
        "/api/v1/skills/00000000-0000-0000-0000-000000000001/forum",
        json={"title": "T", "body": "B"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_create_post_unauthorized_returns_401(client, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum",
        json={"title": "T", "body": "B"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Get post detail  GET /{post_id}
# ---------------------------------------------------------------------------

def test_get_post_returns_200(client, auth_headers, skill_uuid, post_id):
    resp = client.get(f"/api/v1/skills/{skill_uuid}/forum/{post_id}", headers=auth_headers)
    assert resp.status_code == 200


def test_get_post_includes_comments_field(client, auth_headers, skill_uuid, post_id):
    data = client.get(f"/api/v1/skills/{skill_uuid}/forum/{post_id}", headers=auth_headers).json()
    assert "comments" in data
    assert isinstance(data["comments"], list)


def test_get_post_includes_user_voted(client, auth_headers, skill_uuid, post_id):
    data = client.get(f"/api/v1/skills/{skill_uuid}/forum/{post_id}", headers=auth_headers).json()
    assert "user_voted" in data
    assert data["user_voted"] is False


def test_get_post_not_found_returns_404(client, auth_headers, skill_uuid):
    resp = client.get(
        f"/api/v1/skills/{skill_uuid}/forum/00000000-0000-0000-0000-000000000001",
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_get_post_unauthorized_returns_401(client, skill_uuid, post_id):
    assert client.get(f"/api/v1/skills/{skill_uuid}/forum/{post_id}").status_code == 401


# ---------------------------------------------------------------------------
# Add comment  POST /{post_id}/comments
# ---------------------------------------------------------------------------

def test_add_comment_returns_200(client, auth_headers, skill_uuid, post_id):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}/comments",
        json={"body": "Great question!"},
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_add_comment_appears_in_post_detail(client, auth_headers, skill_uuid, post_id):
    client.post(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}/comments",
        json={"body": "My comment"},
        headers=auth_headers,
    )
    data = client.get(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}", headers=auth_headers
    ).json()
    assert len(data["comments"]) == 1
    assert data["comments"][0]["body"] == "My comment"
    assert data["comment_count"] == 1


def test_add_comment_response_has_author_name(client, auth_headers, skill_uuid, post_id, user_payload):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}/comments",
        json={"body": "Hello"},
        headers=auth_headers,
    )
    assert resp.json()["author_name"] == user_payload["name"]


def test_add_comment_missing_body_returns_422(client, auth_headers, skill_uuid, post_id):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}/comments",
        json={},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_add_comment_to_nonexistent_post_returns_404(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum/00000000-0000-0000-0000-000000000001/comments",
        json={"body": "Comment"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_add_comment_unauthorized_returns_401(client, skill_uuid, post_id):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}/comments",
        json={"body": "Comment"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Vote  POST /{post_id}/vote
# ---------------------------------------------------------------------------

def test_vote_post_returns_200(client, auth_headers, skill_uuid, post_id):
    resp = client.post(f"/api/v1/skills/{skill_uuid}/forum/{post_id}/vote", headers=auth_headers)
    assert resp.status_code == 200


def test_vote_increments_count(client, auth_headers, skill_uuid, post_id):
    resp = client.post(f"/api/v1/skills/{skill_uuid}/forum/{post_id}/vote", headers=auth_headers)
    assert resp.json()["vote_count"] == 1
    assert resp.json()["voted"] is True


def test_vote_twice_toggles_off(client, auth_headers, skill_uuid, post_id):
    client.post(f"/api/v1/skills/{skill_uuid}/forum/{post_id}/vote", headers=auth_headers)
    resp = client.post(f"/api/v1/skills/{skill_uuid}/forum/{post_id}/vote", headers=auth_headers)
    assert resp.json()["vote_count"] == 0
    assert resp.json()["voted"] is False


def test_vote_reflected_in_user_voted_field(client, auth_headers, skill_uuid, post_id):
    client.post(f"/api/v1/skills/{skill_uuid}/forum/{post_id}/vote", headers=auth_headers)
    data = client.get(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}", headers=auth_headers
    ).json()
    assert data["user_voted"] is True


def test_vote_different_users_independent(
    client, auth_headers, second_auth_headers, registered_second_user, skill_uuid, post_id
):
    client.post(f"/api/v1/skills/{skill_uuid}/forum/{post_id}/vote", headers=auth_headers)
    client.post(f"/api/v1/skills/{skill_uuid}/forum/{post_id}/vote", headers=second_auth_headers)
    data = client.get(
        f"/api/v1/skills/{skill_uuid}/forum/{post_id}", headers=auth_headers
    ).json()
    assert data["vote_count"] == 2


def test_vote_on_nonexistent_post_returns_404(client, auth_headers, skill_uuid):
    resp = client.post(
        f"/api/v1/skills/{skill_uuid}/forum/00000000-0000-0000-0000-000000000001/vote",
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_vote_unauthorized_returns_401(client, skill_uuid, post_id):
    assert client.post(f"/api/v1/skills/{skill_uuid}/forum/{post_id}/vote").status_code == 401
