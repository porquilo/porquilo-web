import uuid
from decimal import Decimal

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class FoodNutrient(SQLModel, table=True):
    __tablename__ = "food_nutrients"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    food_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="foods.id")
    nutrient_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="nutrient_definitions.id")
    value_per_100: Decimal
