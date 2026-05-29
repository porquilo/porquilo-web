"""Indexes only

Revision ID: 006
Revises: 005
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None

_PARTIAL_WHERE_BARCODE = sa.text("barcode IS NOT NULL")
_PARTIAL_WHERE_EXTERNAL = sa.text("external_source_id IS NOT NULL")
_PARTIAL_WHERE_SOURCE_ID = sa.text("source_id IS NOT NULL")


def upgrade() -> None:
    # log_entries
    op.create_index("ix_log_entries_eaten_at", "log_entries", ["eaten_at"])
    op.create_index("ix_log_entries_logged_at", "log_entries", ["logged_at"])
    op.create_index("ix_log_entries_meal_id", "log_entries", ["meal_id"])

    # log_entry_nutrients
    op.create_index(
        "ix_log_entry_nutrients_log_entry_id",
        "log_entry_nutrients",
        ["log_entry_id"],
    )

    # food_nutrients
    op.create_index("ix_food_nutrients_food_id", "food_nutrients", ["food_id"])

    # foods — partial indexes (WHERE col IS NOT NULL)
    op.create_index(
        "ix_foods_barcode",
        "foods",
        ["barcode"],
        postgresql_where=_PARTIAL_WHERE_BARCODE,
        sqlite_where=_PARTIAL_WHERE_BARCODE,
    )
    op.create_index(
        "ix_foods_source_external",
        "foods",
        ["food_source_id", "external_source_id"],
        postgresql_where=_PARTIAL_WHERE_EXTERNAL,
        sqlite_where=_PARTIAL_WHERE_EXTERNAL,
    )

    # recipes — partial index (WHERE source_id IS NOT NULL)
    op.create_index(
        "ix_recipes_source_source_id",
        "recipes",
        ["source", "source_id"],
        postgresql_where=_PARTIAL_WHERE_SOURCE_ID,
        sqlite_where=_PARTIAL_WHERE_SOURCE_ID,
    )

    # meal_skips
    op.create_index("ix_meal_skips_meal_date", "meal_skips", ["meal_id", "skipped_on"])

    # body_metrics
    op.create_index(
        "ix_body_metrics_type_measured_at",
        "body_metrics",
        ["metric_type", "measured_at"],
    )

    # goals
    op.create_index("ix_goals_effective_from", "goals", ["effective_from"])

    # recipe_ingredients
    op.create_index(
        "ix_recipe_ingredients_recipe_id",
        "recipe_ingredients",
        ["recipe_id"],
    )
    op.create_index(
        "ix_recipe_ingredients_ingredient_id",
        "recipe_ingredients",
        ["ingredient_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_recipe_ingredients_ingredient_id", table_name="recipe_ingredients")
    op.drop_index("ix_recipe_ingredients_recipe_id", table_name="recipe_ingredients")
    op.drop_index("ix_goals_effective_from", table_name="goals")
    op.drop_index("ix_body_metrics_type_measured_at", table_name="body_metrics")
    op.drop_index("ix_meal_skips_meal_date", table_name="meal_skips")
    op.drop_index("ix_recipes_source_source_id", table_name="recipes")
    op.drop_index("ix_foods_source_external", table_name="foods")
    op.drop_index("ix_foods_barcode", table_name="foods")
    op.drop_index("ix_food_nutrients_food_id", table_name="food_nutrients")
    op.drop_index(
        "ix_log_entry_nutrients_log_entry_id", table_name="log_entry_nutrients"
    )
    op.drop_index("ix_log_entries_meal_id", table_name="log_entries")
    op.drop_index("ix_log_entries_logged_at", table_name="log_entries")
    op.drop_index("ix_log_entries_eaten_at", table_name="log_entries")
