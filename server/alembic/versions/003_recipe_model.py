"""Recipe model: recipes, ingredients, recipe_ingredients

Revision ID: 003
Revises: 002
Create Date: 2026-05-28
"""

import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recipes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("total_yield_g", sa.Numeric(), nullable=True),
        sa.Column("yield_estimated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("servings", sa.Numeric(), nullable=True),
        sa.Column("yield_description", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source", "source_id", name="uq_recipes_source_source_id"),
    )

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

    op.create_table(
        "recipe_ingredients",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "recipe_id",
            sa.Uuid(),
            sa.ForeignKey("recipes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "ingredient_id",
            sa.Uuid(),
            sa.ForeignKey("ingredients.id"),
            nullable=False,
        ),
        sa.Column("weight_g", sa.Numeric(), nullable=False),
    )

    # Cross-table self-reference guard: a recipe cannot appear as its own ingredient.
    # A simple CHECK cannot reference other tables, so we use a trigger.
    dialect = op.get_bind().dialect.name
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


def downgrade() -> None:
    dialect = op.get_bind().dialect.name
    if dialect == "sqlite":
        op.execute(sa.text("DROP TRIGGER IF EXISTS ck_recipe_ingredients_no_self_ref"))
        op.execute(sa.text("DROP TRIGGER IF EXISTS ck_recipe_ingredients_no_self_ref_upd"))
    else:
        op.execute(sa.text(
            "DROP TRIGGER IF EXISTS ck_recipe_ingredients_no_self_ref ON recipe_ingredients"
        ))
        op.execute(sa.text("DROP FUNCTION IF EXISTS _check_recipe_no_self_ref"))

    op.drop_table("recipe_ingredients")
    op.drop_table("ingredients")
    op.drop_table("recipes")
