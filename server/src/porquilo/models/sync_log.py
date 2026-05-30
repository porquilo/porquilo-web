import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class SyncLog(SQLModel, table=True):
    __tablename__ = "sync_log"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    food_source_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="food_sources.id")
    completed_at: datetime
    record_count: int
    duration_seconds: float
    file_hash: Optional[str] = None
    notes: Optional[str] = None
