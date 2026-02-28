"""Tests for chat endpoints.

  GET /api/v1/skills/{skill_id}/chat/history  – paginated message history
  WS  /api/v1/skills/{skill_id}/chat/ws       – real-time WebSocket chat
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
def token(auth_headers):
    return auth_headers["Authorization"].split(" ")[1]


# ---------------------------------------------------------------------------
# Chat history  GET /history
# ---------------------------------------------------------------------------

def test_get_history_returns_200(client, auth_headers, skill_uuid):
    resp = client.get(f"/api/v1/skills/{skill_uuid}/chat/history", headers=auth_headers)
    assert resp.status_code == 200


def test_get_history_empty_when_no_messages(client, auth_headers, skill_uuid):
    data = client.get(f"/api/v1/skills/{skill_uuid}/chat/history", headers=auth_headers).json()
    assert data["messages"] == []
    assert data["skill_id"] == skill_uuid


def test_get_history_unauthorized_returns_401(client, skill_uuid):
    assert client.get(f"/api/v1/skills/{skill_uuid}/chat/history").status_code == 401


def test_get_history_unknown_skill_returns_404(client, auth_headers):
    resp = client.get(
        "/api/v1/skills/00000000-0000-0000-0000-000000000001/chat/history",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# WebSocket chat  WS /ws
# ---------------------------------------------------------------------------

def test_websocket_connect_and_send(client, skill_uuid, token):
    with client.websocket_connect(
        f"/api/v1/skills/{skill_uuid}/chat/ws?token={token}"
    ) as ws:
        ws.send_text("Hello room!")
        data = ws.receive_json()
        assert data["content"] == "Hello room!"
        assert data["type"] == "message"


def test_websocket_message_has_required_fields(client, skill_uuid, token):
    with client.websocket_connect(
        f"/api/v1/skills/{skill_uuid}/chat/ws?token={token}"
    ) as ws:
        ws.send_text("Test message")
        data = ws.receive_json()
        for field in ("id", "skill_id", "author_id", "author_name", "content", "created_at"):
            assert field in data, f"Missing field: {field}"


def test_websocket_message_persisted_in_history(client, auth_headers, skill_uuid, token):
    with client.websocket_connect(
        f"/api/v1/skills/{skill_uuid}/chat/ws?token={token}"
    ) as ws:
        ws.send_text("Persisted message")
        ws.receive_json()  # consume the broadcast

    # After disconnect, message should appear in history
    data = client.get(
        f"/api/v1/skills/{skill_uuid}/chat/history", headers=auth_headers
    ).json()
    contents = [m["content"] for m in data["messages"]]
    assert "Persisted message" in contents


def test_websocket_bad_token_closes_connection(client, skill_uuid):
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/api/v1/skills/{skill_uuid}/chat/ws?token=invalidtoken"
        ) as ws:
            ws.receive_json()


def test_websocket_missing_token_rejected(client, skill_uuid):
    with pytest.raises(Exception):
        with client.websocket_connect(
            f"/api/v1/skills/{skill_uuid}/chat/ws"
        ) as ws:
            ws.receive_json()


def test_websocket_history_sent_on_connect(client, auth_headers, skill_uuid, token):
    """Messages sent in a previous session should arrive as 'history' frames."""
    # Send a message in session 1
    with client.websocket_connect(
        f"/api/v1/skills/{skill_uuid}/chat/ws?token={token}"
    ) as ws:
        ws.send_text("Earlier message")
        ws.receive_json()

    # Connect again — should receive the earlier message as history
    with client.websocket_connect(
        f"/api/v1/skills/{skill_uuid}/chat/ws?token={token}"
    ) as ws:
        frame = ws.receive_json()
        assert frame["type"] == "history"
        assert frame["content"] == "Earlier message"


def test_websocket_empty_messages_ignored(client, skill_uuid, token):
    """Sending blank content should not produce a broadcast frame."""
    with client.websocket_connect(
        f"/api/v1/skills/{skill_uuid}/chat/ws?token={token}"
    ) as ws:
        ws.send_text("   ")
        # Send a real message after, to confirm connection is still alive
        ws.send_text("Real message")
        data = ws.receive_json()
        assert data["content"] == "Real message"
