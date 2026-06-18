"""users and auth_tokens tables; user_id FK on log_entries, body_metrics, goals

Revision ID: 016
Revises: 015
Create Date: 2026-06-17
"""

import sqlalchemy as sa
from alembic import op

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("username", sa.Text(), nullable=False),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("units_preference", sa.Text(), nullable=True),
        sa.Column("timezone", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.CheckConstraint("role IN ('admin', 'member')", name="ck_users_role"),
        sa.CheckConstraint(
            "units_preference IN ('metric', 'imperial') OR units_preference IS NULL",
            name="ck_users_units_preference",
        ),
    )

    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )

    for table_name, fk_name in [
        ("log_entries", "fk_log_entries_user_id"),
        ("body_metrics", "fk_body_metrics_user_id"),
        ("goals", "fk_goals_user_id"),
    ]:
        with op.batch_alter_table(table_name) as batch_op:
            batch_op.add_column(sa.Column("user_id", sa.Uuid(), nullable=True))
            batch_op.create_foreign_key(
                fk_name, "users", ["user_id"], ["id"], ondelete="SET NULL"
            )

    op.create_index("ix_auth_tokens_token", "auth_tokens", ["token"], unique=True)
    op.create_index("ix_auth_tokens_user_id", "auth_tokens", ["user_id"])
    op.create_index("ix_log_entries_user_id", "log_entries", ["user_id"])
    op.create_index("ix_body_metrics_user_id", "body_metrics", ["user_id"])
    op.create_index("ix_goals_user_id", "goals", ["user_id"])


def downgrade() -> None:
    bind = op.get_bind()

    for table_name, fk_name in [
        ("goals", "fk_goals_user_id"),
        ("body_metrics", "fk_body_metrics_user_id"),
        ("log_entries", "fk_log_entries_user_id"),
    ]:
        op.drop_index(f"ix_{table_name}_user_id", table_name=table_name)
        with op.batch_alter_table(table_name) as batch_op:
            if bind.dialect.name != "sqlite":
                batch_op.drop_constraint(fk_name, type_="foreignkey")
            batch_op.drop_column("user_id")

    op.drop_table("auth_tokens")
    op.drop_table("users")
