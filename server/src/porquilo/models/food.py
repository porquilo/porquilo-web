import uuid
from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class Food(SQLModel, table=True):
    __tablename__ = "foods"
    __table_args__ = (
        sa.UniqueConstraint(
            "food_source_id", "external_source_id",
            name="uq_foods_source_external_id",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = Field(default=None, unique=True)
    food_source_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="food_sources.id")
    external_source_id: Optional[str] = None
    default_unit: str = "g"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
    )
    source_fetched_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    source_completeness: Optional[float] = Field(
        default=None,
        sa_column=sa.Column(sa.Float, nullable=True),
    )
    display_name: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text, nullable=True),
    )
    display_name_status: Optional[str] = Field(
        default=None,
        sa_column=sa.Column(sa.Text, nullable=True),
    )
