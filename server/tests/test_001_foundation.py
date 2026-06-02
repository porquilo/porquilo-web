import uuid

import pytest
import sqlalchemy as sa
from sqlalchemy.exc import IntegrityError


def _count(engine_001, table: str) -> int:
    with engine_001.connect() as conn:
        return conn.execute(sa.text(f"SELECT COUNT(*) FROM {table}")).scalar()


def test_tables_seeded(engine_001):
    assert _count(engine_001, "nutrient_definitions") == 27
    assert _count(engine_001, "meals") == 4
    assert _count(engine_001, "tracked_nutrients") == 4


def test_meal_names(engine_001):
    with engine_001.connect() as conn:
        rows = conn.execute(
            sa.text("SELECT name, sort_order, is_default FROM meals ORDER BY sort_order")
        ).fetchall()
    names = [r[0] for r in rows]
    assert names == ["Breakfast", "Lunch", "Dinner", "Snack"]
    assert all(r[2] for r in rows), "all meals should have is_default = true"


def test_tracked_nutrients_flags(engine_001):
    with engine_001.connect() as conn:
        rows = conn.execute(
            sa.text(
                "SELECT nd.key, tn.show_in_diary, tn.show_in_goals, tn.show_in_charts "
                "FROM tracked_nutrients tn "
                "JOIN nutrient_definitions nd ON nd.id = tn.nutrient_id "
                "ORDER BY tn.display_order"
            )
        ).fetchall()
    keys = [r[0] for r in rows]
    assert keys == ["calories_kcal", "protein_g", "carbs_g", "fat_g"]
    for key, diary, goals, charts in rows:
        assert diary, f"{key}: show_in_diary should be true"
        assert goals, f"{key}: show_in_goals should be true"
        assert not charts, f"{key}: show_in_charts should be false"


def test_nutrient_key_unique(engine_001):
    with pytest.raises(IntegrityError):
        with engine_001.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO nutrient_definitions (id, key, display_name, unit, sort_order, created_at) "
                    "VALUES (:id, 'calories_kcal', 'Dup', 'kcal', 999, '2026-01-01')"
                ),
                {"id": str(uuid.uuid4())},
            )


def test_nutrient_sort_order_unique(engine_001):
    with pytest.raises(IntegrityError):
        with engine_001.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO nutrient_definitions (id, key, display_name, unit, sort_order, created_at) "
                    "VALUES (:id, 'unique_key_xyz', 'Dup', 'g', 1, '2026-01-01')"
                ),
                {"id": str(uuid.uuid4())},
            )


def test_tracked_nutrient_id_unique(engine_001):
    # Fetch the id of an already-tracked nutrient
    with engine_001.connect() as conn:
        nutrient_id = conn.execute(
            sa.text("SELECT nutrient_id FROM tracked_nutrients LIMIT 1")
        ).scalar()

    with pytest.raises(IntegrityError):
        with engine_001.begin() as conn:
            conn.execute(
                sa.text(
                    "INSERT INTO tracked_nutrients "
                    "(id, nutrient_id, display_order, show_in_diary, show_in_goals, show_in_charts, created_at) "
                    "VALUES (:id, :nid, 99, false, false, false, '2026-01-01')"
                ),
                {"id": str(uuid.uuid4()), "nid": str(nutrient_id)},
            )
