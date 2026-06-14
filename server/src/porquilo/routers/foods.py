from __future__ import annotations

from decimal import Decimal
from typing import Optional
from uuid import UUID

import sqlalchemy as sa
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, model_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from porquilo.core.database import engine, get_session
from porquilo.services.name_normalization import normalize_and_store
from porquilo.services.search_tokens import reindex_food, tokenize
from porquilo.models import (
    Food,
    FoodNutrient,
    FoodSearchToken,
    FoodSource,
    FoodVariant,
    NutrientDefinition,
)
from porquilo.services.food_service import get_food_with_overrides
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
    display_name: Optional[str]
    source: str
    default_unit: str
    nutrients: dict[str, Decimal]
    variants: list[FoodVariantRead]


class FoodPage(BaseModel):
    items: list[FoodRead]
    total: int


VALID_SORT_FIELDS = {"name", "source", "calories", "protein", "fat", "carbs"}
VALID_SORT_DIRS = {"asc", "desc"}
NUTRIENT_SORT_KEYS = {
    "calories": "calories_kcal",
    "protein": "protein_g",
    "fat": "fat_g",
    "carbs": "carbs_g",
}


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
    display_name: Optional[str] = None
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
        display_name=food.display_name,
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
# Background task helpers
# ---------------------------------------------------------------------------


def _bg_normalize(food_id: UUID) -> None:
    """Run normalization with its own session — never reuse the request session."""
    from sqlmodel import Session as _Session  # local import avoids circular at module level

    with _Session(engine) as bg_session:
        normalize_and_store(food_id, bg_session)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get("", response_model=FoodPage)
def search_foods(
    background_tasks: BackgroundTasks,
    q: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="name"),
    sort_dir: str = Query(default="asc"),
    session: Session = Depends(get_session),
) -> FoodPage:
    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(status_code=422, detail=f"Invalid sort_by: {sort_by!r}")
    if sort_dir not in VALID_SORT_DIRS:
        raise HTTPException(status_code=422, detail=f"Invalid sort_dir: {sort_dir!r}")

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

    dir_fn = sa.asc if sort_dir == "asc" else sa.desc

    if sort_by in NUTRIENT_SORT_KEYS:
        nutrient_subq = (
            select(FoodNutrient.food_id, FoodNutrient.value_per_100)
            .join(NutrientDefinition, FoodNutrient.nutrient_id == NutrientDefinition.id)
            .where(NutrientDefinition.key == NUTRIENT_SORT_KEYS[sort_by])
            .subquery()
        )
        base = base.outerjoin(nutrient_subq, nutrient_subq.c.food_id == Food.id)
        sort_clause = sa.nulls_last(dir_fn(nutrient_subq.c.value_per_100))
    elif sort_by == "source":
        sort_clause = dir_fn(FoodSource.key)
    else:
        sort_clause = dir_fn(Food.name)

    token_subq = None
    if q and len(q) >= 2:
        q_tokens = tokenize(q)
        if q_tokens:
            # Prefix-match the last typed token; all earlier tokens must match exactly.
            last_tok = q_tokens[-1]
            earlier_toks = q_tokens[:-1]
            match_subq = (
                select(FoodSearchToken.food_id)
                .where(FoodSearchToken.token.like(f"{last_tok}%"))
            )
            for tok in earlier_toks:
                match_subq = match_subq.where(
                    FoodSearchToken.food_id.in_(
                        select(FoodSearchToken.food_id).where(
                            FoodSearchToken.token == tok
                        )
                    )
                )
            token_subq = match_subq.distinct().subquery()

    if token_subq is not None:
        filtered = base.where(Food.id.in_(select(token_subq.c.food_id)))
    else:
        filtered = base

    stmt = filtered.order_by(sort_clause)

    data_stmt = stmt.offset(offset).limit(limit)

    food_rows = session.execute(data_stmt).all()

    # Two-pass: fill from USDA when local cache doesn't satisfy the request.
    if q and len(q) >= 2 and len(food_rows) < limit:
        usda_results = search_usda(q, session, page_size=limit - len(food_rows))
        if usda_results:
            new_food_ids: list[UUID] = []
            for usda_food in usda_results:
                food, is_new = upsert_usda_food(usda_food, session)
                if is_new:
                    new_food_ids.append(food.id)
            session.commit()
            for fid in new_food_ids:
                reindex_food(fid, session)
            session.commit()
            food_rows = session.execute(data_stmt).all()
            for food_id in new_food_ids:
                background_tasks.add_task(_bg_normalize, food_id)

    count_base = (
        select(sa.func.count())
        .select_from(Food)
        .join(FoodSource, Food.food_source_id == FoodSource.id)
    )
    if source is not None:
        count_base = count_base.where(FoodSource.key == source)
    if token_subq is not None:
        count_base = count_base.where(Food.id.in_(select(token_subq.c.food_id)))
    total = session.execute(count_base).scalar_one()

    if not food_rows:
        return FoodPage(items=[], total=total)

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

    items = [
        FoodRead(
            id=food.id,
            name=food.name,
            brand=food.brand,
            display_name=food.display_name,
            source=source_key,
            default_unit=food.default_unit,
            nutrients=nutrients_by_food.get(food.id, {}),
            variants=variants_by_food.get(food.id, []),
        )
        for food, source_key in food_rows
    ]
    return FoodPage(items=items, total=total)


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
    reindex_food(food.id, session)
    session.commit()
    return _food_out(food, food_source.key, session)


@router.get("/lookup/barcode/{upc}", response_model=FoodOut)
def lookup_food_by_barcode(upc: str, session: Session = Depends(get_session)):
    # C6: barcode lookup — stub until barcode-lookup session is implemented
    raise HTTPException(status_code=501, detail="Barcode lookup not yet implemented")


@router.get("/{food_id}", response_model=FoodOut)
def get_food(food_id: UUID, session: Session = Depends(get_session)):
    record = get_food_with_overrides(food_id, session)
    if record is None:
        raise HTTPException(status_code=404, detail="Food not found")
    return FoodOut(
        id=record["id"],
        name=record["name"],
        brand=record["brand"],
        display_name=None,
        source=record["source_key"],
        default_unit=record["default_unit"],
        nutrients=[
            NutrientOut(nutrient_key=key, value_per_100=val["value_per_100"])
            for key, val in record["nutrients"].items()
        ],
        variants=[
            VariantOut(name=v["name"], amount=v["amount"], unit=v["unit"])
            for v in record["variants"]
        ],
    )
