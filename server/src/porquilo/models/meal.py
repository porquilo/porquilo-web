import uuid
from datetime import datetime

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class Meal(SQLModel, table=True):
    __tablename__ = "meals"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    name: str
    sort_order: int
    is_default: bool
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))
