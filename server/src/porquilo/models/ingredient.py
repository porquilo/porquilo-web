import uuid
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class Ingredient(SQLModel, table=True):
    __tablename__ = "ingredients"
    __table_args__ = (
        sa.UniqueConstraint("food_id", name="uq_ingredients_food_id"),
        sa.UniqueConstraint("recipe_id", name="uq_ingredients_recipe_id"),
        sa.CheckConstraint(
            "(food_id IS NOT NULL AND recipe_id IS NULL)"
            " OR (food_id IS NULL AND recipe_id IS NOT NULL)",
            name="ck_ingredients_exactly_one_fk",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    food_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="foods.id")
    recipe_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="recipes.id")
