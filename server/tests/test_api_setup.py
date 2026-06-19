"""Tests for the first-run setup wizard (GET /api/setup/status, POST /api/setup/init).

Verification checklist:
  - GET /api/setup/status returns { "initialized": false } on a fresh database,
    { "initialized": true } after POST /api/setup/init succeeds
  - POST /api/setup/init creates the first admin and returns a token
  - POST /api/setup/init returns 404 if any user already exists
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset the in-memory rate limiter storage before each test so counters don't bleed."""
    from porquilo.core.limiter import limiter
    limiter._storage.reset()


def test_setup_status_fresh_database(client):
    resp = client.get("/api/setup/status")
    assert resp.status_code == 200
    assert resp.json() == {"initialized": False}


def test_setup_init_creates_first_admin(client):
    resp = client.post(
        "/api/setup/init",
        json={"username": "owner", "password": "ownerpass", "name": "Owner"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data and data["token"]
    assert data["user"]["username"] == "owner"
    assert data["user"]["role"] == "admin"

    status_resp = client.get("/api/setup/status")
    assert status_resp.json() == {"initialized": True}

    login = client.post("/api/auth/token", json={"username": "owner", "password": "ownerpass"})
    assert login.status_code == 200


def test_setup_init_disabled_after_first_user(client, test_user):
    resp = client.post(
        "/api/setup/init",
        json={"username": "second", "password": "whatever"},
    )
    assert resp.status_code == 404
