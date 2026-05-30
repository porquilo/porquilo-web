import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Uuid
from sqlmodel import Field, SQLModel


class BodyMetric(SQLModel, table=True):
    __tablename__ = "body_metrics"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, sa_type=Uuid)
    # Known values: weight_kg, body_fat_pct, waist_cm, etc. — open/extensible.
    metric_type: str
    value: Optional[Decimal] = None
    measured_at: Optional[datetime] = None
    # Known values: manual, apple_health, health_connect, fitbit, withings, garmin — open/extensible.
    source: str
    created_at: Optional[datetime] = Field(default_factory=datetime.now(timezone.utc))
