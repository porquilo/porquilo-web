"""Tests for migration 009: Add source_fetched_at and source_completeness to foods."""

import os
import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.exc import DBAPIError, IntegrityError

_NOW = datetime(2026, 6, 5, 12, 0, 0, tzinfo=timezone.utc)


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


def _new_food(engine, *, name="Test Food", source_fetched_at=None, source_completeness=None):
    food_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO foods"
        " (id, name, food_source_id, default_unit, created_at, updated_at,"
        "  source_fetched_at, source_completeness)"
        " SELECT :id, :name, id, 'g', :ts, :ts, :sfa, :sc"
        " FROM food_sources WHERE key = 'custom'",
        {
            "id": food_id,
            "name": name,
            "ts": _NOW,
            "sfa": source_fetched_at,
            "sc": source_completeness,
        },
    )
    return food_id


def _column_names(engine, table):
    return {col["name"] for col in inspect(engine).get_columns(table)}


# ---------------------------------------------------------------------------
# Schema inspection
# ---------------------------------------------------------------------------

def test_source_fetched_at_column_exists(engine_009):
    assert "source_fetched_at" in _column_names(engine_009, "foods")


def test_source_completeness_column_exists(engine_009):
    assert "source_completeness" in _column_names(engine_009, "foods")


# ---------------------------------------------------------------------------
# source_fetched_at: nullable and valid datetime
# ---------------------------------------------------------------------------

def test_source_fetched_at_accepts_null(engine_009):
    food_id = _new_food(engine_009, source_fetched_at=None)
    val = _scalar(
        engine_009,
        "SELECT source_fetched_at FROM foods WHERE id = :id",
        {"id": food_id},
    )
    assert val is None


def test_source_fetched_at_accepts_datetime(engine_009):
    ts = datetime(2026, 6, 5, 12, 0, 0, tzinfo=timezone.utc)
    food_id = _new_food(engine_009, source_fetched_at=ts)
    val = _scalar(
        engine_009,
        "SELECT source_fetched_at FROM foods WHERE id = :id",
        {"id": food_id},
    )
    assert val is not None


# ---------------------------------------------------------------------------
# source_completeness: nullable and boundary values
# ---------------------------------------------------------------------------

def test_source_completeness_accepts_null(engine_009):
    food_id = _new_food(engine_009, source_completeness=None)
    val = _scalar(
        engine_009,
        "SELECT source_completeness FROM foods WHERE id = :id",
        {"id": food_id},
    )
    assert val is None


def test_source_completeness_accepts_zero(engine_009):
    food_id = _new_food(engine_009, name="Zero", source_completeness=0.0)
    val = _scalar(
        engine_009,
        "SELECT source_completeness FROM foods WHERE id = :id",
        {"id": food_id},
    )
    assert val == pytest.approx(0.0)


def test_source_completeness_accepts_one(engine_009):
    food_id = _new_food(engine_009, name="Full", source_completeness=1.0)
    val = _scalar(
        engine_009,
        "SELECT source_completeness FROM foods WHERE id = :id",
        {"id": food_id},
    )
    assert val == pytest.approx(1.0)


def test_source_completeness_accepts_midpoint(engine_009):
    food_id = _new_food(engine_009, name="Half", source_completeness=0.5)
    val = _scalar(
        engine_009,
        "SELECT source_completeness FROM foods WHERE id = :id",
        {"id": food_id},
    )
    assert val == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# CHECK constraint violations
# ---------------------------------------------------------------------------

def test_source_completeness_rejects_negative(engine_009):
    with pytest.raises((IntegrityError, DBAPIError)):
        _new_food(engine_009, name="Negative", source_completeness=-0.01)


def test_source_completeness_rejects_above_one(engine_009):
    with pytest.raises((IntegrityError, DBAPIError)):
        _new_food(engine_009, name="TooHigh", source_completeness=1.01)


# ---------------------------------------------------------------------------
# Downgrade: columns removed
# ---------------------------------------------------------------------------

@pytest.fixture(params=["sqlite", "pg"])
def engine_009_then_downgrade(request, tmp_path):
    if request.param == "sqlite":
        db_file = tmp_path / "downgrade.db"
        url = f"sqlite:///{db_file}"
        cfg = _alembic_cfg(url)
        command.upgrade(cfg, "009")
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
                command.upgrade(cfg, "009")
                eng = sa.create_engine(url)
                yield eng, cfg
                eng.dispose()
        except Exception as exc:
            pytest.skip(f"Docker unavailable: {exc}")


def test_downgrade_drops_source_fetched_at(engine_009_then_downgrade):
    eng, cfg = engine_009_then_downgrade
    command.downgrade(cfg, "008")
    eng2 = sa.create_engine(eng.url)
    try:
        assert "source_fetched_at" not in _column_names(eng2, "foods")
    finally:
        eng2.dispose()


def test_downgrade_drops_source_completeness(engine_009_then_downgrade):
    eng, cfg = engine_009_then_downgrade
    command.downgrade(cfg, "008")
    eng2 = sa.create_engine(eng.url)
    try:
        assert "source_completeness" not in _column_names(eng2, "foods")
    finally:
        eng2.dispose()


# ---------------------------------------------------------------------------
# Food SQLModel reflects both new fields
# ---------------------------------------------------------------------------

def test_food_model_has_source_fetched_at_field(engine_009):
    from porquilo.models.food import Food
    assert hasattr(Food, "source_fetched_at")


def test_food_model_has_source_completeness_field(engine_009):
    from porquilo.models.food import Food
    assert hasattr(Food, "source_completeness")
