"""pairing_codes table for QR-based mobile authentication

Revision ID: 017
Revises: 016
Create Date: 2026-06-22
"""

import sqlalchemy as sa
from alembic import op

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pairing_codes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pairing_codes_code", "pairing_codes", ["code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_pairing_codes_code", table_name="pairing_codes")
    op.drop_table("pairing_codes")
