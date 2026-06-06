from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional, TypedDict
from uuid import UUID

from sqlmodel import Session, select

from porquilo.models import Food, FoodNutrient, FoodSource, FoodVariant, NutrientDefinition


class NutrientValue(TypedDict):
    value_per_100: Decimal
    is_overridden: bool


class FoodRecord(TypedDict):
    id: UUID
    name: str
    brand: Optional[str]
    barcode: Optional[str]
    source_key: str
    external_source_id: Optional[str]
    default_unit: str
    source_fetched_at: Optional[datetime]
    source_completeness: Optional[float]
    nutrients: dict[str, NutrientValue]
    variants: list[dict[str, Any]]
    overrides: dict[str, Any]
    is_contributable: bool


def get_food_with_overrides(food_id: UUID, session: Session) -> Optional[FoodRecord]:
    """
    Canonical read path for a single food record with applied user overrides.

    STUB: Returns the base food record with an empty overrides dict.
    Override merge logic is implemented in a later session (saveOverride + full merge).

    No code anywhere else in the codebase should query the foods table directly for
    single-food reads. All call sites use this function.
    """
    row = session.execute(
        select(Food, FoodSource)
        .join(FoodSource, Food.food_source_id == FoodSource.id)  # type: ignore[arg-type]
        .where(Food.id == food_id)
    ).first()

    if row is None:
        return None

    food, food_source = row
    source_key: str = food_source.key

    nutrients: dict[str, NutrientValue] = {}
    for fn, nd in session.execute(
        select(FoodNutrient, NutrientDefinition)
        .join(NutrientDefinition, FoodNutrient.nutrient_id == NutrientDefinition.id)  # type: ignore[arg-type]
        .where(FoodNutrient.food_id == food_id)
    ).all():
        nutrients[nd.key] = NutrientValue(value_per_100=fn.value_per_100, is_overridden=False)

    variants: list[dict[str, Any]] = [
        fv.model_dump()
        for fv in session.execute(
            select(FoodVariant).where(FoodVariant.food_id == food_id)
        ).scalars().all()
    ]

    # TODO (Session FD-4): fetch user_overrides rows and merge field-by-field into
    # FoodRecord, setting is_overridden=True on affected NutrientValue entries.

    return FoodRecord(
        id=food.id,
        name=food.name,
        brand=food.brand,
        barcode=food.barcode,
        source_key=source_key,
        external_source_id=food.external_source_id,
        default_unit=food.default_unit,
        source_fetched_at=food.source_fetched_at,
        source_completeness=food.source_completeness,
        nutrients=nutrients,
        variants=variants,
        overrides={},
        is_contributable=(source_key == "open_food_facts"),
    )
