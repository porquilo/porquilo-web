"""Tests for migration 006: Indexes only."""

import os
import re

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

# ---------------------------------------------------------------------------
# Expected indexes introduced by 006
# ---------------------------------------------------------------------------

EXPECTED_INDEXES: dict[str, list[str]] = {
    "log_entries": [
        "ix_log_entries_eaten_at",
        "ix_log_entries_logged_at",
        "ix_log_entries_meal_id",
    ],
    "log_entry_nutrients": [
        "ix_log_entry_nutrients_log_entry_id",
    ],
    "food_nutrients": [
        "ix_food_nutrients_food_id",
    ],
    "foods": [
        "ix_foods_barcode",
        "ix_foods_source_external",
    ],
    "recipes": [
        "ix_recipes_source_source_id",
    ],
    "meal_skips": [
        "ix_meal_skips_meal_date",
    ],
    "body_metrics": [
        "ix_body_metrics_type_measured_at",
    ],
    "goals": [
        "ix_goals_effective_from",
    ],
    "recipe_ingredients": [
        "ix_recipe_ingredients_recipe_id",
        "ix_recipe_ingredients_ingredient_id",
    ],
}

# All index names from EXPECTED_INDEXES, flat
ALL_INDEX_NAMES: set[str] = {
    name for names in EXPECTED_INDEXES.values() for name in names
}

# Partial indexes and a keyword that must appear in their definition SQL
PARTIAL_INDEXES: dict[str, str] = {
    "ix_foods_barcode": "barcode IS NOT NULL",
    "ix_foods_source_external": "external_source_id IS NOT NULL",
    "ix_recipes_source_source_id": "source_id IS NOT NULL",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _alembic_cfg(url: str) -> Config:
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.attributes["configure_logger"] = False
    return cfg


def _index_names_for_table(engine: sa.Engine, table: str) -> set[str]:
    insp = inspect(engine)
    return {idx["name"] for idx in insp.get_indexes(table)}


def _index_def_sql(engine: sa.Engine, index_name: str) -> str:
    """Return the CREATE INDEX SQL for *index_name* from the DB catalog."""
    dialect = engine.dialect.name
    with engine.connect() as conn:
        if dialect == "sqlite":
            row = conn.execute(
                sa.text(
                    "SELECT sql FROM sqlite_master"
                    " WHERE type = 'index' AND name = :name"
                ),
                {"name": index_name},
            ).fetchone()
        else:
            row = conn.execute(
                sa.text(
                    "SELECT indexdef FROM pg_indexes WHERE indexname = :name"
                ),
                {"name": index_name},
            ).fetchone()
    assert row is not None, f"Index {index_name!r} not found in catalog"
    return row[0]


# ---------------------------------------------------------------------------
# Test: all indexes exist after 006
# ---------------------------------------------------------------------------

def test_all_indexes_present(engine_006):
    for table, names in EXPECTED_INDEXES.items():
        found = _index_names_for_table(engine_006, table)
        for name in names:
            assert name in found, (
                f"Expected index {name!r} on table {table!r} was not found. "
                f"Found: {sorted(found)}"
            )


# ---------------------------------------------------------------------------
# Test: none of the 006 indexes existed in 005 (single-migration audit)
# ---------------------------------------------------------------------------

@pytest.fixture(params=["sqlite", "pg"])
def engine_005_only(request, tmp_path):
    """Engine upgraded only to 005 — used to audit that 006 adds all indexes."""
    if request.param == "sqlite":
        db_file = tmp_path / "audit.db"
        url = f"sqlite:///{db_file}"
        cfg = _alembic_cfg(url)
        command.upgrade(cfg, "005")
        eng = sa.create_engine(url)
        yield eng
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
                command.upgrade(cfg, "005")
                eng = sa.create_engine(url)
                yield eng
                eng.dispose()
        except Exception as exc:
            pytest.skip(f"Docker unavailable: {exc}")


def test_no_006_indexes_exist_before_006(engine_005_only):
    """All indexes named in 006 must be absent after only 001–005 run."""
    for table, names in EXPECTED_INDEXES.items():
        found = _index_names_for_table(engine_005_only, table)
        for name in names:
            assert name not in found, (
                f"Index {name!r} on {table!r} already existed before migration 006. "
                "Sessions 1–5 should not add any named indexes."
            )


# ---------------------------------------------------------------------------
# Test: partial indexes carry WHERE clause in their definition
# ---------------------------------------------------------------------------

def test_partial_indexes_have_where_clause(engine_006):
    for index_name, keyword in PARTIAL_INDEXES.items():
        sql = _index_def_sql(engine_006, index_name)
        # Case-insensitive check; both SQLite and PostgreSQL include "WHERE"
        assert re.search(r"\bWHERE\b", sql, re.IGNORECASE), (
            f"Index {index_name!r} SQL does not contain WHERE clause: {sql!r}"
        )
        assert keyword.upper() in sql.upper(), (
            f"Index {index_name!r} SQL missing expected predicate {keyword!r}: {sql!r}"
        )


# ---------------------------------------------------------------------------
# Test: partial index column membership
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("table,index_name,expected_cols", [
    ("log_entries", "ix_log_entries_eaten_at", ["eaten_at"]),
    ("log_entries", "ix_log_entries_logged_at", ["logged_at"]),
    ("log_entries", "ix_log_entries_meal_id", ["meal_id"]),
    ("log_entry_nutrients", "ix_log_entry_nutrients_log_entry_id", ["log_entry_id"]),
    ("food_nutrients", "ix_food_nutrients_food_id", ["food_id"]),
    ("foods", "ix_foods_barcode", ["barcode"]),
    ("foods", "ix_foods_source_external", ["food_source_id", "external_source_id"]),
    ("recipes", "ix_recipes_source_source_id", ["source", "source_id"]),
    ("meal_skips", "ix_meal_skips_meal_date", ["meal_id", "skipped_on"]),
    ("body_metrics", "ix_body_metrics_type_measured_at", ["metric_type", "measured_at"]),
    ("goals", "ix_goals_effective_from", ["effective_from"]),
    ("recipe_ingredients", "ix_recipe_ingredients_recipe_id", ["recipe_id"]),
    ("recipe_ingredients", "ix_recipe_ingredients_ingredient_id", ["ingredient_id"]),
])
def test_index_covers_correct_columns(engine_006, table, index_name, expected_cols):
    insp = inspect(engine_006)
    indexes = {idx["name"]: idx for idx in insp.get_indexes(table)}
    assert index_name in indexes, f"Index {index_name!r} not found on {table!r}"
    assert indexes[index_name]["column_names"] == expected_cols, (
        f"{index_name!r} columns mismatch: "
        f"expected {expected_cols}, got {indexes[index_name]['column_names']}"
    )


# ---------------------------------------------------------------------------
# Test: downgrade removes all 006 indexes
# ---------------------------------------------------------------------------

@pytest.fixture(params=["sqlite", "pg"])
def engine_006_then_downgrade(request, tmp_path):
    """Apply 006, yield the engine, then downgrade to 005 — caller verifies after."""
    if request.param == "sqlite":
        db_file = tmp_path / "downgrade.db"
        url = f"sqlite:///{db_file}"
        cfg = _alembic_cfg(url)
        command.upgrade(cfg, "006")
        eng = sa.create_engine(url)
        yield eng, cfg, url
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
                command.upgrade(cfg, "006")
                eng = sa.create_engine(url)
                yield eng, cfg, url
                eng.dispose()
        except Exception as exc:
            pytest.skip(f"Docker unavailable: {exc}")


def test_downgrade_removes_all_006_indexes(engine_006_then_downgrade):
    eng, cfg, url = engine_006_then_downgrade
    command.downgrade(cfg, "005")
    eng2 = sa.create_engine(url)
    try:
        for table, names in EXPECTED_INDEXES.items():
            found = _index_names_for_table(eng2, table)
            for name in names:
                assert name not in found, (
                    f"Index {name!r} on {table!r} survived downgrade to 005"
                )
    finally:
        eng2.dispose()
