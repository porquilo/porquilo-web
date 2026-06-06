"""Tests for migration 011: Add display_name and display_name_status to foods (FD-S2).

Covers the VERIFICATION checklist items:
  - foods.display_name column exists and accepts null
  - foods.display_name_status column exists and accepts null and any string value
  - Food Pydantic response schema includes display_name (nullable)
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import inspect

_NOW = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _exec(engine, sql, params=None):
    with engine.begin() as conn:
        conn.execute(sa.text(sql), params or {})


def _scalar(engine, sql, params=None):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params or {}).scalar()


def _new_food(engine, *, name="Test Food", display_name=None, display_name_status=None):
    food_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO foods"
        " (id, name, food_source_id, default_unit, created_at, updated_at,"
        "  display_name, display_name_status)"
        " SELECT :id, :name, id, 'g', :ts, :ts, :dn, :dns"
        " FROM food_sources WHERE key = 'custom'",
        {
            "id": food_id,
            "name": name,
            "ts": _NOW,
            "dn": display_name,
            "dns": display_name_status,
        },
    )
    return food_id


def _column_names(engine, table):
    return {col["name"] for col in inspect(engine).get_columns(table)}


# ---------------------------------------------------------------------------
# Schema: column existence
# ---------------------------------------------------------------------------


def test_display_name_column_exists(engine_011):
    assert "display_name" in _column_names(engine_011, "foods")


def test_display_name_status_column_exists(engine_011):
    assert "display_name_status" in _column_names(engine_011, "foods")


# ---------------------------------------------------------------------------
# display_name: accepts null and non-null
# ---------------------------------------------------------------------------


def test_display_name_accepts_null(engine_011):
    food_id = _new_food(engine_011, display_name=None)
    val = _scalar(engine_011, "SELECT display_name FROM foods WHERE id = :id", {"id": food_id})
    assert val is None


def test_display_name_accepts_string(engine_011):
    food_id = _new_food(engine_011, name="Raw name", display_name="Normalized name")
    val = _scalar(engine_011, "SELECT display_name FROM foods WHERE id = :id", {"id": food_id})
    assert val == "Normalized name"


# ---------------------------------------------------------------------------
# display_name_status: accepts null and any open string value
# ---------------------------------------------------------------------------


def test_display_name_status_accepts_null(engine_011):
    food_id = _new_food(engine_011, display_name_status=None)
    val = _scalar(engine_011, "SELECT display_name_status FROM foods WHERE id = :id", {"id": food_id})
    assert val is None


def test_display_name_status_accepts_processing(engine_011):
    food_id = _new_food(engine_011, name="A", display_name_status="processing")
    val = _scalar(engine_011, "SELECT display_name_status FROM foods WHERE id = :id", {"id": food_id})
    assert val == "processing"


def test_display_name_status_accepts_done(engine_011):
    food_id = _new_food(engine_011, name="B", display_name_status="done")
    val = _scalar(engine_011, "SELECT display_name_status FROM foods WHERE id = :id", {"id": food_id})
    assert val == "done"


def test_display_name_status_accepts_failed(engine_011):
    food_id = _new_food(engine_011, name="C", display_name_status="failed")
    val = _scalar(engine_011, "SELECT display_name_status FROM foods WHERE id = :id", {"id": food_id})
    assert val == "failed"


def test_display_name_status_accepts_skipped(engine_011):
    food_id = _new_food(engine_011, name="D", display_name_status="skipped")
    val = _scalar(engine_011, "SELECT display_name_status FROM foods WHERE id = :id", {"id": food_id})
    assert val == "skipped"


def test_display_name_status_accepts_arbitrary_string(engine_011):
    food_id = _new_food(engine_011, name="E", display_name_status="custom_future_value")
    val = _scalar(engine_011, "SELECT display_name_status FROM foods WHERE id = :id", {"id": food_id})
    assert val == "custom_future_value"


# ---------------------------------------------------------------------------
# Pydantic response schema
# ---------------------------------------------------------------------------


def test_food_read_schema_includes_display_name():
    from porquilo.routers.foods import FoodRead
    assert "display_name" in FoodRead.model_fields
    field = FoodRead.model_fields["display_name"]
    # Field must be Optional (allow None)
    import typing
    args = typing.get_args(field.annotation)
    assert type(None) in args or field.annotation is type(None) or str(field.annotation).startswith("Optional")


def test_food_out_schema_includes_display_name():
    from porquilo.routers.foods import FoodOut
    assert "display_name" in FoodOut.model_fields
    field = FoodOut.model_fields["display_name"]
    import typing
    args = typing.get_args(field.annotation)
    assert type(None) in args or field.annotation is type(None) or str(field.annotation).startswith("Optional")


def test_food_model_has_display_name_field(engine_011):
    from porquilo.models.food import Food
    assert hasattr(Food, "display_name")


def test_food_model_has_display_name_status_field(engine_011):
    from porquilo.models.food import Food
    assert hasattr(Food, "display_name_status")
