import uuid
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class RecipeIngredient(SQLModel, table=True):
    __tablename__ = "recipe_ingredients"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    recipe_id: uuid.UUID = Field(
        sa_column=sa.Column(sa.Uuid, sa.ForeignKey("recipes.id", ondelete="CASCADE"), nullable=False)
    )
    food_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="foods.id")
    nested_recipe_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="recipes.id")
    weight_g: Decimal
