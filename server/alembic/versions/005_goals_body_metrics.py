"""Goals and body metrics

Revision ID: 005
Revises: 004
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("calorie_mode", sa.String(), nullable=False),
        sa.Column("calorie_target", sa.Numeric(), nullable=False),
        sa.Column("calorie_factor", sa.Numeric(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("effective_from", name="uq_goals_effective_from"),
    )

    op.create_table(
        "goal_nutrients",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "goal_id",
            sa.Uuid(),
            sa.ForeignKey("goals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "nutrient_id",
            sa.Uuid(),
            sa.ForeignKey("nutrient_definitions.id"),
            nullable=False,
        ),
        sa.Column("target_value", sa.Numeric(), nullable=True),
        sa.UniqueConstraint(
            "goal_id", "nutrient_id",
            name="uq_goal_nutrients_goal_nutrient",
        ),
    )

    op.create_table(
        "body_metrics",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("metric_type", sa.String(), nullable=False),
        sa.Column("value", sa.Numeric(), nullable=True),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("body_metrics")
    op.drop_table("goal_nutrients")
    op.drop_table("goals")
