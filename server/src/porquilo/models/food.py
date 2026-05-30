import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class Food(SQLModel, table=True):
    __tablename__ = "foods"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = Field(default=None, unique=True)
    food_source_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="food_sources.id")
    external_source_id: Optional[str] = None
    default_unit: str = "g"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
