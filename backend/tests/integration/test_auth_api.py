"""Integration tests for the JWT authentication API."""
from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from app.main import create_app
from app.di import container


@pytest.fixture()
def auth_client():
    """TestClient without the auth dependency override — real JWT flows."""
    container.reset()
    app = create_app(enable_trading_worker=False)
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

def test_register_first_user_gets_default_tenant(auth_client):
    """The very first registered user should land in tenant 'default'."""
    resp = auth_client.post(
        "/v1/auth/register",
        json={"email": "first@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "first@example.com"
    assert data["user"]["tenant_id"] == "default"
    assert data["user"]["role"] == "owner"


def test_register_second_user_gets_own_tenant(auth_client):
    """Subsequent registrations should each get a unique tenant."""
    auth_client.post(
        "/v1/auth/register",
        json={"email": "first@example.com", "password": "pw1"},
    )
    resp = auth_client.post(
        "/v1/auth/register",
        json={"email": "second@example.com", "password": "pw2"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["tenant_id"].startswith("tenant_")


def test_register_duplicate_email_returns_400(auth_client):
    auth_client.post(
        "/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )
    resp = auth_client.post(
        "/v1/auth/register",
        json={"email": "dup@example.com", "password": "password456"},
    )
    assert resp.status_code == 400


def test_register_with_display_name(auth_client):
    resp = auth_client.post(
        "/v1/auth/register",
        json={"email": "named@example.com", "password": "pw", "display_name": "Alice"},
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["display_name"] == "Alice"


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def test_login_valid_credentials(auth_client):
    auth_client.post(
        "/v1/auth/register",
        json={"email": "login@example.com", "password": "mypassword"},
    )
    resp = auth_client.post(
        "/v1/auth/login",
        json={"email": "login@example.com", "password": "mypassword"},
    )
    assert resp.status_code == 200
    assert "token" in resp.json()


def test_login_wrong_password_returns_401(auth_client):
    auth_client.post(
        "/v1/auth/register",
        json={"email": "wrong@example.com", "password": "correct"},
    )
    resp = auth_client.post(
        "/v1/auth/login",
        json={"email": "wrong@example.com", "password": "incorrect"},
    )
    assert resp.status_code == 401


def test_login_unknown_email_returns_401(auth_client):
    resp = auth_client.post(
        "/v1/auth/login",
        json={"email": "nobody@example.com", "password": "pw"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# /me endpoint
# ---------------------------------------------------------------------------

def test_me_returns_user_info(auth_client):
    reg = auth_client.post(
        "/v1/auth/register",
        json={"email": "me@example.com", "password": "pw"},
    )
    token = reg.json()["token"]
    resp = auth_client.get(
        "/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


def test_me_without_token_returns_401(auth_client):
    resp = auth_client.get("/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_token_returns_401(auth_client):
    resp = auth_client.get(
        "/v1/auth/me",
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Protected endpoints require auth
# ---------------------------------------------------------------------------

def test_protected_endpoint_rejects_unauthenticated(auth_client):
    """A protected route should return 401 when no token is provided."""
    resp = auth_client.get("/v1/market/state")
    assert resp.status_code == 401


def test_protected_endpoint_accepts_valid_token(auth_client):
    reg = auth_client.post(
        "/v1/auth/register",
        json={"email": "protected@example.com", "password": "pw"},
    )
    token = reg.json()["token"]
    resp = auth_client.get(
        "/v1/market/state",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Change password
# ---------------------------------------------------------------------------

def test_change_password_success(auth_client):
    reg = auth_client.post(
        "/v1/auth/register",
        json={"email": "chpw@example.com", "password": "oldpw123"},
    )
    token = reg.json()["token"]

    resp = auth_client.post(
        "/v1/auth/change-password",
        json={"current_password": "oldpw123", "new_password": "newpw456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200

    # Old password should no longer work
    bad = auth_client.post(
        "/v1/auth/login",
        json={"email": "chpw@example.com", "password": "oldpw123"},
    )
    assert bad.status_code == 401

    # New password should work
    ok = auth_client.post(
        "/v1/auth/login",
        json={"email": "chpw@example.com", "password": "newpw456"},
    )
    assert ok.status_code == 200


def test_change_password_wrong_current_returns_400(auth_client):
    reg = auth_client.post(
        "/v1/auth/register",
        json={"email": "badpw@example.com", "password": "correct"},
    )
    token = reg.json()["token"]

    resp = auth_client.post(
        "/v1/auth/change-password",
        json={"current_password": "wrong", "new_password": "newpw"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
