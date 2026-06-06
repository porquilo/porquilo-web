from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, model_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models import (
    Food,
    FoodNutrient,
    FoodSource,
    FoodVariant,
    NutrientDefinition,
)
from porquilo.services.usda_service import search_usda, upsert_usda_food

router = APIRouter(prefix="/api/foods", tags=["foods"])


# ---------------------------------------------------------------------------
# GET /api/foods — search response models
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# POST /api/foods — request models
# ---------------------------------------------------------------------------


class NutrientIn(BaseModel):
    nutrient_key: str
    value_per_100: Decimal


class VariantIn(BaseModel):
    name: str
    amount: Decimal
    unit: str


class FoodCreate(BaseModel):
    name: str
    brand: Optional[str] = None
    barcode: Optional[str] = None
    source: str = "custom"
    source_id: Optional[str] = None
    default_unit: str = "g"
    nutrients: list[NutrientIn]
    variants: list[VariantIn] = []

    @model_validator(mode="after")
    def calories_required(self) -> "FoodCreate":
        keys = {n.nutrient_key for n in self.nutrients}
        if "calories_kcal" not in keys:
            raise ValueError("nutrients must include calories_kcal")
        return self


# ---------------------------------------------------------------------------
# POST /api/foods — response models
# ---------------------------------------------------------------------------


class NutrientOut(BaseModel):
    nutrient_key: str
    value_per_100: Decimal


class VariantOut(BaseModel):
    name: Optional[str] = None
    amount: Optional[Decimal] = None
    unit: str


class FoodOut(BaseModel):
    id: UUID
    name: str
    brand: Optional[str] = None
    source: str
    default_unit: str
    nutrients: list[NutrientOut]
    variants: list[VariantOut]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _food_out(food: Food, source_key: str, session: Session) -> FoodOut:
    nutrient_rows = session.execute(
        select(FoodNutrient, NutrientDefinition)
        .join(NutrientDefinition, FoodNutrient.nutrient_id == NutrientDefinition.id)
        .where(FoodNutrient.food_id == food.id)
    ).all()

    variant_rows = session.execute(
        select(FoodVariant).where(FoodVariant.food_id == food.id)
    ).scalars().all()

    return FoodOut(
        id=food.id,
        name=food.name,
        brand=food.brand,
        source=source_key,
        default_unit=food.default_unit,
        nutrients=[
            NutrientOut(nutrient_key=nd.key, value_per_100=fn.value_per_100)
            for fn, nd in nutrient_rows
        ],
        variants=[
            VariantOut(name=fv.name, amount=fv.amount, unit=fv.unit)
            for fv in variant_rows
        ],
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("", response_model=list[FoodRead])
def search_foods(
    q: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[FoodRead]:
    has_nutrients = sa.exists(
        select(FoodNutrient.id).where(FoodNutrient.food_id == Food.id).correlate(Food)
    )

    base = (
        select(Food, FoodSource.key.label("source_key"))
        .join(FoodSource, Food.food_source_id == FoodSource.id)
        .where(has_nutrients)
    )

    if source is not None:
        base = base.where(FoodSource.key == source)

    if q and len(q) >= 2:
        q_lower = q.lower()
        stmt = base.where(
            sa.or_(
                Food.name.ilike(f"%{q}%"),
                Food.brand.ilike(f"%{q}%"),
            )
        )
        order_expr = sa.case(
            (sa.func.lower(Food.name) == q_lower, 0),
            (sa.func.lower(Food.name).like(f"{q_lower}%"), 1),
            else_=2,
        )
        stmt = stmt.order_by(order_expr)
    else:
        stmt = base.order_by(Food.name)

    stmt = stmt.offset(offset).limit(limit)

    food_rows = session.execute(stmt).all()

    # Two-pass: fill from USDA when local cache doesn't satisfy the request.
    if q and len(q) >= 2 and len(food_rows) < limit:
        usda_results = search_usda(q, session, page_size=limit - len(food_rows))
        if usda_results:
            for usda_food in usda_results:
                upsert_usda_food(usda_food, session)
            session.commit()
            food_rows = session.execute(stmt).all()

    if not food_rows:
        return []

    food_ids = [row[0].id for row in food_rows]

    nutrients_by_food: dict[UUID, dict[str, Decimal]] = {}
    for fn, nd in session.execute(
        select(FoodNutrient, NutrientDefinition)
        .join(NutrientDefinition, FoodNutrient.nutrient_id == NutrientDefinition.id)
        .where(FoodNutrient.food_id.in_(food_ids))
    ).all():
        nutrients_by_food.setdefault(fn.food_id, {})[nd.key] = fn.value_per_100

    variants_by_food: dict[UUID, list[FoodVariantRead]] = {}
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


@router.post("", response_model=FoodOut, status_code=201)
def create_food(body: FoodCreate, session: Session = Depends(get_session)):
    food_source = session.execute(
        select(FoodSource).where(FoodSource.key == body.source)
    ).scalars().first()
    if not food_source:
        raise HTTPException(status_code=422, detail=f"Unknown source: {body.source!r}")

    nutrient_ids: dict[str, UUID] = {}
    for ni in body.nutrients:
        nd = session.execute(
            select(NutrientDefinition).where(NutrientDefinition.key == ni.nutrient_key)
        ).scalars().first()
        if nd is None:
            raise HTTPException(
                status_code=422, detail=f"Unknown nutrient_key: {ni.nutrient_key!r}"
            )
        nutrient_ids[ni.nutrient_key] = nd.id

    food = Food(
        name=body.name,
        brand=body.brand,
        barcode=body.barcode,
        food_source_id=food_source.id,
        external_source_id=body.source_id,
        default_unit=body.default_unit,
    )
    session.add(food)

    try:
        session.flush()  # assigns food.id; catches barcode / (source, source_id) violations early
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=422,
            detail="Duplicate barcode or (source, source_id) combination",
        )

    for ni in body.nutrients:
        session.add(
            FoodNutrient(
                food_id=food.id,
                nutrient_id=nutrient_ids[ni.nutrient_key],
                value_per_100=ni.value_per_100,
            )
        )

    for vi in body.variants:
        session.add(
            FoodVariant(
                food_id=food.id,
                name=vi.name,
                amount=vi.amount,
                unit=vi.unit,
            )
        )

    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=422, detail="Constraint violation on commit")

    session.refresh(food)
    return _food_out(food, food_source.key, session)
