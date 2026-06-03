from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models import (
    Food,
    LogEntry,
    LogEntryNutrient,
    Meal,
    MealSkip,
    NutrientDefinition,
)

router = APIRouter(prefix="/api/diary", tags=["diary"])


def _parse_date(raw: str) -> date:
    try:
        return date.fromisoformat(raw)
    except ValueError:
        raise HTTPException(status_code=422, detail="date must be YYYY-MM-DD")


class NutrientValue(BaseModel):
    value: Decimal
    coverage: str


class DiaryEntry(BaseModel):
    id: UUID
    food_name: str
    weight_g: Optional[Decimal]
    weight_confidence: str
    input_method: str
    eaten_at: datetime
    nutrients: dict[str, NutrientValue]


class MealResponse(BaseModel):
    meal_id: UUID
    meal_name: str
    is_skipped: bool
    entries: list[DiaryEntry]
    meal_totals: dict[str, Decimal]


class DiaryResponse(BaseModel):
    date: str
    meals: list[MealResponse]
    day_totals: dict[str, Decimal]
    has_estimated_entries: bool


@router.get("/{date}", response_model=DiaryResponse)
def get_diary(date: str, session: Session = Depends(get_session)) -> DiaryResponse:
    parsed_date = _parse_date(date)
    day_start = datetime(parsed_date.year, parsed_date.month, parsed_date.day)
    day_end = day_start + timedelta(days=1)

    meals = session.execute(select(Meal).order_by(Meal.sort_order)).scalars().all()

    skipped_meal_ids: set[uuid.UUID] = {
        row.meal_id
        for row in session.execute(
            select(MealSkip).where(MealSkip.skipped_on == parsed_date)
        ).scalars().all()
    }

    entries = session.execute(
        select(LogEntry)
        .where(LogEntry.eaten_at >= day_start)
        .where(LogEntry.eaten_at < day_end)
        .order_by(LogEntry.meal_id, LogEntry.eaten_at)
    ).scalars().all()

    food_ids = {e.food_id for e in entries if e.food_id is not None}
    food_names: dict[uuid.UUID, str] = {}
    if food_ids:
        for food in session.execute(
            select(Food).where(Food.id.in_(food_ids))
        ).scalars().all():
            food_names[food.id] = food.name

    entry_ids = [e.id for e in entries]
    nutrients_by_entry: dict[uuid.UUID, dict[str, NutrientValue]] = {}
    if entry_ids:
        for len_row, nd in session.execute(
            select(LogEntryNutrient, NutrientDefinition)
            .join(NutrientDefinition, LogEntryNutrient.nutrient_id == NutrientDefinition.id)
            .where(LogEntryNutrient.log_entry_id.in_(entry_ids))
        ).all():
            nutrients_by_entry.setdefault(len_row.log_entry_id, {})[nd.key] = NutrientValue(
                value=len_row.value, coverage=len_row.coverage
            )

    entries_by_meal: dict[uuid.UUID, list[LogEntry]] = {}
    for entry in entries:
        entries_by_meal.setdefault(entry.meal_id, []).append(entry)

    meal_responses: list[MealResponse] = []
    has_estimated = False

    for meal in meals:
        if meal.id in skipped_meal_ids:
            meal_responses.append(MealResponse(
                meal_id=meal.id,
                meal_name=meal.name,
                is_skipped=True,
                entries=[],
                meal_totals={},
            ))
            continue

        meal_entries = entries_by_meal.get(meal.id, [])
        diary_entries: list[DiaryEntry] = []
        meal_totals: dict[str, Decimal] = {}

        for entry in meal_entries:
            if entry.weight_confidence == "estimated":
                has_estimated = True

            entry_nutrients = nutrients_by_entry.get(entry.id, {})
            for key, nv in entry_nutrients.items():
                meal_totals[key] = meal_totals.get(key, Decimal(0)) + nv.value

            diary_entries.append(DiaryEntry(
                id=entry.id,
                food_name=food_names.get(entry.food_id, "") if entry.food_id else "",
                weight_g=entry.weight_g,
                weight_confidence=entry.weight_confidence,
                input_method=entry.input_method,
                eaten_at=entry.eaten_at,
                nutrients=entry_nutrients,
            ))

        meal_responses.append(MealResponse(
            meal_id=meal.id,
            meal_name=meal.name,
            is_skipped=False,
            entries=diary_entries,
            meal_totals=meal_totals,
        ))

    day_totals: dict[str, Decimal] = {}
    for meal_resp in meal_responses:
        for key, val in meal_resp.meal_totals.items():
            day_totals[key] = day_totals.get(key, Decimal(0)) + val

    return DiaryResponse(
        date=date,
        meals=meal_responses,
        day_totals=day_totals,
        has_estimated_entries=has_estimated,
    )


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
