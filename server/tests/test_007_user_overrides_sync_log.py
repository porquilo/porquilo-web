"""Tests for migration 007: user_overrides and sync_log."""

import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

_NOW = datetime(2026, 5, 29, 0, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _exec(engine, sql, params=None):
    with engine.begin() as conn:
        conn.execute(sa.text(sql), params or {})


def _scalar(engine, sql, params=None):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params or {}).scalar()


def _make_food(engine, *, source_key="open_food_facts") -> str:
    food_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO foods (id, name, food_source_id, default_unit, created_at, updated_at) "
        "SELECT :id, 'Test Food', id, 'g', :ts, :ts FROM food_sources WHERE key = :key",
        {"id": food_id, "ts": _NOW, "key": source_key},
    )
    return food_id


def _nutrient_id(engine) -> str:
    return str(_scalar(engine, "SELECT id FROM nutrient_definitions WHERE key = 'protein_g'"))


def _food_source_id(engine, key: str = "open_food_facts") -> str:
    return str(_scalar(engine, "SELECT id FROM food_sources WHERE key = :k", {"k": key}))


# ---------------------------------------------------------------------------
# user_overrides: basic inserts
# ---------------------------------------------------------------------------

def test_nutrient_override_insert(engine_007):
    """A nutrient override (nutrient_id set, field null) can be inserted."""
    food_id = _make_food(engine_007)
    nid = _nutrient_id(engine_007)
    ov_id = str(uuid.uuid4())
    _exec(
        engine_007,
        "INSERT INTO user_overrides"
        " (id, food_id, nutrient_id, field, original_value, corrected_value, corrected_at)"
        " VALUES (:id, :fid, :nid, NULL, '10.5', '11.0', :ts)",
        {"id": ov_id, "fid": food_id, "nid": nid, "ts": _NOW},
    )
    val = _scalar(engine_007, "SELECT corrected_value FROM user_overrides WHERE id = :id", {"id": ov_id})
    assert val == "11.0"


def test_field_override_insert(engine_007):
    """A field override (field set, nutrient_id null) can be inserted for any food."""
    food_id = _make_food(engine_007, source_key="custom")
    ov_id = str(uuid.uuid4())
    _exec(
        engine_007,
        "INSERT INTO user_overrides"
        " (id, food_id, field, nutrient_id, original_value, corrected_value, corrected_at)"
        " VALUES (:id, :fid, 'name', NULL, 'Old Name', 'New Name', :ts)",
        {"id": ov_id, "fid": food_id, "ts": _NOW},
    )
    val = _scalar(engine_007, "SELECT corrected_value FROM user_overrides WHERE id = :id", {"id": ov_id})
    assert val == "New Name"


# ---------------------------------------------------------------------------
# user_overrides: CHECK field XOR nutrient_id
# ---------------------------------------------------------------------------

def test_check_rejects_both_field_and_nutrient(engine_007):
    """CHECK constraint rejects a row with both field and nutrient_id set."""
    food_id = _make_food(engine_007)
    nid = _nutrient_id(engine_007)
    with pytest.raises(IntegrityError):
        _exec(
            engine_007,
            "INSERT INTO user_overrides"
            " (id, food_id, field, nutrient_id, corrected_value, corrected_at)"
            " VALUES (:id, :fid, 'name', :nid, 'X', :ts)",
            {"id": str(uuid.uuid4()), "fid": food_id, "nid": nid, "ts": _NOW},
        )


def test_check_rejects_neither_field_nor_nutrient(engine_007):
    """CHECK constraint rejects a row with neither field nor nutrient_id set."""
    food_id = _make_food(engine_007)
    with pytest.raises(IntegrityError):
        _exec(
            engine_007,
            "INSERT INTO user_overrides"
            " (id, food_id, field, nutrient_id, corrected_value, corrected_at)"
            " VALUES (:id, :fid, NULL, NULL, 'X', :ts)",
            {"id": str(uuid.uuid4()), "fid": food_id, "ts": _NOW},
        )


# ---------------------------------------------------------------------------
# user_overrides: unique constraints
# ---------------------------------------------------------------------------

def test_unique_nutrient_override_per_food(engine_007):
    """Unique constraint rejects a second nutrient override for the same (food_id, nutrient_id)."""
    food_id = _make_food(engine_007)
    nid = _nutrient_id(engine_007)
    _exec(
        engine_007,
        "INSERT INTO user_overrides (id, food_id, nutrient_id, corrected_value, corrected_at)"
        " VALUES (:id, :fid, :nid, '11.0', :ts)",
        {"id": str(uuid.uuid4()), "fid": food_id, "nid": nid, "ts": _NOW},
    )
    with pytest.raises(IntegrityError):
        _exec(
            engine_007,
            "INSERT INTO user_overrides (id, food_id, nutrient_id, corrected_value, corrected_at)"
            " VALUES (:id, :fid, :nid, '12.0', :ts)",
            {"id": str(uuid.uuid4()), "fid": food_id, "nid": nid, "ts": _NOW},
        )


def test_unique_field_override_per_food(engine_007):
    """Unique constraint rejects a second field override for the same (food_id, field)."""
    food_id = _make_food(engine_007)
    _exec(
        engine_007,
        "INSERT INTO user_overrides (id, food_id, field, corrected_value, corrected_at)"
        " VALUES (:id, :fid, 'name', 'First', :ts)",
        {"id": str(uuid.uuid4()), "fid": food_id, "ts": _NOW},
    )
    with pytest.raises(IntegrityError):
        _exec(
            engine_007,
            "INSERT INTO user_overrides (id, food_id, field, corrected_value, corrected_at)"
            " VALUES (:id, :fid, 'name', 'Second', :ts)",
            {"id": str(uuid.uuid4()), "fid": food_id, "ts": _NOW},
        )


# ---------------------------------------------------------------------------
# user_overrides: contribution_status CHECK
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("status", ["pending", "submitted", "accepted", "rejected"])
def test_contribution_status_valid(engine_007, status):
    """contribution_status accepts all values in the allowed set."""
    food_id = _make_food(engine_007)
    ov_id = str(uuid.uuid4())
    _exec(
        engine_007,
        "INSERT INTO user_overrides"
        " (id, food_id, field, corrected_value, corrected_at, contribution_status)"
        " VALUES (:id, :fid, 'name', 'X', :ts, :s)",
        {"id": ov_id, "fid": food_id, "ts": _NOW, "s": status},
    )
    stored = _scalar(
        engine_007, "SELECT contribution_status FROM user_overrides WHERE id = :id", {"id": ov_id}
    )
    assert stored == status


def test_contribution_status_rejects_invalid(engine_007):
    """contribution_status rejects a value outside the allowed set."""
    food_id = _make_food(engine_007)
    with pytest.raises(IntegrityError):
        _exec(
            engine_007,
            "INSERT INTO user_overrides"
            " (id, food_id, field, corrected_value, corrected_at, contribution_status)"
            " VALUES (:id, :fid, 'name', 'X', :ts, 'idle')",
            {"id": str(uuid.uuid4()), "fid": food_id, "ts": _NOW},
        )


def test_contribution_status_null(engine_007):
    """contribution_status can be null (override not queued for contribution)."""
    food_id = _make_food(engine_007)
    ov_id = str(uuid.uuid4())
    _exec(
        engine_007,
        "INSERT INTO user_overrides"
        " (id, food_id, field, corrected_value, corrected_at, contribution_status)"
        " VALUES (:id, :fid, 'name', 'X', :ts, NULL)",
        {"id": ov_id, "fid": food_id, "ts": _NOW},
    )
    status = _scalar(
        engine_007, "SELECT contribution_status FROM user_overrides WHERE id = :id", {"id": ov_id}
    )
    assert status is None


# ---------------------------------------------------------------------------
# user_overrides: cascade delete
# ---------------------------------------------------------------------------

def test_cascade_delete_food_removes_overrides(engine_007):
    """Deleting a food cascades to its user_overrides rows."""
    food_id = _make_food(engine_007)
    _exec(
        engine_007,
        "INSERT INTO user_overrides (id, food_id, field, corrected_value, corrected_at)"
        " VALUES (:id, :fid, 'name', 'X', :ts)",
        {"id": str(uuid.uuid4()), "fid": food_id, "ts": _NOW},
    )
    _exec(engine_007, "DELETE FROM foods WHERE id = :id", {"id": food_id})
    count = _scalar(
        engine_007, "SELECT COUNT(*) FROM user_overrides WHERE food_id = :id", {"id": food_id}
    )
    assert count == 0


# ---------------------------------------------------------------------------
# sync_log
# ---------------------------------------------------------------------------

def test_sync_log_insert(engine_007):
    """A sync_log row can be inserted referencing an existing food_source_id."""
    src_id = _food_source_id(engine_007)
    log_id = str(uuid.uuid4())
    _exec(
        engine_007,
        "INSERT INTO sync_log (id, food_source_id, completed_at, record_count, duration_seconds, file_hash)"
        " VALUES (:id, :sid, :ts, 1000, 5.5, 'sha256:abc123')",
        {"id": log_id, "sid": src_id, "ts": _NOW},
    )
    count = _scalar(engine_007, "SELECT record_count FROM sync_log WHERE id = :id", {"id": log_id})
    assert count == 1000


def test_sync_log_unknown_source_rejected(engine_007):
    """Inserting a sync_log row with an unknown food_source_id is rejected by the FK constraint."""
    with pytest.raises(IntegrityError):
        _exec(
            engine_007,
            "INSERT INTO sync_log (id, food_source_id, completed_at, record_count, duration_seconds)"
            " VALUES (:id, :sid, :ts, 100, 1.0)",
            {"id": str(uuid.uuid4()), "sid": str(uuid.uuid4()), "ts": _NOW},
        )


def test_sync_log_file_hash_nullable(engine_007):
    """file_hash can be null for sources that do not use file-based delivery."""
    src_id = _food_source_id(engine_007, key="custom")
    log_id = str(uuid.uuid4())
    _exec(
        engine_007,
        "INSERT INTO sync_log (id, food_source_id, completed_at, record_count, duration_seconds, file_hash)"
        " VALUES (:id, :sid, :ts, 0, 0.1, NULL)",
        {"id": log_id, "sid": src_id, "ts": _NOW},
    )
    fh = _scalar(engine_007, "SELECT file_hash FROM sync_log WHERE id = :id", {"id": log_id})
    assert fh is None
