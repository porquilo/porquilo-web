"""Remove ingredients table: replace polymorphic FK with direct food_id/recipe_id FKs

Revision ID: 008
Revises: 007
Create Date: 2026-06-03
"""

import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    dialect = op.get_bind().dialect.name

    # 1. Drop the old self-reference triggers (they join through ingredients which is being removed)
    if dialect == "sqlite":
        op.execute(sa.text("DROP TRIGGER IF EXISTS ck_recipe_ingredients_no_self_ref"))
        op.execute(sa.text("DROP TRIGGER IF EXISTS ck_recipe_ingredients_no_self_ref_upd"))
    else:
        op.execute(sa.text(
            "DROP TRIGGER IF EXISTS ck_recipe_ingredients_no_self_ref ON recipe_ingredients"
        ))
        op.execute(sa.text("DROP FUNCTION IF EXISTS _check_recipe_no_self_ref"))

    # 2. Drop index on ingredient_id that is about to be removed
    op.drop_index("ix_recipe_ingredients_ingredient_id", table_name="recipe_ingredients")

    # 3. Alter log_entries: swap ingredient_id for food_id + recipe_id
    # On PostgreSQL, batch recreate fails while log_entry_nutrients has a FK referencing
    # log_entries.id (PostgreSQL won't drop the PK index backing the constraint).
    # Drop and re-add that FK around the batch alter.
    if dialect != "sqlite":
        op.drop_constraint(
            "log_entry_nutrients_log_entry_id_fkey", "log_entry_nutrients", type_="foreignkey"
        )

    with op.batch_alter_table("log_entries", recreate="always") as batch_op:
        batch_op.drop_column("ingredient_id")
        batch_op.add_column(sa.Column("food_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("recipe_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_log_entries_food_id", "foods", ["food_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_log_entries_recipe_id", "recipes", ["recipe_id"], ["id"]
        )
        batch_op.create_check_constraint(
            "ck_log_entries_exactly_one_fk",
            "(food_id IS NOT NULL AND recipe_id IS NULL)"
            " OR (food_id IS NULL AND recipe_id IS NOT NULL)",
        )

    if dialect != "sqlite":
        op.create_foreign_key(
            "log_entry_nutrients_log_entry_id_fkey",
            "log_entry_nutrients", "log_entries",
            ["log_entry_id"], ["id"],
            ondelete="CASCADE",
        )

    # 4. Alter recipe_ingredients: swap ingredient_id for food_id + nested_recipe_id
    with op.batch_alter_table("recipe_ingredients", recreate="always") as batch_op:
        batch_op.drop_column("ingredient_id")
        batch_op.add_column(sa.Column("food_id", sa.Uuid(), nullable=True))
        batch_op.add_column(sa.Column("nested_recipe_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_recipe_ingredients_food_id", "foods", ["food_id"], ["id"]
        )
        batch_op.create_foreign_key(
            "fk_recipe_ingredients_nested_recipe_id", "recipes", ["nested_recipe_id"], ["id"]
        )
        batch_op.create_check_constraint(
            "ck_recipe_ingredients_exactly_one_fk",
            "(food_id IS NOT NULL AND nested_recipe_id IS NULL)"
            " OR (food_id IS NULL AND nested_recipe_id IS NOT NULL)",
        )
        # Direct self-reference guard: now expressible as a CHECK since both columns are on the
        # same row — no trigger or cross-table join needed.
        batch_op.create_check_constraint(
            "ck_recipe_ingredients_no_self_ref",
            "nested_recipe_id IS NULL OR nested_recipe_id != recipe_id",
        )

    # 5. Drop the ingredients table (all referencing FKs have been removed above)
    op.drop_table("ingredients")

    # 6. Add indexes on the new FK columns
    op.create_index("ix_log_entries_food_id", "log_entries", ["food_id"])
    op.create_index("ix_log_entries_recipe_id", "log_entries", ["recipe_id"])
    op.create_index("ix_recipe_ingredients_food_id", "recipe_ingredients", ["food_id"])
    op.create_index(
        "ix_recipe_ingredients_nested_recipe_id", "recipe_ingredients", ["nested_recipe_id"]
    )


def downgrade() -> None:
    dialect = op.get_bind().dialect.name

    # 1. Drop the new indexes
    op.drop_index("ix_recipe_ingredients_nested_recipe_id", table_name="recipe_ingredients")
    op.drop_index("ix_recipe_ingredients_food_id", table_name="recipe_ingredients")
    op.drop_index("ix_log_entries_recipe_id", table_name="log_entries")
    op.drop_index("ix_log_entries_food_id", table_name="log_entries")

    # 2. Recreate the ingredients table (schema from migration 003)
    op.create_table(
        "ingredients",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("food_id", sa.Uuid(), sa.ForeignKey("foods.id"), nullable=True),
        sa.Column("recipe_id", sa.Uuid(), sa.ForeignKey("recipes.id"), nullable=True),
        sa.UniqueConstraint("food_id", name="uq_ingredients_food_id"),
        sa.UniqueConstraint("recipe_id", name="uq_ingredients_recipe_id"),
        sa.CheckConstraint(
            "(food_id IS NOT NULL AND recipe_id IS NULL)"
            " OR (food_id IS NULL AND recipe_id IS NOT NULL)",
            name="ck_ingredients_exactly_one_fk",
        ),
    )

    # 3. Restore recipe_ingredients.ingredient_id (data is not recoverable — ingredient_id is NULL)
    with op.batch_alter_table("recipe_ingredients", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_recipe_ingredients_no_self_ref", type_="check")
        batch_op.drop_constraint("ck_recipe_ingredients_exactly_one_fk", type_="check")
        batch_op.drop_constraint("fk_recipe_ingredients_nested_recipe_id", type_="foreignkey")
        batch_op.drop_constraint("fk_recipe_ingredients_food_id", type_="foreignkey")
        batch_op.drop_column("nested_recipe_id")
        batch_op.drop_column("food_id")
        batch_op.add_column(sa.Column("ingredient_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_recipe_ingredients_ingredient_id", "ingredients", ["ingredient_id"], ["id"]
        )

    # 4. Restore log_entries.ingredient_id
    # Same FK dependency issue as in upgrade: drop before batch recreate, restore after.
    if dialect != "sqlite":
        op.drop_constraint(
            "log_entry_nutrients_log_entry_id_fkey", "log_entry_nutrients", type_="foreignkey"
        )

    with op.batch_alter_table("log_entries", recreate="always") as batch_op:
        batch_op.drop_constraint("ck_log_entries_exactly_one_fk", type_="check")
        batch_op.drop_constraint("fk_log_entries_recipe_id", type_="foreignkey")
        batch_op.drop_constraint("fk_log_entries_food_id", type_="foreignkey")
        batch_op.drop_column("recipe_id")
        batch_op.drop_column("food_id")
        batch_op.add_column(sa.Column("ingredient_id", sa.Uuid(), nullable=True))
        batch_op.create_foreign_key(
            "fk_log_entries_ingredient_id", "ingredients", ["ingredient_id"], ["id"]
        )

    if dialect != "sqlite":
        op.create_foreign_key(
            "log_entry_nutrients_log_entry_id_fkey",
            "log_entry_nutrients", "log_entries",
            ["log_entry_id"], ["id"],
            ondelete="CASCADE",
        )

    # 5. Restore ingredient_id index
    op.create_index(
        "ix_recipe_ingredients_ingredient_id", "recipe_ingredients", ["ingredient_id"]
    )

    # 6. Restore self-reference triggers
    if dialect == "sqlite":
        op.execute(sa.text(
            "CREATE TRIGGER ck_recipe_ingredients_no_self_ref"
            " BEFORE INSERT ON recipe_ingredients"
            " FOR EACH ROW"
            " BEGIN"
            "   SELECT RAISE(ABORT, 'recipe cannot reference itself as an ingredient')"
            "   WHERE EXISTS ("
            "     SELECT 1 FROM ingredients"
            "     WHERE id = NEW.ingredient_id AND recipe_id = NEW.recipe_id"
            "   );"
            " END"
        ))
        op.execute(sa.text(
            "CREATE TRIGGER ck_recipe_ingredients_no_self_ref_upd"
            " BEFORE UPDATE ON recipe_ingredients"
            " FOR EACH ROW"
            " BEGIN"
            "   SELECT RAISE(ABORT, 'recipe cannot reference itself as an ingredient')"
            "   WHERE EXISTS ("
            "     SELECT 1 FROM ingredients"
            "     WHERE id = NEW.ingredient_id AND recipe_id = NEW.recipe_id"
            "   );"
            " END"
        ))
    else:
        op.execute(sa.text(
            "CREATE OR REPLACE FUNCTION _check_recipe_no_self_ref()"
            " RETURNS trigger AS $$"
            " BEGIN"
            "   IF EXISTS ("
            "     SELECT 1 FROM ingredients"
            "     WHERE id = NEW.ingredient_id AND recipe_id = NEW.recipe_id"
            "   ) THEN"
            "     RAISE EXCEPTION 'recipe cannot reference itself as an ingredient';"
            "   END IF;"
            "   RETURN NEW;"
            " END;"
            " $$ LANGUAGE plpgsql"
        ))
        op.execute(sa.text(
            "CREATE TRIGGER ck_recipe_ingredients_no_self_ref"
            " BEFORE INSERT OR UPDATE ON recipe_ingredients"
            " FOR EACH ROW EXECUTE FUNCTION _check_recipe_no_self_ref()"
        ))
