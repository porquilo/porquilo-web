import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class LogEntry(SQLModel, table=True):
    __tablename__ = "log_entries"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    ingredient_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="ingredients.id")
    meal_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="meals.id")
    eaten_at: datetime
    logged_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    weight_g: Optional[Decimal] = None
    weight_source: str
    weight_confidence: str
    input_method: str
    created_at: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
