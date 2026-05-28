import uuid
from decimal import Decimal

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class RecipeIngredient(SQLModel, table=True):
    __tablename__ = "recipe_ingredients"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    recipe_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="recipes.id")
    ingredient_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="ingredients.id")
    weight_g: Decimal
