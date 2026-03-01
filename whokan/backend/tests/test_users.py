"""Tests for user registration, profile retrieval, update, and search endpoints."""
from tests.conftest import skill_names


# ---------------------------------------------------------------------------
# Registration  POST /api/v1/users/
# ---------------------------------------------------------------------------

def test_register_user_returns_200(client, user_payload):
    resp = client.post("/api/v1/users/", json=user_payload)
    assert resp.status_code == 200


def test_register_user_response_fields(client, user_payload):
    resp = client.post("/api/v1/users/", json=user_payload)
    data = resp.json()
    assert data["email"] == user_payload["email"]
    assert data["name"] == user_payload["name"]
    assert data["title"] == user_payload["title"]
    assert data["company"] == user_payload["company"]
    assert data["helped_count"] == 0
    assert skill_names(data) == []
    assert "id" in data


def test_register_user_password_not_in_response(client, user_payload):
    resp = client.post("/api/v1/users/", json=user_payload)
    data = resp.json()
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_email_returns_400(client, user_payload, registered_user):
    resp = client.post("/api/v1/users/", json=user_payload)
    assert resp.status_code == 400
    assert "detail" in resp.json()


def test_register_missing_email_returns_422(client, user_payload):
    payload = {k: v for k, v in user_payload.items() if k != "email"}
    resp = client.post("/api/v1/users/", json=payload)
    assert resp.status_code == 422


def test_register_missing_name_returns_422(client, user_payload):
    payload = {k: v for k, v in user_payload.items() if k != "name"}
    resp = client.post("/api/v1/users/", json=payload)
    assert resp.status_code == 422


def test_register_missing_password_returns_422(client, user_payload):
    payload = {k: v for k, v in user_payload.items() if k != "password"}
    resp = client.post("/api/v1/users/", json=payload)
    assert resp.status_code == 422


def test_register_invalid_email_returns_422(client, user_payload):
    payload = {**user_payload, "email": "notanemail"}
    resp = client.post("/api/v1/users/", json=payload)
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Get current user  GET /api/v1/users/me
# ---------------------------------------------------------------------------

def test_get_me_returns_200(client, auth_headers):
    resp = client.get("/api/v1/users/me", headers=auth_headers)
    assert resp.status_code == 200


def test_get_me_returns_correct_user(client, auth_headers, user_payload):
    resp = client.get("/api/v1/users/me", headers=auth_headers)
    data = resp.json()
    assert data["email"] == user_payload["email"]
    assert data["name"] == user_payload["name"]


def test_get_me_without_auth_returns_401(client):
    resp = client.get("/api/v1/users/me")
    assert resp.status_code == 401


def test_get_me_with_invalid_token_returns_401(client):
    resp = client.get("/api/v1/users/me", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


def test_get_me_with_malformed_header_returns_401(client):
    resp = client.get("/api/v1/users/me", headers={"Authorization": "NotBearer token"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Update current user  PUT /api/v1/users/me
# ---------------------------------------------------------------------------

def test_update_me_name(client, auth_headers, user_payload):
    resp = client.put("/api/v1/users/me", json={"name": "New Name"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"


def test_update_me_title(client, auth_headers):
    resp = client.put("/api/v1/users/me", json={"title": "CTO"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "CTO"


def test_update_me_company(client, auth_headers):
    resp = client.put("/api/v1/users/me", json={"company": "NewCorp"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["company"] == "NewCorp"


def test_update_me_all_fields(client, auth_headers):
    payload = {"name": "Updated Name", "title": "VP Eng", "company": "BigCo"}
    resp = client.put("/api/v1/users/me", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Name"
    assert data["title"] == "VP Eng"
    assert data["company"] == "BigCo"


def test_update_me_partial_leaves_other_fields(client, auth_headers, user_payload):
    resp = client.put("/api/v1/users/me", json={"name": "Changed"}, headers=auth_headers)
    data = resp.json()
    assert data["name"] == "Changed"
    assert data["title"] == user_payload["title"]
    assert data["company"] == user_payload["company"]


def test_update_me_unauthorized_returns_401(client):
    resp = client.put("/api/v1/users/me", json={"name": "Hacker"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# List / search users  GET /api/v1/users/
# ---------------------------------------------------------------------------

def test_list_users_returns_200(client, auth_headers, registered_second_user):
    resp = client.get("/api/v1/users/", headers=auth_headers)
    assert resp.status_code == 200


def test_list_users_excludes_current_user(
    client, auth_headers, user_payload, registered_second_user
):
    resp = client.get("/api/v1/users/", headers=auth_headers)
    emails = [u["email"] for u in resp.json()]
    assert user_payload["email"] not in emails
    assert "second@example.com" in emails


def test_list_users_unauthorized_returns_401(client):
    resp = client.get("/api/v1/users/")
    assert resp.status_code == 401


def test_search_users_by_exact_skill(
    client, auth_headers, second_auth_headers, registered_second_user
):
    # Give second user a skill
    client.post(
        "/api/v1/users/me/skills",
        json={"name": "Python"},
        headers=second_auth_headers,
    )
    resp = client.get("/api/v1/users/?skill=Python", headers=auth_headers)
    assert resp.status_code == 200
    assert "second@example.com" in [u["email"] for u in resp.json()]


def test_search_users_by_skill_partial_match(
    client, auth_headers, second_auth_headers, registered_second_user
):
    client.post(
        "/api/v1/users/me/skills",
        json={"name": "JavaScript"},
        headers=second_auth_headers,
    )
    resp = client.get("/api/v1/users/?skill=java", headers=auth_headers)
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.json()]
    assert "second@example.com" in emails


def test_search_users_by_nonexistent_skill_returns_empty(client, auth_headers):
    resp = client.get("/api/v1/users/?skill=ZzZzZNotASkillZzZz", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_search_excludes_current_user_even_if_they_have_skill(client, auth_headers, user_payload):
    client.post(
        "/api/v1/users/me/skills",
        json={"name": "Python"},
        headers=auth_headers,
    )
    resp = client.get("/api/v1/users/?skill=Python", headers=auth_headers)
    assert user_payload["email"] not in [u["email"] for u in resp.json()]


def test_user_list_response_has_expected_fields(
    client, auth_headers, registered_second_user
):
    resp = client.get("/api/v1/users/", headers=auth_headers)
    user = next(u for u in resp.json() if u["email"] == "second@example.com")
    for field in ("id", "email", "name", "title", "company", "skills", "helped_count"):
        assert field in user


def test_register_returns_skills_as_objects(client, auth_headers):
    """Registration endpoint should return skills as [{id, name}] objects, not strings."""
    client.post("/api/v1/users/me/skills", json={"name": "Rust"}, headers=auth_headers)
    resp = client.get("/api/v1/users/me", headers=auth_headers)
    skills = resp.json()["skills"]
    assert len(skills) == 1
    assert "id" in skills[0]
    assert "name" in skills[0]
    assert skills[0]["name"] == "Rust"
