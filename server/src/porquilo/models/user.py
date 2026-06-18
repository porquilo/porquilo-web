import uuid
from datetime import datetime
from datetime import timezone as tz
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        sa.UniqueConstraint("username", name="uq_users_username"),
        sa.CheckConstraint("role IN ('admin', 'member')", name="ck_users_role"),
        sa.CheckConstraint(
            "units_preference IN ('metric', 'imperial') OR units_preference IS NULL",
            name="ck_users_units_preference",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    username: str
    hashed_password: str
    role: str
    name: Optional[str] = None
    units_preference: Optional[str] = None
    timezone: Optional[str] = None
    is_active: bool = Field(
        default=True,
        sa_column=sa.Column(sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(tz.utc),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(tz.utc),
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
