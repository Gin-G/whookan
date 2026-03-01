"""Tests for help request endpoints.

Endpoints:
  POST   /api/v1/help-requests          – create a help request
  GET    /api/v1/help-requests          – list open requests (excluding own)
  POST   /api/v1/help-requests/confirm  – confirm help was provided
"""
import pytest
from app.db.models import Skill


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def skill_id(client, auth_headers):
    """Add a skill as the primary user and return its UUID from the DB."""
    client.post("/api/v1/users/me/skills", json={"name": "Python"}, headers=auth_headers)


@pytest.fixture()
def skill_uuid(client, auth_headers, skill_id, db):
    skill = db.query(Skill).filter(Skill.name == "Python").first()
    assert skill is not None
    return str(skill.id)


# ---------------------------------------------------------------------------
# Create help request  POST /api/v1/help-requests
# ---------------------------------------------------------------------------

def test_create_help_request_returns_200(client, second_auth_headers, registered_second_user, skill_uuid):
    resp = client.post(
        "/api/v1/help-requests",
        json={"skill_id": skill_uuid, "description": "Need help with asyncio"},
        headers=second_auth_headers,
    )
    assert resp.status_code == 200


def test_create_help_request_response_fields(client, second_auth_headers, registered_second_user, skill_uuid):
    resp = client.post(
        "/api/v1/help-requests",
        json={"skill_id": skill_uuid, "description": "Need asyncio help"},
        headers=second_auth_headers,
    )
    data = resp.json()
    assert "id" in data
    assert data["status"] == "open"
    assert "requester_id" in data
    assert data["skill_id"] == skill_uuid
    assert data["description"] == "Need asyncio help"
    assert data["requester_name"] == "Second User"
    assert data["skill_name"] == "Python"


def test_create_help_request_status_defaults_to_open(client, second_auth_headers, registered_second_user, skill_uuid):
    resp = client.post(
        "/api/v1/help-requests",
        json={"skill_id": skill_uuid, "description": "Help needed"},
        headers=second_auth_headers,
    )
    assert resp.json()["status"] == "open"


def test_create_help_request_unauthorized_returns_401(client, skill_uuid):
    resp = client.post(
        "/api/v1/help-requests",
        json={"skill_id": skill_uuid, "description": "Help"},
    )
    assert resp.status_code == 401


def test_create_help_request_missing_fields_returns_422(client, auth_headers):
    resp = client.post("/api/v1/help-requests", json={}, headers=auth_headers)
    assert resp.status_code == 422


def test_create_help_request_missing_description_returns_422(client, auth_headers, skill_uuid):
    resp = client.post(
        "/api/v1/help-requests",
        json={"skill_id": skill_uuid},
        headers=auth_headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# List help requests  GET /api/v1/help-requests
# ---------------------------------------------------------------------------

def test_list_help_requests_returns_200(client, auth_headers):
    resp = client.get("/api/v1/help-requests", headers=auth_headers)
    assert resp.status_code == 200


def test_list_help_requests_returns_list(client, auth_headers):
    assert isinstance(client.get("/api/v1/help-requests", headers=auth_headers).json(), list)


def test_list_help_requests_empty_when_none_exist(client, auth_headers):
    assert client.get("/api/v1/help-requests", headers=auth_headers).json() == []


def test_list_help_requests_shows_other_users_requests(
    client, auth_headers, second_auth_headers, registered_second_user, skill_uuid
):
    # Second user creates a request
    client.post(
        "/api/v1/help-requests",
        json={"skill_id": skill_uuid, "description": "Need help"},
        headers=second_auth_headers,
    )
    # First user can see it
    resp = client.get("/api/v1/help-requests", headers=auth_headers)
    assert len(resp.json()) == 1
    data = resp.json()[0]
    assert data["description"] == "Need help"
    assert data["requester_name"] == "Second User"
    assert data["skill_name"] == "Python"


def test_list_help_requests_excludes_own_requests(
    client, auth_headers, skill_uuid
):
    # User creates their own request
    client.post(
        "/api/v1/help-requests",
        json={"skill_id": skill_uuid, "description": "My own request"},
        headers=auth_headers,
    )
    # Should not appear in their own list
    resp = client.get("/api/v1/help-requests", headers=auth_headers)
    assert resp.json() == []


def test_list_help_requests_only_shows_open_requests(
    client, auth_headers, second_auth_headers, registered_second_user, skill_uuid, db
):
    from app.db.models import HelpRequest as HelpRequestModel
    from uuid import uuid4

    # Create a completed request directly in DB
    from app.db.models import User
    second_user = db.query(User).filter(User.email == "second@example.com").first()
    skill = db.query(Skill).filter(Skill.name == "Python").first()

    hr = HelpRequestModel(
        id=uuid4(),
        skill_id=skill.id,
        description="Already done",
        status="completed",
        requester_id=second_user.id,
    )
    db.add(hr)
    db.commit()

    resp = client.get("/api/v1/help-requests", headers=auth_headers)
    assert all(r["status"] == "open" for r in resp.json())


def test_list_help_requests_unauthorized_returns_401(client):
    assert client.get("/api/v1/help-requests").status_code == 401


# ---------------------------------------------------------------------------
# Confirm help  POST /api/v1/help-requests/confirm
# ---------------------------------------------------------------------------

def test_confirm_help_unauthorized_returns_401(client):
    resp = client.post(
        "/api/v1/help-requests/confirm",
        json={
            "request_id": "00000000-0000-0000-0000-000000000000",
            "helper_id": "00000000-0000-0000-0000-000000000000",
            "skill_id": "00000000-0000-0000-0000-000000000000",
        },
    )
    assert resp.status_code == 401


def test_confirm_help_nonexistent_request_returns_404(client, auth_headers, registered_user):
    resp = client.post(
        "/api/v1/help-requests/confirm",
        json={
            "request_id": "00000000-0000-0000-0000-000000000001",
            "helper_id": registered_user["id"],
            "skill_id": "00000000-0000-0000-0000-000000000000",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404


def test_confirm_help_wrong_helper_returns_403(
    client, auth_headers, registered_second_user, skill_uuid, db
):
    """Authenticated user cannot confirm as a different helper ID."""
    from app.db.models import HelpRequest as HelpRequestModel, User
    from uuid import uuid4

    second_user = db.query(User).filter(User.email == "second@example.com").first()
    skill = db.query(Skill).filter(Skill.name == "Python").first()

    hr = HelpRequestModel(
        id=uuid4(),
        skill_id=skill.id,
        description="Need Python help",
        status="open",
        requester_id=second_user.id,
    )
    db.add(hr)
    db.commit()
    db.refresh(hr)

    resp = client.post(
        "/api/v1/help-requests/confirm",
        json={
            "request_id": str(hr.id),
            "helper_id": str(uuid4()),  # wrong ID
            "skill_id": str(skill.id),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 403


def test_confirm_help_increments_helped_count(
    client, auth_headers, registered_user, registered_second_user, skill_uuid, db
):
    from app.db.models import HelpRequest as HelpRequestModel, User
    from uuid import uuid4

    second_user = db.query(User).filter(User.email == "second@example.com").first()
    helper = db.query(User).filter(User.email == "testuser@example.com").first()
    skill = db.query(Skill).filter(Skill.name == "Python").first()

    initial_count = helper.helped_count

    hr = HelpRequestModel(
        id=uuid4(),
        skill_id=skill.id,
        description="Need help with Python",
        status="open",
        requester_id=second_user.id,
    )
    db.add(hr)
    db.commit()
    db.refresh(hr)

    resp = client.post(
        "/api/v1/help-requests/confirm",
        json={
            "request_id": str(hr.id),
            "helper_id": str(helper.id),
            "skill_id": str(skill.id),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["helped_count"] == initial_count + 1


def test_confirm_help_marks_request_completed(
    client, auth_headers, registered_user, registered_second_user, skill_uuid, db
):
    from app.db.models import HelpRequest as HelpRequestModel, User
    from uuid import uuid4

    second_user = db.query(User).filter(User.email == "second@example.com").first()
    helper = db.query(User).filter(User.email == "testuser@example.com").first()
    skill = db.query(Skill).filter(Skill.name == "Python").first()

    hr = HelpRequestModel(
        id=uuid4(),
        skill_id=skill.id,
        description="Help with Rust",
        status="open",
        requester_id=second_user.id,
    )
    db.add(hr)
    db.commit()
    db.refresh(hr)

    client.post(
        "/api/v1/help-requests/confirm",
        json={
            "request_id": str(hr.id),
            "helper_id": str(helper.id),
            "skill_id": str(skill.id),
        },
        headers=auth_headers,
    )

    db.refresh(hr)
    assert hr.status == "completed"
