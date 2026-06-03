from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models import Meal

router = APIRouter(prefix="/api/meals", tags=["meals"])


class MealOut(BaseModel):
    id: UUID
    name: str
    sort_order: int
    is_default: bool


@router.get("", response_model=list[MealOut])
def list_meals(session: Session = Depends(get_session)) -> list[MealOut]:
    meals = session.execute(select(Meal).order_by(Meal.sort_order)).scalars().all()
    return [MealOut(id=m.id, name=m.name, sort_order=m.sort_order, is_default=m.is_default) for m in meals]
