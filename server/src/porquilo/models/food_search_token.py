import uuid

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class FoodSearchToken(SQLModel, table=True):
    __tablename__ = "food_search_tokens"
    __table_args__ = (
        sa.Index("ix_food_search_tokens_token", "token"),
        sa.Index("ix_food_search_tokens_food_id", "food_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    food_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="foods.id", nullable=False)
    token: str
