"""Foundation tables: nutrient_definitions, meals, tracked_nutrients

Revision ID: 001
Revises:
Create Date: 2026-05-28
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

_NOW = datetime(2026, 5, 28, 0, 0, 0, tzinfo=timezone.utc)

# Hardcoded UUIDs keep the seed deterministic across fresh installs.
# Must be uuid.UUID objects — sa.Uuid processes them via .hex for SQLite storage.
def _u(s: str) -> uuid.UUID:
    return uuid.UUID(s)

_ND_IDS = [
    _u("2729e2b3-3bf3-4ebb-b70e-5139c9bd9245"),  # calories_kcal
    _u("0dc14194-ac87-40cb-8fbe-b3cd816417b1"),  # protein_g
    _u("5ebfd2db-88b0-4947-8000-5be8742b59a5"),  # carbs_g
    _u("d8c674a9-6373-41ac-a462-805f78c3debb"),  # fat_g
    _u("0faa0d05-f93f-44f9-a413-d28fcf925f2f"),  # fiber_g
    _u("47265d20-6bd2-4541-b25e-a5949b7c2167"),  # sugar_g
    _u("bef32fc6-605f-40e2-a69f-a1891747e657"),  # sodium_mg
    _u("0933a5db-2516-45d0-8282-10fed59447dc"),  # saturated_fat_g
    _u("2c6583e4-c0c7-471b-9034-2b36dc1b1e75"),  # cholesterol_mg
    _u("fb143857-6966-4174-8f6f-7a69f1e81c5f"),  # potassium_mg
    _u("c498ec89-fc52-45b7-be78-99c3a8b3cf49"),  # vitamin_a_mcg
    _u("ecaaadbf-3c97-474d-bce9-fb8f75c4943e"),  # vitamin_c_mg
    _u("b0b35dc0-8bed-4dfa-add5-64c082509017"),  # vitamin_d_mcg
    _u("8dc2c811-d81b-4746-9b2c-c5e1523ed21f"),  # vitamin_e_mg
    _u("b800db73-4838-45d5-9af7-e4c6f1ea6d17"),  # vitamin_k_mcg
    _u("abaa8eb8-d7d5-4175-8a4b-b3ac864ee594"),  # thiamin_mg
    _u("0e2d391a-bab6-44f4-834b-e64d22886dc9"),  # riboflavin_mg
    _u("b1f274f5-dd90-491c-b208-cffea9eaee67"),  # niacin_mg
    _u("40503dd4-8ac1-4f63-876e-9050b69fa932"),  # vitamin_b6_mg
    _u("ff12aa80-1150-4289-9de9-cf6ec69cd185"),  # folate_mcg
    _u("a0082078-ea4a-4349-964b-6ef290f872b3"),  # vitamin_b12_mcg
    _u("641ad02f-2d22-4486-9c90-eb49acd11e79"),  # calcium_mg
    _u("4379fd23-d026-474c-acf8-34eeb821b9f0"),  # iron_mg
    _u("ad4cee37-e445-4754-be9c-5e65e452b921"),  # magnesium_mg
    _u("83fc64d2-60d2-43e5-bf90-5613b1696f6b"),  # phosphorus_mg
    _u("41a59a17-0147-4297-86d0-fd92ae2c34ab"),  # zinc_mg
    _u("73e3bf70-38a9-41a7-8290-b78c95ec9325"),  # selenium_mcg
]


def upgrade() -> None:
    nutrient_definitions = op.create_table(
        "nutrient_definitions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("key", name="uq_nutrient_definitions_key"),
        sa.UniqueConstraint("sort_order", name="uq_nutrient_definitions_sort_order"),
    )

    meals = op.create_table(
        "meals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "tracked_nutrients",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "nutrient_id",
            sa.Uuid(),
            sa.ForeignKey("nutrient_definitions.id"),
            nullable=False,
        ),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("show_in_diary", sa.Boolean(), nullable=False),
        sa.Column("show_in_goals", sa.Boolean(), nullable=False),
        sa.Column("show_in_charts", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("nutrient_id", name="uq_tracked_nutrients_nutrient_id"),
    )

    # fmt: off
    op.bulk_insert(nutrient_definitions, [
        {"id": _ND_IDS[0],  "key": "calories_kcal",    "display_name": "Calories",          "unit": "kcal", "sort_order": 1,  "created_at": _NOW},
        {"id": _ND_IDS[1],  "key": "protein_g",        "display_name": "Protein",            "unit": "g",    "sort_order": 2,  "created_at": _NOW},
        {"id": _ND_IDS[2],  "key": "carbs_g",          "display_name": "Carbohydrates",      "unit": "g",    "sort_order": 3,  "created_at": _NOW},
        {"id": _ND_IDS[3],  "key": "fat_g",            "display_name": "Fat",                "unit": "g",    "sort_order": 4,  "created_at": _NOW},
        {"id": _ND_IDS[4],  "key": "fiber_g",          "display_name": "Fiber",              "unit": "g",    "sort_order": 5,  "created_at": _NOW},
        {"id": _ND_IDS[5],  "key": "sugar_g",          "display_name": "Sugar",              "unit": "g",    "sort_order": 6,  "created_at": _NOW},
        {"id": _ND_IDS[6],  "key": "sodium_mg",        "display_name": "Sodium",             "unit": "mg",   "sort_order": 7,  "created_at": _NOW},
        {"id": _ND_IDS[7],  "key": "saturated_fat_g",  "display_name": "Saturated Fat",      "unit": "g",    "sort_order": 8,  "created_at": _NOW},
        {"id": _ND_IDS[8],  "key": "cholesterol_mg",   "display_name": "Cholesterol",        "unit": "mg",   "sort_order": 9,  "created_at": _NOW},
        {"id": _ND_IDS[9],  "key": "potassium_mg",     "display_name": "Potassium",          "unit": "mg",   "sort_order": 10, "created_at": _NOW},
        {"id": _ND_IDS[10], "key": "vitamin_a_mcg",    "display_name": "Vitamin A",          "unit": "mcg",  "sort_order": 11, "created_at": _NOW},
        {"id": _ND_IDS[11], "key": "vitamin_c_mg",     "display_name": "Vitamin C",          "unit": "mg",   "sort_order": 12, "created_at": _NOW},
        {"id": _ND_IDS[12], "key": "vitamin_d_mcg",    "display_name": "Vitamin D",          "unit": "mcg",  "sort_order": 13, "created_at": _NOW},
        {"id": _ND_IDS[13], "key": "vitamin_e_mg",     "display_name": "Vitamin E",          "unit": "mg",   "sort_order": 14, "created_at": _NOW},
        {"id": _ND_IDS[14], "key": "vitamin_k_mcg",    "display_name": "Vitamin K",          "unit": "mcg",  "sort_order": 15, "created_at": _NOW},
        {"id": _ND_IDS[15], "key": "thiamin_mg",       "display_name": "Thiamin (B1)",       "unit": "mg",   "sort_order": 16, "created_at": _NOW},
        {"id": _ND_IDS[16], "key": "riboflavin_mg",    "display_name": "Riboflavin (B2)",    "unit": "mg",   "sort_order": 17, "created_at": _NOW},
        {"id": _ND_IDS[17], "key": "niacin_mg",        "display_name": "Niacin (B3)",        "unit": "mg",   "sort_order": 18, "created_at": _NOW},
        {"id": _ND_IDS[18], "key": "vitamin_b6_mg",    "display_name": "Vitamin B6",         "unit": "mg",   "sort_order": 19, "created_at": _NOW},
        {"id": _ND_IDS[19], "key": "folate_mcg",       "display_name": "Folate (B9)",        "unit": "mcg",  "sort_order": 20, "created_at": _NOW},
        {"id": _ND_IDS[20], "key": "vitamin_b12_mcg",  "display_name": "Vitamin B12",        "unit": "mcg",  "sort_order": 21, "created_at": _NOW},
        {"id": _ND_IDS[21], "key": "calcium_mg",       "display_name": "Calcium",            "unit": "mg",   "sort_order": 22, "created_at": _NOW},
        {"id": _ND_IDS[22], "key": "iron_mg",          "display_name": "Iron",               "unit": "mg",   "sort_order": 23, "created_at": _NOW},
        {"id": _ND_IDS[23], "key": "magnesium_mg",     "display_name": "Magnesium",          "unit": "mg",   "sort_order": 24, "created_at": _NOW},
        {"id": _ND_IDS[24], "key": "phosphorus_mg",    "display_name": "Phosphorus",         "unit": "mg",   "sort_order": 25, "created_at": _NOW},
        {"id": _ND_IDS[25], "key": "zinc_mg",          "display_name": "Zinc",               "unit": "mg",   "sort_order": 26, "created_at": _NOW},
        {"id": _ND_IDS[26], "key": "selenium_mcg",     "display_name": "Selenium",           "unit": "mcg",  "sort_order": 27, "created_at": _NOW},
    ])

    op.bulk_insert(meals, [
        {"id": _u("7c8c92bd-f6b5-4923-ae42-77d883a70da6"), "name": "Breakfast", "sort_order": 1, "is_default": True, "created_at": _NOW},
        {"id": _u("f3ed9baf-01b3-4564-9c2b-095acc2245e7"), "name": "Lunch",     "sort_order": 2, "is_default": True, "created_at": _NOW},
        {"id": _u("36e75e9e-297e-49cd-a4b3-bb6345fc91e0"), "name": "Dinner",    "sort_order": 3, "is_default": True, "created_at": _NOW},
        {"id": _u("bb075e7e-320a-45e4-a9d8-f28a3939d50a"), "name": "Snack",     "sort_order": 4, "is_default": True, "created_at": _NOW},
    ])
    # fmt: on

    # Resolve nutrient FK by key so UUIDs don't need to be repeated.
    # :tid must be a uuid.UUID so sa.Uuid can process it correctly on both dialects.
    tracked_seed = [
        (_u("7514ae82-7e39-41df-b9d4-0f2539abacad"), "calories_kcal", 1),
        (_u("2caa86c8-15a9-4020-aca4-e7c160fa2372"), "protein_g", 2),
        (_u("3f26e3f1-942e-4043-8396-37e849d3fbdd"), "carbs_g", 3),
        (_u("d906dede-bf67-4f46-81bd-54e53d7ff921"), "fat_g", 4),
    ]
    for tid, key, order in tracked_seed:
        op.execute(
            sa.text(
                "INSERT INTO tracked_nutrients "
                "(id, nutrient_id, display_order, show_in_diary, show_in_goals, show_in_charts, created_at) "
                "SELECT :tid, id, :order, 1, 1, 0, :ts "
                "FROM nutrient_definitions WHERE key = :key"
            ).bindparams(tid=str(tid), order=order, key=key, ts=_NOW)
        )


def downgrade() -> None:
    op.drop_table("tracked_nutrients")
    op.drop_table("meals")
    op.drop_table("nutrient_definitions")
