"""Tests for migration 016: users, auth_tokens, and user_id columns.

Covers the VERIFICATION checklist items:
  - Migration applies and rolls back cleanly on SQLite and PostgreSQL
  - users.username is unique
  - users.role CHECK accepts 'admin' and 'member'; rejects others
  - users.units_preference CHECK accepts 'metric', 'imperial', NULL; rejects others
  - auth_tokens.token is unique
  - Deleting a user cascades to their auth_tokens rows
  - log_entries/body_metrics/goals each gain a nullable user_id column
  - Inserting a log_entries row with user_id=NULL succeeds
  - Deleting a user sets log_entries.user_id to NULL (ON DELETE SET NULL)
  - All five indexes exist via inspect(engine).get_indexes()
  - Each SQLModel model's field count matches inspect(engine).get_columns()
"""

import os
import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

_NOW = datetime(2026, 6, 17, 0, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers (mirrors test_015 pattern)
# ---------------------------------------------------------------------------


def _exec(engine, sql, params=None):
    with engine.begin() as conn:
        conn.execute(sa.text(sql), params or {})


def _scalar(engine, sql, params=None):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params or {}).scalar()


def _fetchall(engine, sql, params=None):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params or {}).fetchall()


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


def _insert_user(engine, *, username="alice", role="admin", units_preference="metric"):
    uid = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO users (id, username, hashed_password, role, units_preference, is_active)"
        " VALUES (:id, :username, :pw, :role, :units, true)",
        {"id": uid, "username": username, "pw": "hashed", "role": role, "units": units_preference},
    )
    return uid


def _insert_food_source_and_meal(engine):
    """Return (food_source_id, meal_id) needed to build a log_entry row."""
    fs_id = _scalar(engine, "SELECT id FROM food_sources WHERE key = 'custom'")
    meal_id = _scalar(engine, "SELECT id FROM meals LIMIT 1")
    return str(fs_id), str(meal_id)


def _insert_log_entry(engine, meal_id, food_source_id, user_id=None):
    entry_id = str(uuid.uuid4())
    food_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO foods (id, name, brand, food_source_id, default_unit, created_at, updated_at)"
        " VALUES (:id, 'Apple', NULL, :fs_id, 'g', :ts, :ts)",
        {"id": food_id, "fs_id": food_source_id, "ts": _NOW},
    )
    _exec(
        engine,
        "INSERT INTO log_entries"
        " (id, food_id, meal_id, eaten_at, logged_at, weight_source, weight_confidence, input_method, user_id)"
        " VALUES (:id, :food_id, :meal_id, :ts, :ts, 'manual', 'high', 'manual', :user_id)",
        {"id": entry_id, "food_id": food_id, "meal_id": meal_id, "ts": _NOW, "user_id": user_id},
    )
    return entry_id


# ---------------------------------------------------------------------------
# Schema: tables exist
# ---------------------------------------------------------------------------


def test_users_table_exists(engine_016):
    assert "users" in _table_names(engine_016)


def test_auth_tokens_table_exists(engine_016):
    assert "auth_tokens" in _table_names(engine_016)


# ---------------------------------------------------------------------------
# Schema: columns present
# ---------------------------------------------------------------------------


def test_users_columns(engine_016):
    expected = {
        "id", "username", "hashed_password", "role", "name",
        "units_preference", "timezone", "is_active", "created_at", "updated_at",
    }
    assert expected <= _column_names(engine_016, "users")


def test_auth_tokens_columns(engine_016):
    expected = {"id", "user_id", "token", "created_at", "last_used_at"}
    assert expected <= _column_names(engine_016, "auth_tokens")


def test_log_entries_has_user_id(engine_016):
    assert "user_id" in _column_names(engine_016, "log_entries")


def test_body_metrics_has_user_id(engine_016):
    assert "user_id" in _column_names(engine_016, "body_metrics")


def test_goals_has_user_id(engine_016):
    assert "user_id" in _column_names(engine_016, "goals")


# ---------------------------------------------------------------------------
# Constraints: users.username unique
# ---------------------------------------------------------------------------


def test_username_unique(engine_016):
    _insert_user(engine_016, username="unique_u1")
    with pytest.raises(sa.exc.IntegrityError):
        _insert_user(engine_016, username="unique_u1")


# ---------------------------------------------------------------------------
# Constraints: users.role CHECK
# ---------------------------------------------------------------------------


def test_role_check_accepts_admin(engine_016):
    _insert_user(engine_016, username="role_admin", role="admin")


def test_role_check_accepts_member(engine_016):
    _insert_user(engine_016, username="role_member", role="member")


def test_role_check_rejects_invalid(engine_016):
    with pytest.raises(sa.exc.IntegrityError):
        uid = str(uuid.uuid4())
        _exec(
            engine_016,
            "INSERT INTO users (id, username, hashed_password, role, is_active)"
            " VALUES (:id, 'bad_role', 'pw', 'superuser', true)",
            {"id": uid},
        )


# ---------------------------------------------------------------------------
# Constraints: users.units_preference CHECK
# ---------------------------------------------------------------------------


def test_units_preference_accepts_metric(engine_016):
    _insert_user(engine_016, username="up_metric", units_preference="metric")


def test_units_preference_accepts_imperial(engine_016):
    _insert_user(engine_016, username="up_imperial", units_preference="imperial")


def test_units_preference_accepts_null(engine_016):
    uid = str(uuid.uuid4())
    _exec(
        engine_016,
        "INSERT INTO users (id, username, hashed_password, role, is_active)"
        " VALUES (:id, 'up_null', 'pw', 'admin', true)",
        {"id": uid},
    )


def test_units_preference_rejects_invalid(engine_016):
    with pytest.raises(sa.exc.IntegrityError):
        uid = str(uuid.uuid4())
        _exec(
            engine_016,
            "INSERT INTO users (id, username, hashed_password, role, units_preference, is_active)"
            " VALUES (:id, 'up_bad', 'pw', 'admin', 'standard', true)",
            {"id": uid},
        )


# ---------------------------------------------------------------------------
# Constraints: auth_tokens.token unique
# ---------------------------------------------------------------------------


def test_auth_token_unique(engine_016):
    uid = _insert_user(engine_016, username="tok_user")
    tok_id1 = str(uuid.uuid4())
    tok_id2 = str(uuid.uuid4())
    _exec(
        engine_016,
        "INSERT INTO auth_tokens (id, user_id, token) VALUES (:id, :uid, 'secret-token-abc')",
        {"id": tok_id1, "uid": uid},
    )
    with pytest.raises(sa.exc.IntegrityError):
        _exec(
            engine_016,
            "INSERT INTO auth_tokens (id, user_id, token) VALUES (:id, :uid, 'secret-token-abc')",
            {"id": tok_id2, "uid": uid},
        )


# ---------------------------------------------------------------------------
# Cascade: deleting a user removes their auth_tokens
# ---------------------------------------------------------------------------


def test_cascade_delete_auth_tokens(engine_016):
    uid = _insert_user(engine_016, username="cascade_user")
    tok_id = str(uuid.uuid4())
    _exec(
        engine_016,
        "INSERT INTO auth_tokens (id, user_id, token) VALUES (:id, :uid, 'cascade-tok')",
        {"id": tok_id, "uid": uid},
    )
    count_before = _scalar(
        engine_016, "SELECT COUNT(*) FROM auth_tokens WHERE user_id = :uid", {"uid": uid}
    )
    assert count_before == 1

    _exec(engine_016, "DELETE FROM users WHERE id = :uid", {"uid": uid})

    count_after = _scalar(
        engine_016, "SELECT COUNT(*) FROM auth_tokens WHERE user_id = :uid", {"uid": uid}
    )
    assert count_after == 0


# ---------------------------------------------------------------------------
# ON DELETE SET NULL: log_entries.user_id becomes NULL when user is deleted
# ---------------------------------------------------------------------------


def test_log_entries_user_id_nullable(engine_016):
    fs_id, meal_id = _insert_food_source_and_meal(engine_016)
    # Should not raise — user_id=NULL is valid
    _insert_log_entry(engine_016, meal_id, fs_id, user_id=None)


def test_on_delete_set_null_log_entries(engine_016):
    uid = _insert_user(engine_016, username="setnull_user")
    fs_id, meal_id = _insert_food_source_and_meal(engine_016)
    entry_id = _insert_log_entry(engine_016, meal_id, fs_id, user_id=uid)

    user_id_before = _scalar(
        engine_016, "SELECT user_id FROM log_entries WHERE id = :eid", {"eid": entry_id}
    )
    assert user_id_before is not None

    _exec(engine_016, "DELETE FROM users WHERE id = :uid", {"uid": uid})

    user_id_after = _scalar(
        engine_016, "SELECT user_id FROM log_entries WHERE id = :eid", {"eid": entry_id}
    )
    assert user_id_after is None


# ---------------------------------------------------------------------------
# body_metrics and goals: nullable user_id inserts
# ---------------------------------------------------------------------------


def test_body_metrics_user_id_nullable(engine_016):
    bm_id = str(uuid.uuid4())
    _exec(
        engine_016,
        "INSERT INTO body_metrics (id, metric_type, source, user_id)"
        " VALUES (:id, 'weight_kg', 'manual', NULL)",
        {"id": bm_id},
    )
    val = _scalar(engine_016, "SELECT user_id FROM body_metrics WHERE id = :id", {"id": bm_id})
    assert val is None


def test_goals_user_id_nullable(engine_016):
    g_id = str(uuid.uuid4())
    _exec(
        engine_016,
        "INSERT INTO goals (id, calorie_mode, calorie_target, effective_from, user_id)"
        " VALUES (:id, 'fixed', 2000, '2026-01-01', NULL)",
        {"id": g_id},
    )
    val = _scalar(engine_016, "SELECT user_id FROM goals WHERE id = :id", {"id": g_id})
    assert val is None


# ---------------------------------------------------------------------------
# Indexes: all five present
# ---------------------------------------------------------------------------


def test_all_five_indexes_exist(engine_016):
    assert "ix_auth_tokens_token" in _index_names(engine_016, "auth_tokens")
    assert "ix_auth_tokens_user_id" in _index_names(engine_016, "auth_tokens")
    assert "ix_log_entries_user_id" in _index_names(engine_016, "log_entries")
    assert "ix_body_metrics_user_id" in _index_names(engine_016, "body_metrics")
    assert "ix_goals_user_id" in _index_names(engine_016, "goals")


# ---------------------------------------------------------------------------
# Model ↔ schema column-count parity
# ---------------------------------------------------------------------------


def test_user_model_column_count(engine_016):
    from porquilo.models.user import User

    model_cols = len(User.__table__.columns)
    db_cols = len(inspect(engine_016).get_columns("users"))
    assert model_cols == db_cols, (
        f"User model has {model_cols} columns but DB has {db_cols}"
    )


def test_auth_token_model_column_count(engine_016):
    from porquilo.models.auth_token import AuthToken

    model_cols = len(AuthToken.__table__.columns)
    db_cols = len(inspect(engine_016).get_columns("auth_tokens"))
    assert model_cols == db_cols, (
        f"AuthToken model has {model_cols} columns but DB has {db_cols}"
    )


# ---------------------------------------------------------------------------
# Downgrade: tables and columns are removed
# ---------------------------------------------------------------------------


def test_downgrade(engine_016):
    cfg = _alembic_cfg(engine_016)
    command.downgrade(cfg, "015")

    tables = _table_names(engine_016)
    assert "users" not in tables
    assert "auth_tokens" not in tables
    assert "user_id" not in _column_names(engine_016, "log_entries")
    assert "user_id" not in _column_names(engine_016, "body_metrics")
    assert "user_id" not in _column_names(engine_016, "goals")

    # Re-apply so fixture teardown (downgrade to base) works cleanly
    command.upgrade(cfg, "016")
