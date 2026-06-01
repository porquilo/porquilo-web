import uuid
from datetime import datetime, timezone
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class UserOverride(SQLModel, table=True):
    __tablename__ = "user_overrides"
    __table_args__ = (
        sa.CheckConstraint(
            "(field IS NULL AND nutrient_id IS NOT NULL)"
            " OR (field IS NOT NULL AND nutrient_id IS NULL)",
            name="ck_user_overrides_exactly_one",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    food_id: uuid.UUID = Field(
        sa_column=sa.Column(sa.Uuid, sa.ForeignKey("foods.id", ondelete="CASCADE"), nullable=False)
    )
    field: Optional[str] = None
    nutrient_id: Optional[uuid.UUID] = Field(
        default=None, sa_type=Uuid, foreign_key="nutrient_definitions.id"
    )
    original_value: Optional[str] = None
    corrected_value: str
    corrected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False),
    )
    contributed_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    contribution_status: Optional[str] = None
