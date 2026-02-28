"""Tests for the /health endpoint."""


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_body_healthy(client):
    resp = client.get("/health")
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_health_is_json(client):
    resp = client.get("/health")
    assert resp.headers["content-type"].startswith("application/json")
