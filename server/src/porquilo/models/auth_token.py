import uuid
from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class AuthToken(SQLModel, table=True):
    __tablename__ = "auth_tokens"
    __table_args__ = (
        sa.Index("ix_auth_tokens_token", "token", unique=True),
        sa.Index("ix_auth_tokens_user_id", "user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    user_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="users.id", nullable=False)
    token: str
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
    last_used_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True),
    )
