"""Add display_name and display_name_status to foods

Revision ID: 011
Revises: 010
Create Date: 2026-06-06
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("foods") as batch_op:
        batch_op.add_column(
            sa.Column("display_name", sa.Text, nullable=True)
        )
        batch_op.add_column(
            sa.Column("display_name_status", sa.Text, nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("foods") as batch_op:
        batch_op.drop_column("display_name_status")
        batch_op.drop_column("display_name")
