import uuid
from datetime import date, datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class MealSkip(SQLModel, table=True):
    __tablename__ = "meal_skips"
    __table_args__ = (
        sa.UniqueConstraint("meal_id", "skipped_on", name="uq_meal_skips_meal_date"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    meal_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="meals.id")
    skipped_on: date
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
