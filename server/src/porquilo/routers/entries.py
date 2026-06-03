from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models import Food, LogEntry, LogEntryNutrient, Meal, NutrientDefinition
from porquilo.services.nutrients import compute_nutrients, derive_confidence

router = APIRouter(prefix="/api/entries", tags=["entries"])


class EntryCreate(BaseModel):
    food_id: UUID
    meal_id: UUID
    weight_g: Decimal
    eaten_at: datetime
    weight_source: str
    input_method: str


class NutrientValue(BaseModel):
    value: Decimal
    coverage: str


class EntryOut(BaseModel):
    id: UUID
    nutrients: dict[str, NutrientValue]


# Must be declared before /{id} routes so FastAPI does not match "batch" as a path parameter.
@router.post("/batch", status_code=501)
def create_entries_batch():
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.post("", response_model=EntryOut, status_code=201)
def create_entry(body: EntryCreate, session: Session = Depends(get_session)):
    food = session.get(Food, body.food_id)
    if food is None:
        raise HTTPException(status_code=422, detail="food_id not found")

    meal = session.get(Meal, body.meal_id)
    if meal is None:
        raise HTTPException(status_code=422, detail="meal_id not found")

    nutrients_by_id = compute_nutrients(body.food_id, body.weight_g, session)
    confidence = derive_confidence(body.weight_source)

    entry = LogEntry(
        food_id=body.food_id,
        recipe_id=None,
        meal_id=body.meal_id,
        eaten_at=body.eaten_at,
        logged_at=datetime.now(timezone.utc),
        weight_g=body.weight_g,
        weight_source=body.weight_source,
        weight_confidence=confidence,
        input_method=body.input_method,
    )
    session.add(entry)
    session.flush()

    for nutrient_id, ndata in nutrients_by_id.items():
        session.add(
            LogEntryNutrient(
                log_entry_id=entry.id,
                nutrient_id=nutrient_id,
                value=ndata["value"],
                coverage=ndata["coverage"],
            )
        )

    id_to_key: dict[UUID, str] = {}
    if nutrients_by_id:
        nd_rows = session.execute(
            select(NutrientDefinition).where(
                NutrientDefinition.id.in_(list(nutrients_by_id.keys()))
            )
        ).scalars().all()
        id_to_key = {nd.id: nd.key for nd in nd_rows}

    session.commit()

    return EntryOut(
        id=entry.id,
        nutrients={
            id_to_key[nid]: NutrientValue(value=ndata["value"], coverage=ndata["coverage"])
            for nid, ndata in nutrients_by_id.items()
            if nid in id_to_key
        },
    )
