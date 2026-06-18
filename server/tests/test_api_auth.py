"""Tests for auth endpoints and supporting service layer.

Verification checklist:
  - POST /api/auth/token valid credentials → 200 with token + user
  - POST /api/auth/token wrong password → invalid_credentials
  - POST /api/auth/token deactivated user → account_deactivated
  - POST /api/auth/logout → 204; token reuse → token_revoked
  - PATCH /api/auth/password correct → updated; old pw fails
  - PATCH /api/auth/password wrong current → invalid_credentials
  - GET /health → 200 (catch-all doesn't break existing routes)
  - RequestValidationError → {"error": {"code": "validation_error", ...}}
  - require_admin with member role → insufficient_role
  - hash_password + verify_password round-trip
  - create_token inserts; revoke_token deletes; second revoke is no-op
  - >10 login attempts/minute → 429 too_many_attempts
  - Tests run against SQLite and PostgreSQL
"""

import uuid

import pytest
from sqlmodel import Session, select

from porquilo.models.auth_token import AuthToken
from porquilo.models.user import User
from porquilo.services.auth_service import (
    create_token,
    create_user,
    hash_password,
    revoke_token,
    verify_password,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the in-memory rate limiter storage before each test so counters don't bleed."""
    from porquilo.core.limiter import limiter
    limiter._storage.reset()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(session, *, username=None, password="secret", role="member", is_active=True):
    uname = username or f"user_{uuid.uuid4().hex[:8]}"
    user = create_user(uname, password, role, session)
    user.is_active = is_active
    session.add(user)
    session.flush()
    return user


def _login(client, username, password):
    return client.post("/api/auth/token", json={"username": username, "password": password})


# ---------------------------------------------------------------------------
# Unit tests: password hashing
# ---------------------------------------------------------------------------


def test_hash_verify_roundtrip():
    hashed = hash_password("correct-horse")
    assert verify_password("correct-horse", hashed) is True
    assert verify_password("wrong-horse", hashed) is False


# ---------------------------------------------------------------------------
# Unit tests: token service
# ---------------------------------------------------------------------------


def test_create_token_inserts_row(db_session):
    user = _make_user(db_session)
    db_session.flush()

    token = create_token(user.id, db_session)
    db_session.flush()

    row = db_session.execute(select(AuthToken).where(AuthToken.token == token)).scalars().first()
    assert row is not None
    assert row.user_id == user.id


def test_revoke_token_deletes_row(db_session):
    user = _make_user(db_session)
    db_session.flush()
    token = create_token(user.id, db_session)
    db_session.flush()

    revoke_token(token, db_session)
    db_session.flush()

    gone = db_session.execute(select(AuthToken).where(AuthToken.token == token)).scalars().first()
    assert gone is None


def test_revoke_token_noop(db_session):
    # Second revoke should not raise
    user = _make_user(db_session)
    db_session.flush()
    token = create_token(user.id, db_session)
    db_session.flush()

    revoke_token(token, db_session)
    db_session.flush()
    revoke_token(token, db_session)  # no-op
    db_session.flush()


# ---------------------------------------------------------------------------
# API: existing routes unaffected
# ---------------------------------------------------------------------------


def test_health_unaffected(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# API: validation error shape
# ---------------------------------------------------------------------------


def test_validation_error_shape(client):
    # Missing both required fields
    resp = client.post("/api/auth/token", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Validation failed."
    assert "errors" in body["error"]["details"]


# ---------------------------------------------------------------------------
# API: login
# ---------------------------------------------------------------------------


def test_login_valid_credentials(client, db_session):
    user = _make_user(db_session, username="login_ok", password="pass1")
    db_session.flush()

    resp = _login(client, "login_ok", "pass1")
    assert resp.status_code == 200
    body = resp.json()
    assert "token" in body
    assert body["user"]["username"] == "login_ok"
    assert body["user"]["role"] == "member"
    assert "id" in body["user"]


def test_login_wrong_password(client, db_session):
    _make_user(db_session, username="login_badpw", password="correct")
    db_session.flush()

    resp = _login(client, "login_badpw", "wrong")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_credentials"


def test_login_unknown_user(client):
    resp = _login(client, "no_such_user", "anything")
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_credentials"


def test_login_deactivated_user(client, db_session):
    _make_user(db_session, username="login_deact", password="pw", is_active=False)
    db_session.flush()

    resp = _login(client, "login_deact", "pw")
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "account_deactivated"


# ---------------------------------------------------------------------------
# API: logout
# ---------------------------------------------------------------------------


def test_logout_returns_204(client, db_session):
    user = _make_user(db_session, username="logout_ok", password="pw")
    db_session.flush()

    login_resp = _login(client, "logout_ok", "pw")
    token = login_resp.json()["token"]

    resp = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 204


def test_logout_then_token_revoked(client, db_session):
    user = _make_user(db_session, username="logout_rev", password="pw")
    db_session.flush()

    token = _login(client, "logout_rev", "pw").json()["token"]
    client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})

    resp = client.patch(
        "/api/auth/password",
        json={"current_password": "pw", "new_password": "new"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "token_revoked"


# ---------------------------------------------------------------------------
# API: change password
# ---------------------------------------------------------------------------


def test_change_password_success(client, db_session):
    user = _make_user(db_session, username="chpw_ok", password="old_pass")
    db_session.flush()

    token = _login(client, "chpw_ok", "old_pass").json()["token"]

    resp = client.patch(
        "/api/auth/password",
        json={"current_password": "old_pass", "new_password": "new_pass"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Password updated."

    # Old password should no longer work
    assert _login(client, "chpw_ok", "old_pass").status_code == 400

    # New password should authenticate
    assert _login(client, "chpw_ok", "new_pass").status_code == 200


def test_change_password_wrong_current(client, db_session):
    user = _make_user(db_session, username="chpw_bad", password="real_pass")
    db_session.flush()

    token = _login(client, "chpw_bad", "real_pass").json()["token"]

    resp = client.patch(
        "/api/auth/password",
        json={"current_password": "wrong_pass", "new_password": "new"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "invalid_credentials"


# ---------------------------------------------------------------------------
# API: require_admin
# ---------------------------------------------------------------------------


def test_require_admin_member_rejected(client, db_session):
    """A member-role user hitting an admin-only endpoint gets insufficient_role."""
    from porquilo.core.deps import require_admin
    from porquilo.main import app

    # Add a throwaway admin-only route for this test
    from fastapi import Depends
    from fastapi.routing import APIRoute

    called = []

    @app.get("/_test_admin_only", include_in_schema=False)
    def _admin_only(user: User = Depends(require_admin)):
        called.append(user.id)
        return {"ok": True}

    try:
        user = _make_user(db_session, username="admin_test_member", role="member", password="pw")
        db_session.flush()

        token = _login(client, "admin_test_member", "pw").json()["token"]
        resp = client.get("/_test_admin_only", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "insufficient_role"
    finally:
        # Remove the temporary route
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/_test_admin_only"]


def test_require_admin_admin_allowed(client, db_session):
    from porquilo.core.deps import require_admin
    from porquilo.main import app
    from fastapi import Depends

    @app.get("/_test_admin_only2", include_in_schema=False)
    def _admin_only2(user: User = Depends(require_admin)):
        return {"ok": True}

    try:
        _make_user(db_session, username="admin_test_admin", role="admin", password="pw")
        db_session.flush()

        token = _login(client, "admin_test_admin", "pw").json()["token"]
        resp = client.get("/_test_admin_only2", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
    finally:
        app.routes[:] = [r for r in app.routes if getattr(r, "path", None) != "/_test_admin_only2"]


# ---------------------------------------------------------------------------
# Rate limiting: >10 attempts/minute → 429 too_many_attempts
# ---------------------------------------------------------------------------


def test_rate_limit_exceeded(client, db_session):
    """Firing 11 login requests from the same IP triggers the 429 envelope."""
    _make_user(db_session, username="rl_user", password="pw")
    db_session.flush()

    last_resp = None
    for _ in range(11):
        last_resp = _login(client, "rl_user", "pw")
        if last_resp.status_code == 429:
            break

    assert last_resp is not None
    assert last_resp.status_code == 429
    body = last_resp.json()
    assert body["error"]["code"] == "too_many_attempts"
