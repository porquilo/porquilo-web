"""Tests for migration 008: Remove ingredients table."""

import os
import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.exc import DBAPIError, IntegrityError

_NOW = datetime(2026, 6, 3, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _alembic_cfg(url: str) -> Config:
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.attributes["configure_logger"] = False
    return cfg


def _exec(engine, sql, params=None):
    with engine.begin() as conn:
        conn.execute(sa.text(sql), params or {})


def _scalar(engine, sql, params=None):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params or {}).scalar()


def _new_food(engine, *, name="Test Food"):
    food_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO foods (id, name, food_source_id, default_unit, created_at, updated_at)"
        " SELECT :id, :name, id, 'g', :ts, :ts FROM food_sources WHERE key = 'custom'",
        {"id": food_id, "name": name, "ts": _NOW},
    )
    return food_id


def _new_recipe(engine, *, name="Test Recipe"):
    recipe_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO recipes (id, name, source, created_at, updated_at)"
        " VALUES (:id, :name, 'custom', :ts, :ts)",
        {"id": recipe_id, "name": name, "ts": _NOW},
    )
    return recipe_id


def _new_meal(engine, *, name="Dinner"):
    meal_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO meals (id, name, sort_order, is_default, created_at)"
        " VALUES (:id, :name, 1, 0, :ts)",
        {"id": meal_id, "name": name, "ts": _NOW},
    )
    return meal_id


def _column_names(engine, table):
    return {col["name"] for col in inspect(engine).get_columns(table)}


def _index_names(engine, table):
    return {idx["name"] for idx in inspect(engine).get_indexes(table)}


# ---------------------------------------------------------------------------
# Schema structure
# ---------------------------------------------------------------------------

def test_ingredients_table_absent(engine_008):
    assert "ingredients" not in inspect(engine_008).get_table_names()


def test_log_entries_has_food_id_and_recipe_id(engine_008):
    cols = _column_names(engine_008, "log_entries")
    assert "food_id" in cols
    assert "recipe_id" in cols
    assert "ingredient_id" not in cols


def test_recipe_ingredients_has_food_id_and_nested_recipe_id(engine_008):
    cols = _column_names(engine_008, "recipe_ingredients")
    assert "food_id" in cols
    assert "nested_recipe_id" in cols
    assert "ingredient_id" not in cols


# ---------------------------------------------------------------------------
# CHECK constraints on log_entries
# ---------------------------------------------------------------------------

def _insert_log_entry(engine, *, food_id=None, recipe_id=None, meal_id):
    entry_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO log_entries"
        " (id, food_id, recipe_id, meal_id, eaten_at, logged_at,"
        "  weight_g, weight_source, weight_confidence, input_method)"
        " VALUES (:id, :fid, :rid, :mid, :ts, :ts, 100, 'scale', 'high', 'manual')",
        {"id": entry_id, "fid": food_id, "rid": recipe_id, "mid": meal_id, "ts": _NOW},
    )
    return entry_id


def test_log_entry_food_only_accepted(engine_008):
    food_id = _new_food(engine_008)
    meal_id = _new_meal(engine_008)
    entry_id = _insert_log_entry(engine_008, food_id=food_id, meal_id=meal_id)
    assert _scalar(engine_008, "SELECT COUNT(*) FROM log_entries WHERE id = :id", {"id": entry_id}) == 1


def test_log_entry_recipe_only_accepted(engine_008):
    recipe_id = _new_recipe(engine_008)
    meal_id = _new_meal(engine_008, name="Lunch")
    entry_id = _insert_log_entry(engine_008, recipe_id=recipe_id, meal_id=meal_id)
    assert _scalar(engine_008, "SELECT COUNT(*) FROM log_entries WHERE id = :id", {"id": entry_id}) == 1


def test_log_entry_both_set_rejected(engine_008):
    food_id = _new_food(engine_008, name="Bread")
    recipe_id = _new_recipe(engine_008, name="Soup")
    meal_id = _new_meal(engine_008, name="Breakfast")
    with pytest.raises((IntegrityError, DBAPIError)):
        _insert_log_entry(engine_008, food_id=food_id, recipe_id=recipe_id, meal_id=meal_id)


def test_log_entry_neither_set_rejected(engine_008):
    meal_id = _new_meal(engine_008, name="Snack")
    with pytest.raises((IntegrityError, DBAPIError)):
        _insert_log_entry(engine_008, food_id=None, recipe_id=None, meal_id=meal_id)


# ---------------------------------------------------------------------------
# CHECK constraints on recipe_ingredients
# ---------------------------------------------------------------------------

def _insert_recipe_ingredient(engine, *, recipe_id, food_id=None, nested_recipe_id=None, weight_g=100):
    ri_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO recipe_ingredients (id, recipe_id, food_id, nested_recipe_id, weight_g)"
        " VALUES (:id, :rid, :fid, :nrid, :w)",
        {"id": ri_id, "rid": recipe_id, "fid": food_id, "nrid": nested_recipe_id, "w": weight_g},
    )
    return ri_id


def test_recipe_ingredient_food_only_accepted(engine_008):
    recipe_id = _new_recipe(engine_008, name="Pasta")
    food_id = _new_food(engine_008, name="Pasta Dry")
    ri_id = _insert_recipe_ingredient(engine_008, recipe_id=recipe_id, food_id=food_id)
    assert _scalar(
        engine_008,
        "SELECT COUNT(*) FROM recipe_ingredients WHERE id = :id",
        {"id": ri_id},
    ) == 1


def test_recipe_ingredient_nested_recipe_accepted(engine_008):
    parent_id = _new_recipe(engine_008, name="Big Recipe")
    child_id = _new_recipe(engine_008, name="Sub Recipe")
    ri_id = _insert_recipe_ingredient(engine_008, recipe_id=parent_id, nested_recipe_id=child_id)
    assert _scalar(
        engine_008,
        "SELECT COUNT(*) FROM recipe_ingredients WHERE id = :id",
        {"id": ri_id},
    ) == 1


def test_recipe_ingredient_both_set_rejected(engine_008):
    recipe_id = _new_recipe(engine_008, name="Both")
    food_id = _new_food(engine_008, name="Oil")
    nested_id = _new_recipe(engine_008, name="Sauce")
    with pytest.raises((IntegrityError, DBAPIError)):
        _insert_recipe_ingredient(
            engine_008, recipe_id=recipe_id, food_id=food_id, nested_recipe_id=nested_id
        )


def test_recipe_ingredient_neither_set_rejected(engine_008):
    recipe_id = _new_recipe(engine_008, name="Neither")
    with pytest.raises((IntegrityError, DBAPIError)):
        _insert_recipe_ingredient(engine_008, recipe_id=recipe_id)


# ---------------------------------------------------------------------------
# Self-reference guard
# ---------------------------------------------------------------------------

def test_self_reference_rejected(engine_008):
    recipe_id = _new_recipe(engine_008, name="Circular")
    with pytest.raises((IntegrityError, DBAPIError)):
        _insert_recipe_ingredient(engine_008, recipe_id=recipe_id, nested_recipe_id=recipe_id)


# ---------------------------------------------------------------------------
# New indexes
# ---------------------------------------------------------------------------

def test_new_indexes_exist(engine_008):
    assert "ix_log_entries_food_id" in _index_names(engine_008, "log_entries")
    assert "ix_log_entries_recipe_id" in _index_names(engine_008, "log_entries")
    assert "ix_recipe_ingredients_food_id" in _index_names(engine_008, "recipe_ingredients")
    assert "ix_recipe_ingredients_nested_recipe_id" in _index_names(engine_008, "recipe_ingredients")


# ---------------------------------------------------------------------------
# SQLModel field count via inspect (verifies model matches migration)
# ---------------------------------------------------------------------------

def test_log_entries_column_count(engine_008):
    cols = inspect(engine_008).get_columns("log_entries")
    col_names = {c["name"] for c in cols}
    expected = {
        "id", "food_id", "recipe_id", "meal_id",
        "eaten_at", "logged_at", "weight_g", "weight_source",
        "weight_confidence", "input_method", "created_at",
    }
    assert col_names == expected, f"Column mismatch: got {col_names}"


def test_recipe_ingredients_column_count(engine_008):
    cols = inspect(engine_008).get_columns("recipe_ingredients")
    col_names = {c["name"] for c in cols}
    expected = {"id", "recipe_id", "food_id", "nested_recipe_id", "weight_g"}
    assert col_names == expected, f"Column mismatch: got {col_names}"


# ---------------------------------------------------------------------------
# Downgrade: schema reverts correctly
# ---------------------------------------------------------------------------

@pytest.fixture(params=["sqlite", "pg"])
def engine_008_then_downgrade(request, tmp_path):
    if request.param == "sqlite":
        db_file = tmp_path / "downgrade.db"
        url = f"sqlite:///{db_file}"
        cfg = _alembic_cfg(url)
        command.upgrade(cfg, "008")
        eng = sa.create_engine(url)

        @sa.event.listens_for(eng, "connect")
        def _fk(dbapi_conn, _rec):
            dbapi_conn.execute("PRAGMA foreign_keys = ON")

        yield eng, cfg
        eng.dispose()
    elif request.param == "pg":
        try:
            from testcontainers.postgres import PostgresContainer
        except ImportError:
            pytest.skip("testcontainers not installed")
        try:
            with PostgresContainer("postgres:16") as pg:
                url = pg.get_connection_url()
                cfg = _alembic_cfg(url)
                command.upgrade(cfg, "008")
                eng = sa.create_engine(url)
                yield eng, cfg
                eng.dispose()
        except Exception as exc:
            pytest.skip(f"Docker unavailable: {exc}")


def test_downgrade_restores_ingredients_table(engine_008_then_downgrade):
    eng, cfg = engine_008_then_downgrade
    command.downgrade(cfg, "007")
    eng2 = sa.create_engine(eng.url)
    try:
        tables = inspect(eng2).get_table_names()
        assert "ingredients" in tables
        # log_entries: ingredient_id back, food_id/recipe_id gone
        log_cols = _column_names(eng2, "log_entries")
        assert "ingredient_id" in log_cols
        assert "food_id" not in log_cols
        assert "recipe_id" not in log_cols
        # recipe_ingredients: ingredient_id back, new cols gone
        ri_cols = _column_names(eng2, "recipe_ingredients")
        assert "ingredient_id" in ri_cols
        assert "food_id" not in ri_cols
        assert "nested_recipe_id" not in ri_cols
        # New indexes gone
        assert "ix_log_entries_food_id" not in _index_names(eng2, "log_entries")
        assert "ix_log_entries_recipe_id" not in _index_names(eng2, "log_entries")
        assert "ix_recipe_ingredients_food_id" not in _index_names(eng2, "recipe_ingredients")
        assert "ix_recipe_ingredients_nested_recipe_id" not in _index_names(eng2, "recipe_ingredients")
        # ingredient_id index restored
        assert "ix_recipe_ingredients_ingredient_id" in _index_names(eng2, "recipe_ingredients")
    finally:
        eng2.dispose()
