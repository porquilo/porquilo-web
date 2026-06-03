from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models import Food, FoodNutrient, FoodSource, FoodVariant, NutrientDefinition

router = APIRouter(prefix="/api/foods", tags=["foods"])


class FoodVariantRead(BaseModel):
    id: UUID
    name: Optional[str]
    amount: Optional[Decimal]
    unit: str


class FoodRead(BaseModel):
    id: UUID
    name: str
    brand: Optional[str]
    source: str
    default_unit: str
    nutrients: dict[str, Decimal]
    variants: list[FoodVariantRead]


@router.get("", response_model=list[FoodRead])
def search_foods(
    q: str = Query(min_length=2),
    source: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=50),
    session: Session = Depends(get_session),
) -> list[FoodRead]:
    q_lower = q.lower()

    has_nutrients = sa.exists(
        select(FoodNutrient.id).where(FoodNutrient.food_id == Food.id).correlate(Food)
    )

    stmt = (
        select(Food, FoodSource.key.label("source_key"))
        .join(FoodSource, Food.food_source_id == FoodSource.id)
        .where(
            sa.or_(
                Food.name.ilike(f"%{q}%"),
                Food.brand.ilike(f"%{q}%"),
            )
        )
        .where(has_nutrients)
    )

    if source is not None:
        stmt = stmt.where(FoodSource.key == source)

    order_expr = sa.case(
        (sa.func.lower(Food.name) == q_lower, 0),
        (sa.func.lower(Food.name).like(f"{q_lower}%"), 1),
        else_=2,
    )
    stmt = stmt.order_by(order_expr).limit(limit)

    food_rows = session.execute(stmt).all()
    if not food_rows:
        return []

    food_ids = [row[0].id for row in food_rows]

    nutrients_by_food: dict[uuid.UUID, dict[str, Decimal]] = {}
    for fn, nd in session.execute(
        select(FoodNutrient, NutrientDefinition)
        .join(NutrientDefinition, FoodNutrient.nutrient_id == NutrientDefinition.id)
        .where(FoodNutrient.food_id.in_(food_ids))
    ).all():
        nutrients_by_food.setdefault(fn.food_id, {})[nd.key] = fn.value_per_100

    variants_by_food: dict[uuid.UUID, list[FoodVariantRead]] = {}
    for fv in session.execute(
        select(FoodVariant).where(FoodVariant.food_id.in_(food_ids))
    ).scalars():
        variants_by_food.setdefault(fv.food_id, []).append(
            FoodVariantRead(id=fv.id, name=fv.name, amount=fv.amount, unit=fv.unit)
        )

    return [
        FoodRead(
            id=food.id,
            name=food.name,
            brand=food.brand,
            source=source_key,
            default_unit=food.default_unit,
            nutrients=nutrients_by_food.get(food.id, {}),
            variants=variants_by_food.get(food.id, []),
        )
        for food, source_key in food_rows
    ]
