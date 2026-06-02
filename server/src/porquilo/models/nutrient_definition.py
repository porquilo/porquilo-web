import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class NutrientDefinition(SQLModel, table=True):
    __tablename__ = "nutrient_definitions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    key: str = Field(unique=True)
    display_name: str
    unit: str
    sort_order: int = Field(unique=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
    )
