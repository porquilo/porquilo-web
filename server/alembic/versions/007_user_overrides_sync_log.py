"""User overrides and sync log

Revision ID: 007
Revises: 006
Create Date: 2026-05-29
"""

import sqlalchemy as sa
from alembic import op

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None

_WHERE_NUTRIENT = sa.text("nutrient_id IS NOT NULL")
_WHERE_FIELD = sa.text("field IS NOT NULL")


def upgrade() -> None:
    op.create_table(
        "user_overrides",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "food_id",
            sa.Uuid(),
            sa.ForeignKey("foods.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("field", sa.String(), nullable=True),
        sa.Column(
            "nutrient_id",
            sa.Uuid(),
            sa.ForeignKey("nutrient_definitions.id"),
            nullable=True,
        ),
        sa.Column("original_value", sa.String(), nullable=True),
        sa.Column("corrected_value", sa.String(), nullable=False),
        sa.Column("corrected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("contributed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("contribution_status", sa.String(), nullable=True),
        sa.CheckConstraint(
            "(field IS NULL AND nutrient_id IS NOT NULL)"
            " OR (field IS NOT NULL AND nutrient_id IS NULL)",
            name="ck_user_overrides_field_xor_nutrient",
        ),
        sa.CheckConstraint(
            "contribution_status IN ('pending', 'submitted', 'accepted', 'rejected')",
            name="ck_user_overrides_contribution_status",
        ),
    )

    op.create_table(
        "sync_log",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "food_source_id",
            sa.Uuid(),
            sa.ForeignKey("food_sources.id"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("record_count", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False),
        sa.Column("file_hash", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
    )

    # Partial unique indexes for user_overrides (enforce one override per field/nutrient per food)
    op.create_index(
        "uq_user_overrides_food_field",
        "user_overrides",
        ["food_id", "field"],
        unique=True,
        postgresql_where=_WHERE_FIELD,
        sqlite_where=_WHERE_FIELD,
    )
    op.create_index(
        "uq_user_overrides_food_nutrient",
        "user_overrides",
        ["food_id", "nutrient_id"],
        unique=True,
        postgresql_where=_WHERE_NUTRIENT,
        sqlite_where=_WHERE_NUTRIENT,
    )

    # Regular index for sync_log lookup by source + time
    op.create_index(
        "ix_sync_log_source_completed",
        "sync_log",
        ["food_source_id", "completed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_sync_log_source_completed", table_name="sync_log")
    op.drop_index("uq_user_overrides_food_nutrient", table_name="user_overrides")
    op.drop_index("uq_user_overrides_food_field", table_name="user_overrides")
    op.drop_table("sync_log")
    op.drop_table("user_overrides")
