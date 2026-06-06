"""Add app_settings table

Revision ID: 010
Revises: 009
Create Date: 2026-06-05
"""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None

_app_settings = sa.table(
    "app_settings",
    sa.column("key", sa.Text),
    sa.column("value", sa.Text),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.Text, primary_key=True),
        sa.Column("value", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    now = datetime.now(timezone.utc)
    op.bulk_insert(
        _app_settings,
        [
            {"key": "mealie_api_key", "value": None, "updated_at": now},
            {"key": "mealie_url",     "value": None, "updated_at": now},
            {"key": "off_password",   "value": None, "updated_at": now},
            {"key": "off_username",   "value": None, "updated_at": now},
            {"key": "usda_api_key",   "value": None, "updated_at": now},
        ],
    )


def downgrade() -> None:
    op.drop_table("app_settings")
