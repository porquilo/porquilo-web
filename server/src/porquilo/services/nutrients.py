from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session
from sqlmodel import select

from porquilo.models.food_nutrient import FoodNutrient


def compute_nutrients(food_id: UUID, weight_g: Decimal, session: Session) -> dict:
    rows = session.execute(select(FoodNutrient).where(FoodNutrient.food_id == food_id)).scalars().all()
    result = {}
    for row in rows:
        scaled = row.value_per_100 * weight_g / Decimal("100")
        result[row.nutrient_id] = {"value": scaled, "coverage": "full"}
    return result


def derive_confidence(weight_source: str) -> str:
    if weight_source in ("scale", "recipe_derived"):
        return "measured"
    return "estimated"
