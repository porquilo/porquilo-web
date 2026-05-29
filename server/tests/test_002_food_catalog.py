import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

_NOW = datetime(2026, 5, 28, 0, 0, 0, tzinfo=timezone.utc)


def _exec(engine, sql, params=None):
    with engine.begin() as conn:
        conn.execute(sa.text(sql), params or {})


def _scalar(engine, sql, params=None):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params or {}).scalar()


def _rows(engine, sql, params=None):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params or {}).fetchall()


def _food_source_id(engine, key: str):
    return _scalar(engine, "SELECT id FROM food_sources WHERE key = :k", {"k": key})


def _new_food(engine, *, name="Test Food", source_key="usda", external_id=None, default_unit="g"):
    food_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO foods (id, name, food_source_id, external_source_id, default_unit, created_at, updated_at) "
        "SELECT :id, :name, id, :eid, :unit, :ts, :ts FROM food_sources WHERE key = :key",
        {"id": food_id, "name": name, "eid": external_id, "unit": default_unit, "ts": _NOW, "key": source_key},
    )
    return food_id


# --- seed checks ---

def test_food_sources_seeded(engine_002):
    rows = _rows(engine_002, "SELECT key FROM food_sources ORDER BY key")
    keys = [r[0] for r in rows]
    assert keys == ["custom", "open_food_facts", "usda"]


def test_food_sources_key_unique(engine_002):
    with pytest.raises(IntegrityError):
        _exec(
            engine_002,
            "INSERT INTO food_sources (id, key, display_name, is_active, created_at, updated_at) "
            "VALUES (:id, 'usda', 'Dup', true, :ts, :ts)",
            {"id": str(uuid.uuid4()), "ts": _NOW},
        )


# --- food insert ---

def test_food_with_usda_source(engine_002):
    food_id = _new_food(engine_002, source_key="usda", external_id="FDC001")
    unit = _scalar(engine_002, "SELECT default_unit FROM foods WHERE id = :id", {"id": food_id})
    assert unit == "g"


def test_liquid_food_ml(engine_002):
    food_id = _new_food(engine_002, name="Milk", source_key="custom", default_unit="ml")
    unit = _scalar(engine_002, "SELECT default_unit FROM foods WHERE id = :id", {"id": food_id})
    assert unit == "ml"


def test_food_variant_ml(engine_002):
    food_id = _new_food(engine_002, name="OJ", source_key="custom", default_unit="ml")
    variant_id = str(uuid.uuid4())
    _exec(
        engine_002,
        "INSERT INTO food_variants (id, food_id, name, amount, unit, created_at) "
        "VALUES (:id, :fid, '250 ml', 250, 'ml', :ts)",
        {"id": variant_id, "fid": food_id, "ts": _NOW},
    )
    unit = _scalar(engine_002, "SELECT unit FROM food_variants WHERE id = :id", {"id": variant_id})
    assert unit == "ml"


def test_food_unknown_source_rejected(engine_002):
    with pytest.raises(IntegrityError):
        _exec(
            engine_002,
            "INSERT INTO foods (id, name, food_source_id, default_unit, created_at, updated_at) "
            "VALUES (:id, 'Ghost', :src, 'g', :ts, :ts)",
            {"id": str(uuid.uuid4()), "src": str(uuid.uuid4()), "ts": _NOW},
        )


def test_new_food_source_enables_food(engine_002):
    src_id = str(uuid.uuid4())
    _exec(
        engine_002,
        "INSERT INTO food_sources (id, key, display_name, is_active, created_at, updated_at) "
        "VALUES (:id, 'cronometer', 'Cronometer', true, :ts, :ts)",
        {"id": src_id, "ts": _NOW},
    )
    food_id = str(uuid.uuid4())
    _exec(
        engine_002,
        "INSERT INTO foods (id, name, food_source_id, default_unit, created_at, updated_at) "
        "VALUES (:id, 'Apple', :src, 'g', :ts, :ts)",
        {"id": food_id, "src": src_id, "ts": _NOW},
    )
    name = _scalar(engine_002, "SELECT name FROM foods WHERE id = :id", {"id": food_id})
    assert name == "Apple"


def test_duplicate_source_external_id_rejected(engine_002):
    _new_food(engine_002, name="Food A", source_key="usda", external_id="FDC-DUP")
    with pytest.raises(IntegrityError):
        _new_food(engine_002, name="Food B", source_key="usda", external_id="FDC-DUP")


def test_cascade_delete_food(engine_002):
    food_id = _new_food(engine_002, name="Deletable", source_key="custom")

    nutrient_id = _scalar(engine_002, "SELECT id FROM nutrient_definitions WHERE key = 'protein_g'")
    fn_id = str(uuid.uuid4())
    _exec(
        engine_002,
        "INSERT INTO food_nutrients (id, food_id, nutrient_id, value_per_100) VALUES (:id, :fid, :nid, 10)",
        {"id": fn_id, "fid": food_id, "nid": str(nutrient_id)},
    )

    fv_id = str(uuid.uuid4())
    _exec(
        engine_002,
        "INSERT INTO food_variants (id, food_id, name, amount, unit, created_at) VALUES (:id, :fid, '100g', 100, 'g', :ts)",
        {"id": fv_id, "fid": food_id, "ts": _NOW},
    )

    _exec(engine_002, "DELETE FROM foods WHERE id = :id", {"id": food_id})

    assert _scalar(engine_002, "SELECT COUNT(*) FROM food_nutrients WHERE food_id = :id", {"id": food_id}) == 0
    assert _scalar(engine_002, "SELECT COUNT(*) FROM food_variants WHERE food_id = :id", {"id": food_id}) == 0


# --- sync_status ---

def test_sync_status_defaults_null(engine_002):
    status = _scalar(engine_002, "SELECT sync_status FROM food_sources WHERE key = 'custom'")
    assert status is None


def test_sync_status_valid_values(engine_002):
    for status in ("queued", "running", "succeeded", "failed"):
        _exec(
            engine_002,
            "UPDATE food_sources SET sync_status = :s WHERE key = 'usda'",
            {"s": status},
        )
        stored = _scalar(engine_002, "SELECT sync_status FROM food_sources WHERE key = 'usda'")
        assert stored == status


def test_sync_status_rejects_invalid(engine_002):
    with pytest.raises(IntegrityError):
        _exec(
            engine_002,
            "UPDATE food_sources SET sync_status = 'idle' WHERE key = 'usda'",
        )
