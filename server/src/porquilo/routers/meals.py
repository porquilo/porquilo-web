from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, func, select

from porquilo.core.database import get_session
from porquilo.models import Meal

router = APIRouter(prefix="/api/meals", tags=["meals"])


class MealOut(BaseModel):
    id: UUID
    name: str
    sort_order: int
    is_default: bool


class MealCreate(BaseModel):
    name: str
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
