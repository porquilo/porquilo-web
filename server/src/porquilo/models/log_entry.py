import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class LogEntry(SQLModel, table=True):
    __tablename__ = "log_entries"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    food_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="foods.id")
    recipe_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="recipes.id")
    meal_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="meals.id")
    eaten_at: datetime = Field(sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False))
    logged_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
    )
    user_id: Optional[uuid.UUID] = Field(default=None, sa_type=Uuid, foreign_key="users.id")
    weight_g: Optional[Decimal] = None
    weight_source: str
    weight_confidence: str
    input_method: str
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
