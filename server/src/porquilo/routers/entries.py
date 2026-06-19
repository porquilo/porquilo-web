from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.core.deps import get_current_user
from porquilo.models import Food, LogEntry, LogEntryNutrient, Meal, NutrientDefinition
from porquilo.models.user import User
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


class EntryDetailOut(BaseModel):
    id: UUID
    food_id: UUID
    food_name: str
    meal_id: UUID
    eaten_at: datetime
    logged_at: datetime
    weight_g: Decimal
    weight_source: str
    weight_confidence: str
    input_method: str
    nutrients: dict[str, NutrientValue]


class EntryPatch(BaseModel):
    meal_id:       Optional[UUID]     = None
    eaten_at:      Optional[datetime] = None
    weight_g:      Optional[Decimal]  = None
    weight_source: Optional[str]      = None


def _entry_detail_out(entry: LogEntry, session: Session) -> EntryDetailOut:
    food = session.get(Food, entry.food_id)
    food_name = food.name if food else "Unknown"

    nutrient_rows = session.execute(
        select(LogEntryNutrient, NutrientDefinition)
        .join(NutrientDefinition, LogEntryNutrient.nutrient_id == NutrientDefinition.id)
        .where(LogEntryNutrient.log_entry_id == entry.id)
    ).all()

    nutrients = {
        nd.key: NutrientValue(value=len_row.value, coverage=len_row.coverage)
        for len_row, nd in nutrient_rows
    }

    return EntryDetailOut(
        id=entry.id,
        food_id=entry.food_id,
        food_name=food_name,
        meal_id=entry.meal_id,
        eaten_at=entry.eaten_at,
        logged_at=entry.logged_at,
        weight_g=entry.weight_g,
        weight_source=entry.weight_source,
        weight_confidence=entry.weight_confidence,
        input_method=entry.input_method,
        nutrients=nutrients,
    )


# Must be declared before /{id} routes so FastAPI does not match "batch" as a path parameter.
@router.post("/batch", status_code=501)
def create_entries_batch():
    raise HTTPException(status_code=501, detail="Not Implemented")


@router.post("", response_model=EntryOut, status_code=201)
def create_entry(body: EntryCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
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
        user_id=current_user.id,
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


@router.delete("/{entry_id}", status_code=204)
def delete_entry(entry_id: UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    entry = session.get(LogEntry, entry_id)
    if entry is None or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    session.delete(entry)
    session.commit()


@router.patch("/{entry_id}", response_model=EntryDetailOut)
def patch_entry(entry_id: UUID, body: EntryPatch, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    entry = session.get(LogEntry, entry_id)
    if entry is None or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Entry not found")

    if "meal_id" in body.model_fields_set:
        meal = session.get(Meal, body.meal_id)
        if meal is None:
            raise HTTPException(status_code=422, detail="meal_id not found")
        entry.meal_id = body.meal_id

    if "eaten_at" in body.model_fields_set:
        entry.eaten_at = body.eaten_at

    if {"weight_g", "weight_source"} & body.model_fields_set:
        effective_weight_g = body.weight_g if "weight_g" in body.model_fields_set else entry.weight_g
        effective_weight_source = body.weight_source if "weight_source" in body.model_fields_set else entry.weight_source

        entry.weight_g = effective_weight_g
        entry.weight_source = effective_weight_source
        entry.weight_confidence = derive_confidence(effective_weight_source)

        nutrients_by_id = compute_nutrients(entry.food_id, effective_weight_g, session)

        existing = session.execute(
            select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == entry.id)
        ).scalars().all()
        for row in existing:
            session.delete(row)
        session.flush()

        for nutrient_id, ndata in nutrients_by_id.items():
            session.add(LogEntryNutrient(
                log_entry_id=entry.id,
                nutrient_id=nutrient_id,
                value=ndata["value"],
                coverage=ndata["coverage"],
            ))

    session.add(entry)
    session.commit()
    session.refresh(entry)
    return _entry_detail_out(entry, session)


@router.get("/{entry_id}", response_model=EntryDetailOut)
def get_entry(entry_id: UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    entry = session.get(LogEntry, entry_id)
    if entry is None or entry.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Entry not found")
    return _entry_detail_out(entry, session)
