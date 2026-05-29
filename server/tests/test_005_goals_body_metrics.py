import uuid
from datetime import date, datetime, timezone

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


def _first_nutrient_id(engine):
    return _scalar(engine, "SELECT id FROM nutrient_definitions ORDER BY sort_order LIMIT 1")


def _new_goal(engine, *, calorie_mode="fixed", calorie_target=2000, calorie_factor=None,
              effective_from=date(2026, 5, 1)):
    goal_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO goals (id, calorie_mode, calorie_target, calorie_factor, effective_from, created_at)"
        " VALUES (:id, :mode, :target, :factor, :from_, :ts)",
        {
            "id": goal_id,
            "mode": calorie_mode,
            "target": calorie_target,
            "factor": calorie_factor,
            "from_": effective_from,
            "ts": _NOW,
        },
    )
    return goal_id


def _new_goal_nutrient(engine, *, goal_id, nutrient_id, target_value=None):
    gn_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO goal_nutrients (id, goal_id, nutrient_id, target_value)"
        " VALUES (:id, :gid, :nid, :val)",
        {"id": gn_id, "gid": goal_id, "nid": nutrient_id, "val": target_value},
    )
    return gn_id


def _new_body_metric(engine, *, metric_type="weight_kg", value=80.5,
                     measured_at=_NOW, source="manual"):
    bm_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO body_metrics (id, metric_type, value, measured_at, source, created_at)"
        " VALUES (:id, :mt, :val, :meas, :src, :ts)",
        {
            "id": bm_id,
            "mt": metric_type,
            "val": value,
            "meas": measured_at,
            "src": source,
            "ts": _NOW,
        },
    )
    return bm_id


# --- goals versioning ---

def test_two_goals_coexist(engine_005):
    """Inserting a second goal does not modify or delete the first."""
    id1 = _new_goal(engine_005, effective_from=date(2026, 1, 1), calorie_target=1800)
    id2 = _new_goal(engine_005, effective_from=date(2026, 5, 1), calorie_target=2000)

    count = _scalar(engine_005, "SELECT COUNT(*) FROM goals")
    assert count == 2

    t1 = _scalar(engine_005, "SELECT calorie_target FROM goals WHERE id = :id", {"id": id1})
    t2 = _scalar(engine_005, "SELECT calorie_target FROM goals WHERE id = :id", {"id": id2})
    assert float(t1) == 1800
    assert float(t2) == 2000


def test_duplicate_effective_from_rejected(engine_005):
    _new_goal(engine_005, effective_from=date(2026, 3, 1))
    with pytest.raises(IntegrityError):
        _new_goal(engine_005, effective_from=date(2026, 3, 1))


# --- calorie_factor / calorie_mode ---

def test_calorie_factor_null_when_mode_fixed(engine_005):
    """calorie_factor must be null for mode='fixed'; app layer enforces this."""
    goal_id = _new_goal(engine_005, calorie_mode="fixed", calorie_factor=None)
    factor = _scalar(engine_005, "SELECT calorie_factor FROM goals WHERE id = :id", {"id": goal_id})
    assert factor is None


def test_calorie_factor_not_null_when_mode_exercise_adjusted(engine_005):
    goal_id = _new_goal(
        engine_005,
        calorie_mode="exercise_adjusted",
        calorie_factor=0.5,
        effective_from=date(2026, 6, 1),
    )
    factor = _scalar(engine_005, "SELECT calorie_factor FROM goals WHERE id = :id", {"id": goal_id})
    assert float(factor) == 0.5


def test_calorie_factor_non_null_with_mode_fixed_is_db_allowed(engine_005):
    """The DB does not enforce calorie_factor=NULL when mode='fixed' — this is app-layer only.
    This test documents that the DB will accept it without error."""
    goal_id = _new_goal(
        engine_005,
        calorie_mode="fixed",
        calorie_factor=0.8,
        effective_from=date(2026, 7, 1),
    )
    factor = _scalar(engine_005, "SELECT calorie_factor FROM goals WHERE id = :id", {"id": goal_id})
    # DB stores the value; application layer is responsible for rejecting this combination.
    assert float(factor) == 0.8


# --- goal_nutrients ---

def test_goal_nutrient_null_target_value(engine_005):
    goal_id = _new_goal(engine_005)
    nutrient_id = _first_nutrient_id(engine_005)
    gn_id = _new_goal_nutrient(engine_005, goal_id=goal_id, nutrient_id=nutrient_id, target_value=None)

    val = _scalar(
        engine_005,
        "SELECT target_value FROM goal_nutrients WHERE id = :id",
        {"id": gn_id},
    )
    assert val is None


def test_goal_nutrient_explicit_target_value(engine_005):
    goal_id = _new_goal(engine_005)
    nutrient_id = _first_nutrient_id(engine_005)
    gn_id = _new_goal_nutrient(engine_005, goal_id=goal_id, nutrient_id=nutrient_id, target_value=150.0)

    val = _scalar(
        engine_005,
        "SELECT target_value FROM goal_nutrients WHERE id = :id",
        {"id": gn_id},
    )
    assert float(val) == 150.0


def test_duplicate_goal_nutrient_rejected(engine_005):
    goal_id = _new_goal(engine_005)
    nutrient_id = _first_nutrient_id(engine_005)
    _new_goal_nutrient(engine_005, goal_id=goal_id, nutrient_id=nutrient_id)
    with pytest.raises(IntegrityError):
        _new_goal_nutrient(engine_005, goal_id=goal_id, nutrient_id=nutrient_id)


def test_cascade_delete_goal_removes_goal_nutrients(engine_005):
    goal_id = _new_goal(engine_005)
    nutrient_id = _first_nutrient_id(engine_005)
    _new_goal_nutrient(engine_005, goal_id=goal_id, nutrient_id=nutrient_id)

    before = _scalar(
        engine_005,
        "SELECT COUNT(*) FROM goal_nutrients WHERE goal_id = :gid",
        {"gid": goal_id},
    )
    assert before == 1

    _exec(engine_005, "DELETE FROM goals WHERE id = :id", {"id": goal_id})

    after = _scalar(
        engine_005,
        "SELECT COUNT(*) FROM goal_nutrients WHERE goal_id = :gid",
        {"gid": goal_id},
    )
    assert after == 0


# --- body_metrics ---

def test_body_metric_inserted(engine_005):
    bm_id = _new_body_metric(engine_005, metric_type="weight_kg", value=75.0, source="manual")
    count = _scalar(engine_005, "SELECT COUNT(*) FROM body_metrics WHERE id = :id", {"id": bm_id})
    assert count == 1


def test_multiple_metric_types(engine_005):
    types = ["weight_kg", "body_fat_pct", "waist_cm", "chest_cm", "hips_cm"]
    for i, mt in enumerate(types):
        _new_body_metric(
            engine_005,
            metric_type=mt,
            value=float(60 + i),
            source="manual",
            measured_at=datetime(2026, 5, 28, i, 0, 0, tzinfo=timezone.utc),
        )

    count = _scalar(engine_005, "SELECT COUNT(*) FROM body_metrics")
    assert count == len(types)


def test_open_string_metric_type_and_source(engine_005):
    """metric_type and source accept arbitrary strings beyond the documented known values."""
    bm_id = _new_body_metric(
        engine_005,
        metric_type="grip_strength_kg",
        source="future_device_v2",
        value=42.0,
    )

    mt = _scalar(engine_005, "SELECT metric_type FROM body_metrics WHERE id = :id", {"id": bm_id})
    src = _scalar(engine_005, "SELECT source FROM body_metrics WHERE id = :id", {"id": bm_id})
    assert mt == "grip_strength_kg"
    assert src == "future_device_v2"


def test_body_metric_multiple_readings_same_type(engine_005):
    """Multiple readings of the same metric_type are all stored; no uniqueness constraint."""
    d1 = datetime(2026, 5, 26, 8, 0, 0, tzinfo=timezone.utc)
    d2 = datetime(2026, 5, 27, 8, 0, 0, tzinfo=timezone.utc)
    d3 = datetime(2026, 5, 28, 8, 0, 0, tzinfo=timezone.utc)

    for measured_at, value in [(d1, 80.0), (d2, 79.5), (d3, 79.1)]:
        _new_body_metric(engine_005, metric_type="weight_kg", value=value,
                         measured_at=measured_at, source="manual")

    count = _scalar(
        engine_005,
        "SELECT COUNT(*) FROM body_metrics WHERE metric_type = 'weight_kg'",
    )
    assert count == 3
