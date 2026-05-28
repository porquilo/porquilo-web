import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class FoodSource(SQLModel, table=True):
    __tablename__ = "food_sources"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    key: str = Field(unique=True)
    display_name: str
    is_active: bool = True
    last_synced_at: Optional[datetime] = None
    sync_status: Optional[str] = None
    sync_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
