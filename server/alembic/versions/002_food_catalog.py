"""Food catalog: food_sources, foods, food_nutrients, food_variants

Revision ID: 002
Revises: 001
Create Date: 2026-05-28
"""

import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None

_NOW = datetime(2026, 5, 28, 0, 0, 0, tzinfo=timezone.utc)


def _u(s: str) -> uuid.UUID:
    return uuid.UUID(s)


_FS_IDS = {
    "custom":          _u("a1b2c3d4-0001-4000-8000-000000000001"),
    "open_food_facts": _u("a1b2c3d4-0002-4000-8000-000000000002"),
    "usda":            _u("a1b2c3d4-0003-4000-8000-000000000003"),
}


def upgrade() -> None:
    food_sources = op.create_table(
        "food_sources",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_status", sa.String(), nullable=True),
        sa.Column("sync_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("key", name="uq_food_sources_key"),
        sa.CheckConstraint(
            "sync_status IN ('queued', 'running', 'succeeded', 'failed')",
            name="ck_food_sources_sync_status",
        ),
    )

    op.create_table(
        "foods",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("brand", sa.String(), nullable=True),
        sa.Column("barcode", sa.String(), nullable=True, unique=True),
        sa.Column(
            "food_source_id",
            sa.Uuid(),
            sa.ForeignKey("food_sources.id"),
            nullable=False,
        ),
        sa.Column("external_source_id", sa.String(), nullable=True),
        sa.Column("default_unit", sa.String(), nullable=False, server_default="g"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "food_source_id", "external_source_id",
            name="uq_foods_source_external_id",
        ),
    )

    op.create_table(
        "food_nutrients",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "food_id",
            sa.Uuid(),
            sa.ForeignKey("foods.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "nutrient_id",
            sa.Uuid(),
            sa.ForeignKey("nutrient_definitions.id"),
            nullable=False,
        ),
        sa.Column("value_per_100", sa.Numeric(), nullable=False),
        sa.UniqueConstraint("food_id", "nutrient_id", name="uq_food_nutrients_food_nutrient"),
    )

    op.create_table(
        "food_variants",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "food_id",
            sa.Uuid(),
            sa.ForeignKey("foods.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("amount", sa.Numeric(), nullable=True),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # fmt: off
    op.bulk_insert(food_sources, [
        {"id": _FS_IDS["custom"],          "display_name": "Custom",          "key": "custom",          "is_active": True, "last_synced_at": None, "sync_status": None, "sync_error": None, "created_at": _NOW, "updated_at": _NOW},
        {"id": _FS_IDS["open_food_facts"], "display_name": "Open Food Facts", "key": "open_food_facts", "is_active": True, "last_synced_at": None, "sync_status": None, "sync_error": None, "created_at": _NOW, "updated_at": _NOW},
        {"id": _FS_IDS["usda"],            "display_name": "USDA",            "key": "usda",            "is_active": True, "last_synced_at": None, "sync_status": None, "sync_error": None, "created_at": _NOW, "updated_at": _NOW},
    ])
    # fmt: on


def downgrade() -> None:
    op.drop_table("food_variants")
    op.drop_table("food_nutrients")
    op.drop_table("foods")
    op.drop_table("food_sources")
