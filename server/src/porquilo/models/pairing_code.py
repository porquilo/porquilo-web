import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class PairingCode(SQLModel, table=True):
    __tablename__ = "pairing_codes"
    __table_args__ = (sa.Index("ix_pairing_codes_code", "code", unique=True),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    user_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="users.id", nullable=False)
    code: str
    expires_at: datetime = Field(sa_column=sa.Column(sa.DateTime(timezone=True), nullable=False))
    used_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
