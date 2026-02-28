"""Tests for POST /api/v1/auth/login."""


def test_login_success_returns_token(client, user_payload, registered_user):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": user_payload["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_login_wrong_password_returns_401(client, user_payload, registered_user):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "detail" in resp.json()


def test_login_wrong_email_returns_401(client, registered_user):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@nowhere.com", "password": "anypassword"},
    )
    assert resp.status_code == 401


def test_login_missing_credentials_returns_422(client):
    resp = client.post("/api/v1/auth/login", data={})
    assert resp.status_code == 422


def test_login_missing_password_returns_422(client, registered_user, user_payload):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"]},
    )
    assert resp.status_code == 422


def test_login_error_message_is_generic(client, user_payload, registered_user):
    """Wrong email and wrong password should return the same error message
    to prevent user enumeration."""
    wrong_pw = client.post(
        "/api/v1/auth/login",
        data={"username": user_payload["email"], "password": "bad"},
    )
    wrong_email = client.post(
        "/api/v1/auth/login",
        data={"username": "no@no.com", "password": user_payload["password"]},
    )
    assert wrong_pw.json()["detail"] == wrong_email.json()["detail"]
