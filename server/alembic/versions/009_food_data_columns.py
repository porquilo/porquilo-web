"""Add source_fetched_at and source_completeness to foods

Revision ID: 009
Revises: 008
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("foods") as batch_op:
        batch_op.add_column(
            sa.Column("source_fetched_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column(
                "source_completeness",
                sa.Float,
                sa.CheckConstraint(
                    "source_completeness >= 0.0 AND source_completeness <= 1.0",
                    name="ck_foods_source_completeness",
                ),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("foods") as batch_op:
        batch_op.drop_constraint("ck_foods_source_completeness", type_="check")
        batch_op.drop_column("source_completeness")
        batch_op.drop_column("source_fetched_at")
