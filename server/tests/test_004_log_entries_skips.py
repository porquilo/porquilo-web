import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError

_EATEN = datetime(2026, 5, 28, 18, 30, 0, tzinfo=timezone.utc)   # 6:30 pm — when food was eaten
_LOGGED = datetime(2026, 5, 28, 21, 0, 0, tzinfo=timezone.utc)   # 9:00 pm — when it was logged
_NOW = _LOGGED


def _exec(engine, sql, params=None):
    with engine.begin() as conn:
        conn.execute(sa.text(sql), params or {})


def _scalar(engine, sql, params=None):
    with engine.connect() as conn:
        return conn.execute(sa.text(sql), params or {}).scalar()


# --- seed helpers ---

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


def _ingredient_for_food(engine, food_id):
    ing_id = str(uuid.uuid4())
    _exec(engine, "INSERT INTO ingredients (id, food_id) VALUES (:id, :fid)",
          {"id": ing_id, "fid": food_id})
    return ing_id


def _ingredient_for_recipe(engine, recipe_id):
    ing_id = str(uuid.uuid4())
    _exec(engine, "INSERT INTO ingredients (id, recipe_id) VALUES (:id, :rid)",
          {"id": ing_id, "rid": recipe_id})
    return ing_id


def _first_meal_id(engine):
    return _scalar(engine, "SELECT id FROM meals ORDER BY sort_order LIMIT 1")


def _first_nutrient_id(engine):
    return _scalar(engine, "SELECT id FROM nutrient_definitions ORDER BY sort_order LIMIT 1")


def _new_log_entry(engine, *, ingredient_id, meal_id, eaten_at=_EATEN, logged_at=_LOGGED,
                   weight_g=150, weight_source="scale", weight_confidence="measured",
                   input_method="scale_session"):
    entry_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO log_entries"
        " (id, ingredient_id, meal_id, eaten_at, logged_at, weight_g,"
        "  weight_source, weight_confidence, input_method, created_at)"
        " VALUES (:id, :ing, :meal, :eaten, :logged, :wg, :ws, :wc, :im, :ts)",
        {
            "id": entry_id, "ing": ingredient_id, "meal": meal_id,
            "eaten": eaten_at, "logged": logged_at, "wg": weight_g,
            "ws": weight_source, "wc": weight_confidence, "im": input_method,
            "ts": _NOW,
        },
    )
    return entry_id


def _new_log_entry_nutrient(engine, *, log_entry_id, nutrient_id, value=10.5, coverage="measured"):
    nut_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO log_entry_nutrients (id, log_entry_id, nutrient_id, value, coverage)"
        " VALUES (:id, :le, :nd, :val, :cov)",
        {"id": nut_id, "le": log_entry_id, "nd": nutrient_id, "val": value, "cov": coverage},
    )
    return nut_id


# --- log_entries ---

def test_log_entry_inserted_directly(engine_004):
    food_id = _new_food(engine_004)
    ing_id = _ingredient_for_food(engine_004, food_id)
    meal_id = _first_meal_id(engine_004)
    entry_id = _new_log_entry(engine_004, ingredient_id=ing_id, meal_id=meal_id)
    count = _scalar(engine_004, "SELECT COUNT(*) FROM log_entries WHERE id = :id", {"id": entry_id})
    assert count == 1


def test_eaten_at_and_logged_at_are_distinct_columns(engine_004):
    food_id = _new_food(engine_004)
    ing_id = _ingredient_for_food(engine_004, food_id)
    meal_id = _first_meal_id(engine_004)
    entry_id = _new_log_entry(engine_004, ingredient_id=ing_id, meal_id=meal_id,
                              eaten_at=_EATEN, logged_at=_LOGGED)

    with engine_004.connect() as conn:
        row = conn.execute(
            sa.text("SELECT eaten_at, logged_at FROM log_entries WHERE id = :id"),
            {"id": entry_id},
        ).one()

    # Both columns exist and hold different values.
    assert row.eaten_at is not None
    assert row.logged_at is not None
    # They differ by at least the 2.5 hour gap we inserted.
    assert row.eaten_at != row.logged_at


def test_cascade_delete_log_entry_removes_nutrients(engine_004):
    food_id = _new_food(engine_004)
    ing_id = _ingredient_for_food(engine_004, food_id)
    meal_id = _first_meal_id(engine_004)
    entry_id = _new_log_entry(engine_004, ingredient_id=ing_id, meal_id=meal_id)
    nutrient_id = _first_nutrient_id(engine_004)
    _new_log_entry_nutrient(engine_004, log_entry_id=entry_id, nutrient_id=nutrient_id)

    before = _scalar(engine_004,
                     "SELECT COUNT(*) FROM log_entry_nutrients WHERE log_entry_id = :id",
                     {"id": entry_id})
    assert before == 1

    _exec(engine_004, "DELETE FROM log_entries WHERE id = :id", {"id": entry_id})

    after = _scalar(engine_004,
                    "SELECT COUNT(*) FROM log_entry_nutrients WHERE log_entry_id = :id",
                    {"id": entry_id})
    assert after == 0


def test_log_entry_with_snapshotted_nutrients(engine_004):
    food_id = _new_food(engine_004)
    ing_id = _ingredient_for_food(engine_004, food_id)
    meal_id = _first_meal_id(engine_004)
    entry_id = _new_log_entry(engine_004, ingredient_id=ing_id, meal_id=meal_id, weight_g=200)
    nutrient_id = _first_nutrient_id(engine_004)

    _new_log_entry_nutrient(engine_004, log_entry_id=entry_id, nutrient_id=nutrient_id,
                            value=42.0, coverage="measured")

    val = _scalar(engine_004,
                  "SELECT value FROM log_entry_nutrients"
                  " WHERE log_entry_id = :le AND nutrient_id = :nd",
                  {"le": entry_id, "nd": nutrient_id})
    assert float(val) == 42.0


def test_nested_recipe_snapshotted_nutrition_accepted(engine_004):
    """
    Recipe B contains recipe A as a sub-recipe. Application pre-computes resolved
    nutrition for the weight consumed and inserts it into log_entry_nutrients.
    This test confirms the schema accepts the snapshotted row.

    Composition (all weights in grams):
      Recipe A: 100g total yield
        - food X: 60g  → calories 120 kcal (2 kcal/g)
        - food Y: 40g  → calories  80 kcal (2 kcal/g)
        Total: 200 kcal / 100g = 2 kcal/g

      Recipe B: 200g total yield, uses 100g of recipe A
        Contribution from A portion: 100g × 2 kcal/g = 200 kcal
        Serving logged: 50g of recipe B
        Resolved calories: 50 / 200 × 200 = 50 kcal
    """
    recipe_a_id = _new_recipe(engine_004, name="Sub-recipe A")
    recipe_b_id = _new_recipe(engine_004, name="Parent Recipe B")

    # Wire A as an ingredient of B.
    ing_a_id = _ingredient_for_recipe(engine_004, recipe_a_id)
    ri_id = str(uuid.uuid4())
    _exec(
        engine_004,
        "INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, weight_g)"
        " VALUES (:id, :rid, :iid, 100)",
        {"id": ri_id, "rid": recipe_b_id, "iid": ing_a_id},
    )

    # Log a 50g portion of recipe B.
    ing_b_id = _ingredient_for_recipe(engine_004, recipe_b_id)
    meal_id = _first_meal_id(engine_004)
    entry_id = _new_log_entry(engine_004, ingredient_id=ing_b_id, meal_id=meal_id, weight_g=50)

    # Application resolves: 50 kcal. Snapshot into log_entry_nutrients.
    nutrient_id = _first_nutrient_id(engine_004)
    _new_log_entry_nutrient(engine_004, log_entry_id=entry_id, nutrient_id=nutrient_id,
                            value=50.0, coverage="estimated")

    val = _scalar(engine_004,
                  "SELECT value FROM log_entry_nutrients"
                  " WHERE log_entry_id = :le AND nutrient_id = :nd",
                  {"le": entry_id, "nd": nutrient_id})
    assert float(val) == 50.0


# --- log_entry_nutrients unique constraint ---

def test_duplicate_log_entry_nutrient_rejected(engine_004):
    food_id = _new_food(engine_004)
    ing_id = _ingredient_for_food(engine_004, food_id)
    meal_id = _first_meal_id(engine_004)
    entry_id = _new_log_entry(engine_004, ingredient_id=ing_id, meal_id=meal_id)
    nutrient_id = _first_nutrient_id(engine_004)

    _new_log_entry_nutrient(engine_004, log_entry_id=entry_id, nutrient_id=nutrient_id)
    with pytest.raises(IntegrityError):
        _new_log_entry_nutrient(engine_004, log_entry_id=entry_id, nutrient_id=nutrient_id)


# --- meal_skips ---

def test_meal_skip_recorded(engine_004):
    meal_id = _first_meal_id(engine_004)
    skip_id = str(uuid.uuid4())
    _exec(
        engine_004,
        "INSERT INTO meal_skips (id, meal_id, skipped_on, created_at)"
        " VALUES (:id, :mid, :d, :ts)",
        {"id": skip_id, "mid": meal_id, "d": date(2026, 5, 28), "ts": _NOW},
    )
    count = _scalar(engine_004, "SELECT COUNT(*) FROM meal_skips WHERE id = :id", {"id": skip_id})
    assert count == 1


def test_duplicate_meal_skip_rejected(engine_004):
    meal_id = _first_meal_id(engine_004)
    skip_date = date(2026, 5, 27)

    _exec(
        engine_004,
        "INSERT INTO meal_skips (id, meal_id, skipped_on, created_at)"
        " VALUES (:id, :mid, :d, :ts)",
        {"id": str(uuid.uuid4()), "mid": meal_id, "d": skip_date, "ts": _NOW},
    )
    with pytest.raises(IntegrityError):
        _exec(
            engine_004,
            "INSERT INTO meal_skips (id, meal_id, skipped_on, created_at)"
            " VALUES (:id, :mid, :d, :ts)",
            {"id": str(uuid.uuid4()), "mid": meal_id, "d": skip_date, "ts": _NOW},
        )


def test_meal_skip_hard_deleted(engine_004):
    meal_id = _first_meal_id(engine_004)
    skip_id = str(uuid.uuid4())
    _exec(
        engine_004,
        "INSERT INTO meal_skips (id, meal_id, skipped_on, created_at)"
        " VALUES (:id, :mid, :d, :ts)",
        {"id": skip_id, "mid": meal_id, "d": date(2026, 5, 26), "ts": _NOW},
    )

    _exec(engine_004, "DELETE FROM meal_skips WHERE id = :id", {"id": skip_id})

    count = _scalar(engine_004, "SELECT COUNT(*) FROM meal_skips WHERE id = :id", {"id": skip_id})
    assert count == 0

    # A skip for the same meal + date can be re-inserted after hard delete.
    _exec(
        engine_004,
        "INSERT INTO meal_skips (id, meal_id, skipped_on, created_at)"
        " VALUES (:id, :mid, :d, :ts)",
        {"id": str(uuid.uuid4()), "mid": meal_id, "d": date(2026, 5, 26), "ts": _NOW},
    )
    count_after = _scalar(engine_004,
                          "SELECT COUNT(*) FROM meal_skips WHERE meal_id = :mid",
                          {"mid": meal_id})
    assert count_after == 1


# --- open string fields ---

def test_open_string_fields_accept_arbitrary_values(engine_004):
    food_id = _new_food(engine_004)
    ing_id = _ingredient_for_food(engine_004, food_id)
    meal_id = _first_meal_id(engine_004)

    entry_id = _new_log_entry(
        engine_004,
        ingredient_id=ing_id,
        meal_id=meal_id,
        weight_source="future_source_v2",
        weight_confidence="calibrated",
        input_method="voice_dictation",
    )
    nutrient_id = _first_nutrient_id(engine_004)
    _new_log_entry_nutrient(engine_004, log_entry_id=entry_id, nutrient_id=nutrient_id,
                            coverage="partially_estimated")

    ws = _scalar(engine_004, "SELECT weight_source FROM log_entries WHERE id = :id", {"id": entry_id})
    wc = _scalar(engine_004, "SELECT weight_confidence FROM log_entries WHERE id = :id", {"id": entry_id})
    im = _scalar(engine_004, "SELECT input_method FROM log_entries WHERE id = :id", {"id": entry_id})
    cov = _scalar(engine_004,
                  "SELECT coverage FROM log_entry_nutrients WHERE log_entry_id = :id",
                  {"id": entry_id})

    assert ws == "future_source_v2"
    assert wc == "calibrated"
    assert im == "voice_dictation"
    assert cov == "partially_estimated"
