import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class NutrientDefinition(SQLModel, table=True):
    __tablename__ = "nutrient_definitions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    # Valid keys use snake_case + unit suffix, e.g. protein_g, sodium_mg, calories_kcal.
    # Validated at the application layer only.
    key: str = Field(unique=True)
    display_name: str
    unit: str
    sort_order: int = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
