from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter(prefix="/api/foods", tags=["foods"])


# ---------------------------------------------------------------------------
# Request models
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
# Response models
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


@router.post("", response_model=FoodOut, status_code=201)
def create_food(body: FoodCreate, session: Session = Depends(get_session)):
    # 1. Resolve food source
    food_source = session.execute(
        select(FoodSource).where(FoodSource.key == body.source)
    ).scalars().first()
    if not food_source:
        raise HTTPException(status_code=422, detail=f"Unknown source: {body.source!r}")

    # 2. Resolve all nutrient keys up front; fail early on any unknown key
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

    # 3-6. Insert Food, FoodNutrient rows, FoodVariant rows — commit atomically
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
