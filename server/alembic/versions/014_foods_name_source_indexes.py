"""Add ix_foods_name and ix_foods_food_source_id indexes

Revision ID: 014
Revises: 013
Create Date: 2026-06-08
"""

from alembic import op

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("foods") as batch_op:
        batch_op.create_index("ix_foods_name", ["name"])
        batch_op.create_index("ix_foods_food_source_id", ["food_source_id"])


def downgrade() -> None:
    with op.batch_alter_table("foods") as batch_op:
        batch_op.drop_index("ix_foods_food_source_id")
        batch_op.drop_index("ix_foods_name")
