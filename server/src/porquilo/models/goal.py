import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class Goal(SQLModel, table=True):
    __tablename__ = "goals"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    # Known values: fixed, exercise_adjusted — open/extensible, not constrained at DB level.
    calorie_mode: str
    calorie_target: Decimal
    # Null when calorie_mode is 'fixed'; enforced at application layer.
    calorie_factor: Optional[Decimal] = None
    effective_from: date = Field(sa_column=sa.Column(sa.Date(), unique=True, nullable=False))
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
