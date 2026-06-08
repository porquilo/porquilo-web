"""Add sync_pid, sync_progress, sync_total to food_sources for subprocess-based OFF import

Revision ID: 013
Revises: 012
Create Date: 2026-06-07
"""

from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("food_sources") as batch_op:
        batch_op.add_column(sa.Column("sync_pid", sa.Integer, nullable=True))
        batch_op.add_column(sa.Column("sync_progress", sa.Integer, nullable=True))
        batch_op.add_column(sa.Column("sync_total", sa.Integer, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("food_sources") as batch_op:
        batch_op.drop_column("sync_total")
        batch_op.drop_column("sync_progress")
        batch_op.drop_column("sync_pid")
