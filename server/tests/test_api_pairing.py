"""Tests for QR pairing endpoints.

Verification checklist:
  - POST /api/users/{id}/pairing-code returns code and expires_at for a valid user
  - POST /api/users/{id}/pairing-code by a non-admin returns insufficient_role
  - POST /api/users/{id}/pairing-code with unknown user_id returns 404
  - POST /api/auth/pairing/exchange with a valid unused code returns a bearer token
  - Returned bearer token authenticates a request to GET /api/users (admin) or returns 403 (member)
  - Second exchange of the same code returns 422 pairing_code_already_used
  - Exchange of an expired code returns 422 pairing_code_expired
  - Exchange of a nonexistent code returns 422 invalid_pairing_code
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select

from porquilo.models.pairing_code import PairingCode
from porquilo.services.auth_service import create_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(session, *, username=None, role="member", password="secret"):
    uname = username or f"user_{uuid.uuid4().hex[:8]}"
    user = create_user(uname, password, role, session)
    session.flush()
    return user


def _generate_code(client, user_id, admin_headers):
    return client.post(f"/api/users/{user_id}/pairing-code", headers=admin_headers)


def _exchange(client, code):
    return client.post("/api/auth/pairing/exchange", json={"code": code})


# ---------------------------------------------------------------------------
# POST /api/users/{id}/pairing-code
# ---------------------------------------------------------------------------


def test_generate_pairing_code_success(client, db_session, admin_user, admin_headers):
    target = _make_user(db_session, username="pair_target")
    resp = _generate_code(client, target.id, admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert "code" in body
    assert "expires_at" in body
    assert len(body["code"]) > 10


def test_generate_pairing_code_non_admin_rejected(client, db_session, test_user, auth_headers):
    resp = _generate_code(client, test_user.id, auth_headers)
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "insufficient_role"


def test_generate_pairing_code_unknown_user(client, admin_headers):
    resp = _generate_code(client, uuid.uuid4(), admin_headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/auth/pairing/exchange
# ---------------------------------------------------------------------------


def test_exchange_valid_code_returns_token(client, db_session, admin_user, admin_headers):
    resp = _generate_code(client, admin_user.id, admin_headers)
    code = resp.json()["code"]

    exch = _exchange(client, code)
    assert exch.status_code == 200
    body = exch.json()
    assert "token" in body
    assert body["user"]["id"] == str(admin_user.id)
    assert body["user"]["username"] == admin_user.username
    assert body["user"]["role"] == admin_user.role


def test_exchanged_token_authenticates(client, db_session, admin_user, admin_headers):
    resp = _generate_code(client, admin_user.id, admin_headers)
    code = resp.json()["code"]
    token = _exchange(client, code).json()["token"]

    # The exchanged token must work on any authenticated endpoint
    check = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert check.status_code == 200


def test_exchange_member_token_authenticates(client, db_session, admin_headers):
    member = _make_user(db_session, username="pair_member", role="member")
    resp = _generate_code(client, member.id, admin_headers)
    code = resp.json()["code"]
    token = _exchange(client, code).json()["token"]

    # Member token is valid (returns 403, not 401)
    check = client.get("/api/users", headers={"Authorization": f"Bearer {token}"})
    assert check.status_code == 403
    assert check.json()["error"]["code"] == "insufficient_role"


def test_exchange_used_code_rejected(client, db_session, admin_user, admin_headers):
    resp = _generate_code(client, admin_user.id, admin_headers)
    code = resp.json()["code"]

    _exchange(client, code)  # first use
    second = _exchange(client, code)  # second use
    assert second.status_code == 422
    assert second.json()["error"]["code"] == "pairing_code_already_used"


def test_exchange_expired_code_rejected(client, db_session, admin_user):
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    expired_code = "expired-code-xyz"
    pairing = PairingCode(
        user_id=admin_user.id,
        code=expired_code,
        expires_at=now - timedelta(minutes=1),
        created_at=now - timedelta(minutes=16),
    )
    db_session.add(pairing)
    db_session.flush()

    resp = _exchange(client, expired_code)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "pairing_code_expired"


def test_exchange_nonexistent_code_rejected(client):
    resp = _exchange(client, "does-not-exist")
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_pairing_code"
