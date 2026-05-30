import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class UserOverride(SQLModel, table=True):
    __tablename__ = "user_overrides"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    food_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="foods.id")
    field: Optional[str] = None
    nutrient_id: Optional[uuid.UUID] = Field(
        default=None, sa_type=Uuid, foreign_key="nutrient_definitions.id"
    )
    original_value: Optional[str] = None
    corrected_value: str
    corrected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    contributed_at: Optional[datetime] = None
    contribution_status: Optional[str] = None
