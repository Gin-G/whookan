"""Tests for skill management endpoints.

Endpoints under /api/v1/users/me/skills:
  POST        – add single skill
  POST /bulk  – bulk import skills
  DELETE /{id} – remove a skill
"""
from tests.conftest import skill_names
from app.db.models import Skill


# ---------------------------------------------------------------------------
# Add single skill  POST /api/v1/users/me/skills
# ---------------------------------------------------------------------------

def test_add_skill_returns_200(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": "Python"},
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_add_skill_appears_in_user_skills(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": "Python"},
        headers=auth_headers,
    )
    assert "Python" in skill_names(resp.json())


def test_add_multiple_different_skills(client, auth_headers):
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    client.post("/api/v1/users/me/skills", json={"name": "JavaScript"}, headers=auth_headers)
    me = client.get("/api/v1/users/me", headers=auth_headers).json()
    assert "Python" in skill_names(me)
    assert "JavaScript" in skill_names(me)


def test_add_duplicate_skill_returns_400(client, auth_headers):
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": "Python"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_add_duplicate_skill_case_insensitive_returns_400(client, auth_headers):
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": "python"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


def test_add_skill_same_name_different_users_is_allowed(
    client, auth_headers, second_auth_headers, registered_second_user
):
    r1 = client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    r2 = client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=second_auth_headers)
    assert r1.status_code == 200
    assert r2.status_code == 200


def test_add_skill_response_contains_user_fields(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": "Go"},
        headers=auth_headers,
    )
    data = resp.json()
    for field in ("id", "email", "name", "skills", "helped_count"):
        assert field in data


def test_add_skill_object_has_id_and_name(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills",
        json={"name": "Rust"},
        headers=auth_headers,
    )
    skill_obj = resp.json()["skills"][0]
    assert "id" in skill_obj
    assert "name" in skill_obj


def test_add_skill_unauthorized_returns_401(client):
    resp = client.post("/api/v1/users/me/skills", json={"name": "Python"})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Delete skill  DELETE /api/v1/users/me/skills/{skill_id}
# ---------------------------------------------------------------------------

def test_delete_skill_returns_200(client, auth_headers, db):
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    skill = db.query(Skill).filter(Skill.name == "Python").first()
    resp = client.delete(f"/api/v1/users/me/skills/{skill.id}", headers=auth_headers)
    assert resp.status_code == 200


def test_delete_skill_removes_it_from_user(client, auth_headers, db):
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    skill = db.query(Skill).filter(Skill.name == "Python").first()
    client.delete(f"/api/v1/users/me/skills/{skill.id}", headers=auth_headers)
    me = client.get("/api/v1/users/me", headers=auth_headers).json()
    assert "Python" not in skill_names(me)


def test_delete_skill_only_removes_from_that_user(
    client, auth_headers, second_auth_headers, registered_second_user, db
):
    """Deleting a skill for user A should not remove it from user B."""
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=second_auth_headers)
    skill = db.query(Skill).filter(Skill.name == "Python").first()
    client.delete(f"/api/v1/users/me/skills/{skill.id}", headers=auth_headers)
    second_me = client.get("/api/v1/users/me", headers=second_auth_headers).json()
    assert "Python" in skill_names(second_me)


def test_delete_nonexistent_skill_returns_404(client, auth_headers):
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.delete(f"/api/v1/users/me/skills/{fake_id}", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_other_users_skill_returns_404(
    client, auth_headers, second_auth_headers, registered_second_user, db
):
    """User A cannot delete a skill they don't have (even if it exists)."""
    client.post("/api/v1/users/me/skills", json={"name": "Rust"}, headers=second_auth_headers)
    skill = db.query(Skill).filter(Skill.name == "Rust").first()
    resp = client.delete(f"/api/v1/users/me/skills/{skill.id}", headers=auth_headers)
    assert resp.status_code == 404


def test_delete_skill_unauthorized_returns_401(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.delete(f"/api/v1/users/me/skills/{fake_id}")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Bulk import  POST /api/v1/users/me/skills/bulk
# ---------------------------------------------------------------------------

def test_bulk_import_csv_returns_200(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills/bulk",
        json={"skills": "Python, JavaScript, TypeScript", "format": "csv"},
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_bulk_import_csv_adds_all_skills(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills/bulk",
        json={"skills": "Python, JavaScript, TypeScript", "format": "csv"},
        headers=auth_headers,
    )
    names = skill_names(resp.json())
    assert "Python" in names
    assert "JavaScript" in names
    assert "TypeScript" in names


def test_bulk_import_newline_returns_200(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills/bulk",
        json={"skills": "Python\nJavaScript\nRust", "format": "newline"},
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_bulk_import_newline_adds_all_skills(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills/bulk",
        json={"skills": "Python\nJavaScript\nRust", "format": "newline"},
        headers=auth_headers,
    )
    names = skill_names(resp.json())
    assert "Python" in names
    assert "JavaScript" in names
    assert "Rust" in names


def test_bulk_import_deduplicates_case_insensitive(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills/bulk",
        json={"skills": "Python, python, PYTHON", "format": "csv"},
        headers=auth_headers,
    )
    python_count = sum(1 for n in skill_names(resp.json()) if n.lower() == "python")
    assert python_count == 1


def test_bulk_import_skips_skills_user_already_has(client, auth_headers):
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)
    resp = client.post(
        "/api/v1/users/me/skills/bulk",
        json={"skills": "Python, Go", "format": "csv"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    names = skill_names(resp.json())
    assert "Python" in names
    assert "Go" in names
    assert sum(1 for n in names if n.lower() == "python") == 1


def test_bulk_import_trims_whitespace(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills/bulk",
        json={"skills": "  Python  ,  Go  ", "format": "csv"},
        headers=auth_headers,
    )
    names = skill_names(resp.json())
    assert "Python" in names
    assert "Go" in names


def test_bulk_import_default_format_is_newline(client, auth_headers):
    resp = client.post(
        "/api/v1/users/me/skills/bulk",
        json={"skills": "Python\nGo"},
        headers=auth_headers,
    )
    assert resp.status_code == 200


def test_bulk_import_unauthorized_returns_401(client):
    resp = client.post(
        "/api/v1/users/me/skills/bulk",
        json={"skills": "Python", "format": "csv"},
    )
    assert resp.status_code == 401
