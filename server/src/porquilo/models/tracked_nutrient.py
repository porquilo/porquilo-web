import uuid
from datetime import datetime

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class TrackedNutrient(SQLModel, table=True):
    __tablename__ = "tracked_nutrients"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    nutrient_id: uuid.UUID = Field(
        foreign_key="nutrient_definitions.id", unique=True, sa_type=Uuid
    )
    display_order: int
    show_in_diary: bool
    show_in_goals: bool
    show_in_charts: bool
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
