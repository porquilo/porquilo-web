import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError, IntegrityError

_NOW = datetime(2026, 5, 28, 0, 0, 0, tzinfo=timezone.utc)


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


def _new_recipe(engine, *, name="Test Recipe", source="custom", source_id=None,
                total_yield_g=None, yield_estimated=False, servings=None,
                yield_description=None, notes=None):
    recipe_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO recipes"
        " (id, name, source, source_id, total_yield_g, yield_estimated, servings,"
        "  yield_description, notes, created_at, updated_at)"
        " VALUES (:id, :name, :source, :source_id, :total_yield_g, :yield_estimated,"
        "         :servings, :yield_description, :notes, :ts, :ts)",
        {
            "id": recipe_id, "name": name, "source": source, "source_id": source_id,
            "total_yield_g": total_yield_g, "yield_estimated": yield_estimated,
            "servings": servings, "yield_description": yield_description,
            "notes": notes, "ts": _NOW,
        },
    )
    return recipe_id


def _new_ingredient_food(engine, food_id):
    ing_id = str(uuid.uuid4())
    _exec(engine, "INSERT INTO ingredients (id, food_id) VALUES (:id, :fid)",
          {"id": ing_id, "fid": food_id})
    return ing_id


def _new_ingredient_recipe(engine, recipe_id):
    ing_id = str(uuid.uuid4())
    _exec(engine, "INSERT INTO ingredients (id, recipe_id) VALUES (:id, :rid)",
          {"id": ing_id, "rid": recipe_id})
    return ing_id


def _add_recipe_ingredient(engine, recipe_id, ingredient_id, weight_g=100):
    ri_id = str(uuid.uuid4())
    _exec(
        engine,
        "INSERT INTO recipe_ingredients (id, recipe_id, ingredient_id, weight_g)"
        " VALUES (:id, :rid, :iid, :w)",
        {"id": ri_id, "rid": recipe_id, "iid": ingredient_id, "w": weight_g},
    )
    return ri_id


# --- recipes table ---

def test_recipe_with_total_yield_g(engine_003):
    recipe_id = _new_recipe(engine_003, name="Soup", source="custom", total_yield_g=800)
    val = _scalar(engine_003, "SELECT total_yield_g FROM recipes WHERE id = :id", {"id": recipe_id})
    assert float(val) == 800.0


def test_recipe_with_null_total_yield_g(engine_003):
    recipe_id = _new_recipe(engine_003, name="Mealie Import", source="mealie", source_id="abc123")
    val = _scalar(engine_003, "SELECT total_yield_g FROM recipes WHERE id = :id", {"id": recipe_id})
    assert val is None


def test_yield_estimated_defaults_false(engine_003):
    recipe_id = _new_recipe(engine_003)
    val = _scalar(engine_003, "SELECT yield_estimated FROM recipes WHERE id = :id", {"id": recipe_id})
    assert val in (False, 0)


def test_recipe_servings_with_null_yield(engine_003):
    recipe_id = _new_recipe(engine_003, source="mealie", source_id="xyz", servings=4)
    servings = _scalar(engine_003, "SELECT servings FROM recipes WHERE id = :id", {"id": recipe_id})
    yield_g = _scalar(engine_003, "SELECT total_yield_g FROM recipes WHERE id = :id", {"id": recipe_id})
    assert float(servings) == 4.0
    assert yield_g is None


def test_recipe_yield_description(engine_003):
    recipe_id = _new_recipe(engine_003, yield_description="12 cookies")
    desc = _scalar(engine_003, "SELECT yield_description FROM recipes WHERE id = :id", {"id": recipe_id})
    assert desc == "12 cookies"


def test_recipe_mealie_source_with_source_id(engine_003):
    recipe_id = _new_recipe(engine_003, source="mealie", source_id="mealie-recipe-001")
    source = _scalar(engine_003, "SELECT source FROM recipes WHERE id = :id", {"id": recipe_id})
    sid = _scalar(engine_003, "SELECT source_id FROM recipes WHERE id = :id", {"id": recipe_id})
    assert source == "mealie"
    assert sid == "mealie-recipe-001"


def test_recipe_arbitrary_source_accepted(engine_003):
    recipe_id = _new_recipe(engine_003, source="paprika_app", source_id="p-001")
    source = _scalar(engine_003, "SELECT source FROM recipes WHERE id = :id", {"id": recipe_id})
    assert source == "paprika_app"


def test_recipe_source_source_id_unique(engine_003):
    _new_recipe(engine_003, name="Recipe A", source="mealie", source_id="dup-001")
    with pytest.raises(IntegrityError):
        _new_recipe(engine_003, name="Recipe B", source="mealie", source_id="dup-001")


def test_recipe_null_source_id_not_unique(engine_003):
    # Multiple rows with source_id=null for the same source should be allowed.
    _new_recipe(engine_003, name="Custom A", source="custom", source_id=None)
    _new_recipe(engine_003, name="Custom B", source="custom", source_id=None)
    count = _scalar(engine_003, "SELECT COUNT(*) FROM recipes WHERE source = 'custom'")
    assert count == 2


# --- food ingredient ---

def test_recipe_contains_food_ingredient(engine_003):
    recipe_id = _new_recipe(engine_003, name="Pasta")
    food_id = _new_food(engine_003, name="Pasta Dry")
    ing_id = _new_ingredient_food(engine_003, food_id)
    _add_recipe_ingredient(engine_003, recipe_id, ing_id, weight_g=200)

    count = _scalar(
        engine_003,
        "SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = :rid",
        {"rid": recipe_id},
    )
    assert count == 1


# --- nested recipe ingredient ---

def test_recipe_contains_recipe_ingredient(engine_003):
    sauce_id = _new_recipe(engine_003, name="Tomato Sauce")
    pasta_id = _new_recipe(engine_003, name="Pasta Dish")
    ing_id = _new_ingredient_recipe(engine_003, sauce_id)
    _add_recipe_ingredient(engine_003, pasta_id, ing_id, weight_g=150)

    count = _scalar(
        engine_003,
        "SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = :rid",
        {"rid": pasta_id},
    )
    assert count == 1


# --- self-reference ---

def test_self_reference_rejected(engine_003):
    recipe_id = _new_recipe(engine_003, name="Circular")
    ing_id = _new_ingredient_recipe(engine_003, recipe_id)
    with pytest.raises((IntegrityError, DBAPIError)):
        _add_recipe_ingredient(engine_003, recipe_id, ing_id)


# --- ingredients check constraint ---

def test_ingredient_rejects_both_fks(engine_003):
    food_id = _new_food(engine_003)
    recipe_id = _new_recipe(engine_003, name="Both FKs")
    with pytest.raises((IntegrityError, DBAPIError)):
        _exec(
            engine_003,
            "INSERT INTO ingredients (id, food_id, recipe_id) VALUES (:id, :fid, :rid)",
            {"id": str(uuid.uuid4()), "fid": food_id, "rid": recipe_id},
        )


def test_ingredient_rejects_neither_fk(engine_003):
    with pytest.raises((IntegrityError, DBAPIError)):
        _exec(
            engine_003,
            "INSERT INTO ingredients (id, food_id, recipe_id) VALUES (:id, NULL, NULL)",
            {"id": str(uuid.uuid4())},
        )


# --- cascade delete ---

def test_cascade_delete_recipe(engine_003):
    recipe_id = _new_recipe(engine_003, name="To Delete")
    food_id = _new_food(engine_003, name="Ingredient Food")
    ing_id = _new_ingredient_food(engine_003, food_id)
    _add_recipe_ingredient(engine_003, recipe_id, ing_id)

    _exec(engine_003, "DELETE FROM recipes WHERE id = :id", {"id": recipe_id})

    count = _scalar(
        engine_003,
        "SELECT COUNT(*) FROM recipe_ingredients WHERE recipe_id = :rid",
        {"rid": recipe_id},
    )
    assert count == 0
