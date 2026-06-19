"""Tests for GET/PATCH /api/profile.

Verification checklist:
  - GET /api/profile returns name, units_preference, timezone for authenticated user
  - PATCH /api/profile updates fields; GET /api/profile reflects changes
  - PATCH /api/profile with units_preference="cups" returns 422
"""

from __future__ import annotations


def test_get_profile(client, auth_headers):
    resp = client.get("/api/profile", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"name", "units_preference", "timezone"}


def test_patch_profile_updates_fields(client, auth_headers):
    resp = client.patch(
        "/api/profile",
        json={"name": "Pat", "units_preference": "metric", "timezone": "UTC"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"name": "Pat", "units_preference": "metric", "timezone": "UTC"}

    resp = client.get("/api/profile", headers=auth_headers)
    assert resp.json() == {"name": "Pat", "units_preference": "metric", "timezone": "UTC"}


def test_patch_profile_invalid_units_preference(client, auth_headers):
    resp = client.patch(
        "/api/profile",
        json={"units_preference": "cups"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


def test_patch_profile_requires_auth(client):
    resp = client.patch("/api/profile", json={"name": "Pat"})
    assert resp.status_code == 401
