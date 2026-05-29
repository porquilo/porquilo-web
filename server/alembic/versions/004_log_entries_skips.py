"""Log entries and meal skips

Revision ID: 004
Revises: 003
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "log_entries",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "ingredient_id",
            sa.Uuid(),
            sa.ForeignKey("ingredients.id"),
            nullable=False,
        ),
        sa.Column(
            "meal_id",
            sa.Uuid(),
            sa.ForeignKey("meals.id"),
            nullable=False,
        ),
        sa.Column("eaten_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("weight_g", sa.Numeric(), nullable=True),
        sa.Column("weight_source", sa.String(), nullable=False),
        sa.Column("weight_confidence", sa.String(), nullable=False),
        sa.Column("input_method", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "log_entry_nutrients",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "log_entry_id",
            sa.Uuid(),
            sa.ForeignKey("log_entries.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "nutrient_id",
            sa.Uuid(),
            sa.ForeignKey("nutrient_definitions.id"),
            nullable=False,
        ),
        sa.Column("value", sa.Numeric(), nullable=False),
        sa.Column("coverage", sa.String(), nullable=False),
        sa.UniqueConstraint(
            "log_entry_id", "nutrient_id",
            name="uq_log_entry_nutrients_entry_nutrient",
        ),
    )

    op.create_table(
        "meal_skips",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "meal_id",
            sa.Uuid(),
            sa.ForeignKey("meals.id"),
            nullable=False,
        ),
        sa.Column("skipped_on", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("meal_id", "skipped_on", name="uq_meal_skips_meal_date"),
    )


def downgrade() -> None:
    op.drop_table("meal_skips")
    op.drop_table("log_entry_nutrients")
    op.drop_table("log_entries")
