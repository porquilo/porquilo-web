"""Add per-category nutrient completeness columns to foods; seed fat sub-type nutrients

Revision ID: 012
Revises: 011
Create Date: 2026-06-07
"""
import datetime
import uuid

from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None

_NUTRIENT_KEYS = [
    ("trans_fat_g",           "Trans Fat",           "g"),
    ("monounsaturated_fat_g", "Monounsaturated Fat", "g"),
    ("polyunsaturated_fat_g", "Polyunsaturated Fat", "g"),
]


def upgrade() -> None:
    with op.batch_alter_table("foods") as batch_op:
        batch_op.add_column(
            sa.Column(
                "macro_completeness",
                sa.Float,
                sa.CheckConstraint(
                    "macro_completeness >= 0.0 AND macro_completeness <= 1.0",
                    name="ck_foods_macro_completeness",
                ),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "fat_completeness",
                sa.Float,
                sa.CheckConstraint(
                    "fat_completeness >= 0.0 AND fat_completeness <= 1.0",
                    name="ck_foods_fat_completeness",
                ),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "mineral_completeness",
                sa.Float,
                sa.CheckConstraint(
                    "mineral_completeness >= 0.0 AND mineral_completeness <= 1.0",
                    name="ck_foods_mineral_completeness",
                ),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "vitamin_completeness",
                sa.Float,
                sa.CheckConstraint(
                    "vitamin_completeness >= 0.0 AND vitamin_completeness <= 1.0",
                    name="ck_foods_vitamin_completeness",
                ),
                nullable=True,
            )
        )

    _now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    for key, display_name, unit in _NUTRIENT_KEYS:
        op.execute(
            sa.text(
                "INSERT INTO nutrient_definitions (id, key, display_name, unit, sort_order, created_at) "
                "SELECT :id, :key, :display_name, :unit, "
                "(SELECT COALESCE(MAX(sort_order), 0) + 1 FROM nutrient_definitions), "
                ":ts "
                "WHERE NOT EXISTS (SELECT 1 FROM nutrient_definitions WHERE key = :key)"
            ).bindparams(
                id=str(uuid.uuid4()),
                key=key,
                display_name=display_name,
                unit=unit,
                ts=_now,
            )
        )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM nutrient_definitions "
            "WHERE key IN ('trans_fat_g', 'monounsaturated_fat_g', 'polyunsaturated_fat_g')"
        )
    )

    with op.batch_alter_table("foods") as batch_op:
        batch_op.drop_constraint("ck_foods_vitamin_completeness", type_="check")
        batch_op.drop_constraint("ck_foods_mineral_completeness", type_="check")
        batch_op.drop_constraint("ck_foods_fat_completeness", type_="check")
        batch_op.drop_constraint("ck_foods_macro_completeness", type_="check")
        batch_op.drop_column("vitamin_completeness")
        batch_op.drop_column("mineral_completeness")
        batch_op.drop_column("fat_completeness")
        batch_op.drop_column("macro_completeness")
