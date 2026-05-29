import uuid
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class GoalNutrient(SQLModel, table=True):
    __tablename__ = "goal_nutrients"
    __table_args__ = (
        sa.UniqueConstraint(
            "goal_id", "nutrient_id",
            name="uq_goal_nutrients_goal_nutrient",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    goal_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="goals.id")
    nutrient_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="nutrient_definitions.id")
    # Null means use system-calculated default (protein 20%, carbs 50%, fat 30% of calorie_target).
    target_value: Optional[Decimal] = None
