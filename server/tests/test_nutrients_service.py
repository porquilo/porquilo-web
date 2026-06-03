# Run against SQLite (default):
#   pytest server/tests/test_nutrients_service.py
#
# Run against PostgreSQL:
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost/porquilo_test \
#     pytest server/tests/test_nutrients_service.py

import uuid
from decimal import Decimal

import sqlalchemy as sa

from porquilo.models.food import Food
from porquilo.models.food_nutrient import FoodNutrient
from porquilo.services.nutrients import compute_nutrients, derive_confidence


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_food_source_id(session) -> uuid.UUID:
    row = session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'usda'")
    ).fetchone()
    return uuid.UUID(str(row[0]))


def _get_nutrient_id(session, key: str) -> uuid.UUID:
    """Return the UUID of a seeded nutrient_definition by key."""
    row = session.execute(
        sa.text("SELECT id FROM nutrient_definitions WHERE key = :key"), {"key": key}
    ).fetchone()
    return uuid.UUID(str(row[0]))


def _insert_food(session, *, food_source_id: uuid.UUID, name: str = "Test Food") -> Food:
    food = Food(name=name, food_source_id=food_source_id)
    session.add(food)
    session.flush()
    return food


def _insert_food_nutrient(
    session,
    *,
    food_id: uuid.UUID,
    nutrient_id: uuid.UUID,
    value_per_100: Decimal,
) -> FoodNutrient:
    fn = FoodNutrient(food_id=food_id, nutrient_id=nutrient_id, value_per_100=value_per_100)
    session.add(fn)
    session.flush()
    return fn


# ---------------------------------------------------------------------------
# compute_nutrients
# ---------------------------------------------------------------------------


def test_compute_nutrients_scales_values(db_session):
    source_id = _get_food_source_id(db_session)
    food = _insert_food(db_session, food_source_id=source_id)
    nutrient_id = _get_nutrient_id(db_session, "protein_g")
    _insert_food_nutrient(db_session, food_id=food.id, nutrient_id=nutrient_id, value_per_100=Decimal("20.0"))

    result = compute_nutrients(food.id, Decimal("250"), db_session)

    assert nutrient_id in result
    assert result[nutrient_id]["value"] == Decimal("50.0")  # 20 * 250 / 100
    assert result[nutrient_id]["coverage"] == "full"


def test_compute_nutrients_multiple_nutrients(db_session):
    source_id = _get_food_source_id(db_session)
    food = _insert_food(db_session, food_source_id=source_id, name="Multi Food")
    fat_id = _get_nutrient_id(db_session, "fat_g")
    carbs_id = _get_nutrient_id(db_session, "carbs_g")
    _insert_food_nutrient(db_session, food_id=food.id, nutrient_id=fat_id, value_per_100=Decimal("10.0"))
    _insert_food_nutrient(db_session, food_id=food.id, nutrient_id=carbs_id, value_per_100=Decimal("30.0"))

    result = compute_nutrients(food.id, Decimal("50"), db_session)

    assert len(result) == 2
    assert result[fat_id]["value"] == Decimal("5.0")    # 10 * 50 / 100
    assert result[carbs_id]["value"] == Decimal("15.0")  # 30 * 50 / 100


def test_compute_nutrients_accepts_uuid_food_id(db_session):
    source_id = _get_food_source_id(db_session)
    food = _insert_food(db_session, food_source_id=source_id, name="UUID Food")
    nutrient_id = _get_nutrient_id(db_session, "fiber_g")
    _insert_food_nutrient(db_session, food_id=food.id, nutrient_id=nutrient_id, value_per_100=Decimal("5.0"))

    food_uuid = food.id
    assert isinstance(food_uuid, uuid.UUID)

    result = compute_nutrients(food_uuid, Decimal("100"), db_session)
    assert nutrient_id in result


def test_compute_nutrients_unknown_food_returns_empty(db_session):
    unknown_id = uuid.uuid4()
    result = compute_nutrients(unknown_id, Decimal("100"), db_session)
    assert result == {}


def test_compute_nutrients_result_keys_are_uuids(db_session):
    source_id = _get_food_source_id(db_session)
    food = _insert_food(db_session, food_source_id=source_id, name="Key Type Food")
    nutrient_id = _get_nutrient_id(db_session, "sodium_mg")
    _insert_food_nutrient(db_session, food_id=food.id, nutrient_id=nutrient_id, value_per_100=Decimal("100.0"))

    result = compute_nutrients(food.id, Decimal("100"), db_session)

    for key in result:
        assert isinstance(key, uuid.UUID)


# ---------------------------------------------------------------------------
# derive_confidence
# ---------------------------------------------------------------------------


def test_derive_confidence_scale():
    assert derive_confidence("scale") == "measured"


def test_derive_confidence_recipe_derived():
    assert derive_confidence("recipe_derived") == "measured"


def test_derive_confidence_ai_estimated():
    assert derive_confidence("ai_estimated") == "estimated"


def test_derive_confidence_manual():
    assert derive_confidence("manual") == "estimated"


def test_derive_confidence_unknown():
    assert derive_confidence("barcode_scan") == "estimated"
    assert derive_confidence("") == "estimated"
    assert derive_confidence("anything_else") == "estimated"
