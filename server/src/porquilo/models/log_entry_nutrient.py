import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class LogEntryNutrient(SQLModel, table=True):
    __tablename__ = "log_entry_nutrients"
    __table_args__ = (
        sa.UniqueConstraint(
            "log_entry_id", "nutrient_id",
            name="uq_log_entry_nutrients_entry_nutrient",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    log_entry_id: uuid.UUID = Field(
        sa_column=sa.Column(
            sa.Uuid, sa.ForeignKey("log_entries.id", ondelete="CASCADE"), nullable=False
        )
    )
    nutrient_id: uuid.UUID = Field(sa_type=Uuid, foreign_key="nutrient_definitions.id")
    value: Decimal
    coverage: str
