from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, func, select

from porquilo.core.database import get_session
from porquilo.models import LogEntry, Meal

router = APIRouter(prefix="/api/meals", tags=["meals"])


class MealOut(BaseModel):
    id: UUID
    name: str
    sort_order: int
    is_default: bool


class MealCreate(BaseModel):
    name: str
    sort_order: Optional[int] = None


class MealPatch(BaseModel):
    name: Optional[str] = None
    sort_order: Optional[int] = None


@router.get("", response_model=list[MealOut])
def list_meals(session: Session = Depends(get_session)) -> list[MealOut]:
    meals = session.execute(select(Meal).order_by(Meal.sort_order)).scalars().all()
    return [MealOut(id=m.id, name=m.name, sort_order=m.sort_order, is_default=m.is_default) for m in meals]


@router.post("", response_model=MealOut, status_code=201)
def create_meal(body: MealCreate, session: Session = Depends(get_session)):
    sort_order = body.sort_order
    if sort_order is None:
        max_order = session.execute(select(func.max(Meal.sort_order))).scalar_one_or_none()
        sort_order = (max_order or 0) + 1

    meal = Meal(name=body.name, sort_order=sort_order, is_default=False)
    session.add(meal)
    session.commit()
    session.refresh(meal)
    return MealOut(id=meal.id, name=meal.name, sort_order=meal.sort_order, is_default=meal.is_default)


@router.delete("/{meal_id}", status_code=204)
def delete_meal(meal_id: UUID, session: Session = Depends(get_session)):
    meal = session.get(Meal, meal_id)
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")

    if meal.is_default:
        raise HTTPException(status_code=422, detail="Default meals cannot be deleted")

    has_entries = session.execute(
        select(LogEntry.id).where(LogEntry.meal_id == meal_id).limit(1)
    ).first()
    if has_entries:
        raise HTTPException(status_code=422, detail="Cannot delete a meal with existing log entries")

    session.delete(meal)
    session.commit()


@router.patch("/{meal_id}", response_model=MealOut)
def update_meal(meal_id: UUID, body: MealPatch, session: Session = Depends(get_session)):
    meal = session.get(Meal, meal_id)
    if meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")

    if "name" in body.model_fields_set:
        meal.name = body.name
    if "sort_order" in body.model_fields_set:
        meal.sort_order = body.sort_order

    session.commit()
    session.refresh(meal)
    return MealOut(id=meal.id, name=meal.name, sort_order=meal.sort_order, is_default=meal.is_default)
