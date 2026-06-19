"""Tests for admin user management endpoints (POST/GET /api/users, PATCH, reset-password).

Verification checklist:
  - POST /api/users creates a user; GET /api/users returns them
  - POST /api/users with a duplicate username returns 422 with code "username_taken"
  - PATCH /api/users/{id} with is_active=false deactivates user; subsequent login
    returns account_deactivated
  - PATCH /api/users/{id} where id == current_user.id returns 409 with cannot_deactivate_self
  - POST /api/users/{id}/reset-password updates hash; old password fails; all prior
    tokens revoked
  - GET /api/users by a member-role user returns insufficient_role
  - hashed_password never appears in any GET /api/users or POST /api/users response
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the in-memory rate limiter storage before each test so counters don't bleed."""
    from porquilo.core.limiter import limiter
    limiter._storage.reset()


def test_create_and_list_users(client, admin_headers):
    resp = client.post(
        "/api/users",
        json={"username": "newbie", "password": "secret123", "role": "member"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    created = resp.json()
    assert created["username"] == "newbie"
    assert created["role"] == "member"
    assert created["is_active"] is True
    assert "hashed_password" not in created

    resp = client.get("/api/users", headers=admin_headers)
    assert resp.status_code == 200
    usernames = {u["username"] for u in resp.json()}
    assert "newbie" in usernames
    for u in resp.json():
        assert "hashed_password" not in u


def test_create_user_duplicate_username(client, admin_headers, admin_user):
    resp = client.post(
        "/api/users",
        json={"username": admin_user.username, "password": "whatever"},
        headers=admin_headers,
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "username_taken"


def test_patch_user_deactivate(client, admin_headers, test_user):
    resp = client.patch(
        f"/api/users/{test_user.id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    login = client.post(
        "/api/auth/token",
        json={"username": test_user.username, "password": "testpass"},
    )
    assert login.status_code == 403
    assert login.json()["error"]["code"] == "account_deactivated"


def test_patch_user_cannot_deactivate_self(client, admin_headers, admin_user):
    resp = client.patch(
        f"/api/users/{admin_user.id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "cannot_deactivate_self"


def test_patch_user_not_found(client, admin_headers):
    import uuid

    resp = client.patch(
        f"/api/users/{uuid.uuid4()}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 404


def test_reset_password_revokes_tokens(client, admin_headers, test_user, auth_headers):
    resp = client.get("/api/profile", headers=auth_headers)
    assert resp.status_code == 200

    resp = client.post(
        f"/api/users/{test_user.id}/reset-password",
        json={"new_password": "newpassword456"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"message": "Password reset."}

    resp = client.get("/api/profile", headers=auth_headers)
    assert resp.status_code == 401

    old_login = client.post(
        "/api/auth/token",
        json={"username": test_user.username, "password": "testpass"},
    )
    assert old_login.status_code == 400
    assert old_login.json()["error"]["code"] == "invalid_credentials"

    new_login = client.post(
        "/api/auth/token",
        json={"username": test_user.username, "password": "newpassword456"},
    )
    assert new_login.status_code == 200


def test_list_users_requires_admin(client, auth_headers):
    resp = client.get("/api/users", headers=auth_headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "insufficient_role"
