"""Tests for migration 017: pairing_codes table.

Covers the VERIFICATION checklist items:
  - Migration applies and rolls back cleanly on SQLite and PostgreSQL
  - pairing_codes table and all columns exist
  - ix_pairing_codes_code index exists (unique)
  - code column is unique (duplicate → IntegrityError)
  - user_id is NOT NULL (null insert → IntegrityError)
  - Deleting a user cascades to their pairing_codes rows
  - PairingCode model field count matches inspect(engine).get_columns("pairing_codes")
"""

import os
import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

_NOW = datetime(2026, 6, 22, 0, 0, 0)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exec(engine, sql, params=None):
    with engine.begin() as conn:
        conn.execute(sa.text(sql), params or {})


def _scalar(engine, sql, params=None):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params or {}).scalar()


def _table_names(engine):
    return inspect(engine).get_table_names()


def _index_names(engine, table):
    return {idx["name"] for idx in inspect(engine).get_indexes(table)}


def _column_names(engine, table):
    return {col["name"] for col in inspect(engine).get_columns(table)}


def _alembic_cfg(engine):
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", engine.url.render_as_string(hide_password=False))
    cfg.attributes["configure_logger"] = False
    return cfg


def _insert_user(engine, *, username="alice", role="admin"):
    uid = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO users (id, username, hashed_password, role, is_active)"
        " VALUES (:id, :username, :pw, :role, true)",
        {"id": uid, "username": username, "pw": "hashed", "role": role},
    )
    return uid


def _insert_pairing_code(engine, user_id, *, code=None, expires_at=None):
    row_id = str(uuid.uuid4())
    code = code or secrets_token()
    expires_at = expires_at or _NOW
    _exec(
        engine,
        "INSERT INTO pairing_codes (id, user_id, code, expires_at)"
        " VALUES (:id, :user_id, :code, :expires_at)",
        {"id": row_id, "user_id": user_id, "code": code, "expires_at": expires_at},
    )
    return row_id


def secrets_token():
    import secrets
    return secrets.token_urlsafe(16)


# ---------------------------------------------------------------------------
# Schema: table exists
# ---------------------------------------------------------------------------


def test_pairing_codes_table_exists(engine_017):
    assert "pairing_codes" in _table_names(engine_017)


# ---------------------------------------------------------------------------
# Schema: columns present
# ---------------------------------------------------------------------------


def test_pairing_codes_columns(engine_017):
    expected = {"id", "user_id", "code", "expires_at", "used_at", "created_at"}
    assert expected <= _column_names(engine_017, "pairing_codes")


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------


def test_pairing_codes_code_index_exists(engine_017):
    assert "ix_pairing_codes_code" in _index_names(engine_017, "pairing_codes")


# ---------------------------------------------------------------------------
# Constraint: code unique
# ---------------------------------------------------------------------------


def test_code_unique(engine_017):
    uid = _insert_user(engine_017, username="unique_code_user")
    shared_code = "code-unique-test"
    _insert_pairing_code(engine_017, uid, code=shared_code)
    with pytest.raises(sa.exc.IntegrityError):
        _insert_pairing_code(engine_017, uid, code=shared_code)


# ---------------------------------------------------------------------------
# Constraint: user_id NOT NULL
# ---------------------------------------------------------------------------


def test_user_id_not_null(engine_017):
    with pytest.raises(sa.exc.IntegrityError):
        row_id = str(uuid.uuid4())
        _exec(
            engine_017,
            "INSERT INTO pairing_codes (id, user_id, code, expires_at)"
            " VALUES (:id, NULL, 'some-code', :ts)",
            {"id": row_id, "ts": _NOW},
        )


# ---------------------------------------------------------------------------
# Cascade: deleting a user removes their pairing_codes
# ---------------------------------------------------------------------------


def test_cascade_delete_pairing_codes(engine_017):
    uid = _insert_user(engine_017, username="cascade_pair_user")
    _insert_pairing_code(engine_017, uid, code="cascade-code-1")
    _insert_pairing_code(engine_017, uid, code="cascade-code-2")

    count_before = _scalar(
        engine_017,
        "SELECT COUNT(*) FROM pairing_codes WHERE user_id = :uid",
        {"uid": uid},
    )
    assert count_before == 2

    _exec(engine_017, "DELETE FROM users WHERE id = :uid", {"uid": uid})

    count_after = _scalar(
        engine_017,
        "SELECT COUNT(*) FROM pairing_codes WHERE user_id = :uid",
        {"uid": uid},
    )
    assert count_after == 0


# ---------------------------------------------------------------------------
# Model ↔ schema column-count parity
# ---------------------------------------------------------------------------


def test_pairing_code_model_column_count(engine_017):
    from porquilo.models.pairing_code import PairingCode

    model_cols = len(PairingCode.__table__.columns)
    db_cols = len(inspect(engine_017).get_columns("pairing_codes"))
    assert model_cols == db_cols, (
        f"PairingCode model has {model_cols} columns but DB has {db_cols}"
    )


# ---------------------------------------------------------------------------
# Downgrade: table is removed
# ---------------------------------------------------------------------------


def test_downgrade(engine_017):
    cfg = _alembic_cfg(engine_017)
    command.downgrade(cfg, "016")

    assert "pairing_codes" not in _table_names(engine_017)

    # Re-apply so fixture teardown (downgrade to base) works cleanly
    command.upgrade(cfg, "017")
