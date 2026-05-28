import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class FoodVariant(SQLModel, table=True):
    __tablename__ = "food_variants"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    food_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="foods.id")
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    unit: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
