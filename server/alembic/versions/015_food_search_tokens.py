"""food_search_tokens table for prefix-match word-token search

Revision ID: 015
Revises: 014
Create Date: 2026-06-08
"""

import re
import uuid

import sqlalchemy as sa
from alembic import op

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def _tokenize(text):
    """Inline copy of services.search_tokens.tokenize — kept here so the migration
    remains self-contained and survives future service refactors."""
    if not text:
        return []
    lowered = text.lower()
    parts = re.split(r"[^a-z0-9]+", lowered)
    seen = set()
    result = []
    for p in parts:
        if len(p) >= 2 and p not in seen:
            seen.add(p)
            result.append(p)
    return result


def upgrade() -> None:
    op.create_table(
        "food_search_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "food_id",
            sa.Uuid(),
            sa.ForeignKey("foods.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.Text(), nullable=False),
    )
    op.create_index("ix_food_search_tokens_token", "food_search_tokens", ["token"])
    op.create_index("ix_food_search_tokens_food_id", "food_search_tokens", ["food_id"])

    # Backfill existing foods in batches.
    conn = op.get_bind()
    foods_tbl = sa.table(
        "foods",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("brand", sa.String()),
    )
    tokens_tbl = sa.table(
        "food_search_tokens",
        sa.column("id", sa.Uuid()),
        sa.column("food_id", sa.Uuid()),
        sa.column("token", sa.Text()),
    )

    BATCH = 500
    offset = 0
    while True:
        rows = conn.execute(
            sa.select(foods_tbl).offset(offset).limit(BATCH)
        ).fetchall()
        if not rows:
            break
        to_insert = []
        for row in rows:
            tokens = set(_tokenize(row.name)) | set(_tokenize(row.brand))
            for token in tokens:
                to_insert.append(
                    {"id": uuid.uuid4(), "food_id": row.id, "token": token}
                )
        if to_insert:
            conn.execute(tokens_tbl.insert(), to_insert)
        offset += BATCH


def downgrade() -> None:
    op.drop_table("food_search_tokens")
