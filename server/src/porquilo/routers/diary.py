from __future__ import annotations

import uuid
from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models import Meal, MealSkip

router = APIRouter(prefix="/api/diary", tags=["diary"])


def _parse_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise HTTPException(status_code=422, detail="date must be YYYY-MM-DD")


class MealDay(BaseModel):
    meal_id: UUID
    name: str
    sort_order: int
    is_skipped: bool


@router.get("/{date}", response_model=list[MealDay])
def get_diary(date: str, session: Session = Depends(get_session)):
    parsed = _parse_date(date)
    meals = session.execute(select(Meal).order_by(Meal.sort_order)).scalars().all()

    meal_ids = [m.id for m in meals]
    skipped_ids: set[uuid.UUID] = set()
    if meal_ids:
        skips = session.execute(
            select(MealSkip).where(
                MealSkip.meal_id.in_(meal_ids),
                MealSkip.skipped_on == parsed,
            )
        ).scalars().all()
        skipped_ids = {s.meal_id for s in skips}

    return [
        MealDay(
            meal_id=m.id,
            name=m.name,
            sort_order=m.sort_order,
            is_skipped=m.id in skipped_ids,
        )
        for m in meals
    ]


@router.post("/{date}/meals/{meal_id}/skip", status_code=201)
def skip_meal(date: str, meal_id: UUID, session: Session = Depends(get_session)):
    parsed = _parse_date(date)

    meal = session.get(Meal, meal_id)
    if meal is None:
        raise HTTPException(status_code=422, detail="meal_id not found")

    existing = session.execute(
        select(MealSkip).where(
            MealSkip.meal_id == meal_id,
            MealSkip.skipped_on == parsed,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="meal already skipped on this date")

    session.add(MealSkip(meal_id=meal_id, skipped_on=parsed))
    session.commit()


@router.delete("/{date}/meals/{meal_id}/skip", status_code=204)
def unskip_meal(date: str, meal_id: UUID, session: Session = Depends(get_session)):
    parsed = _parse_date(date)

    skip = session.execute(
        select(MealSkip).where(
            MealSkip.meal_id == meal_id,
            MealSkip.skipped_on == parsed,
        )
    ).scalar_one_or_none()
    if skip is None:
        raise HTTPException(status_code=404, detail="no skip found for this meal on this date")

    session.delete(skip)
    session.commit()
