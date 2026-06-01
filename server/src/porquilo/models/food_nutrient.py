import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class FoodNutrient(SQLModel, table=True):
    __tablename__ = "food_nutrients"
    __table_args__ = (
        sa.UniqueConstraint("food_id", "nutrient_id", name="uq_food_nutrients_food_nutrient"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    food_id: uuid.UUID = Field(
        sa_column=sa.Column(sa.Uuid, sa.ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    )
    nutrient_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="nutrient_definitions.id")
    value_per_100: Decimal
