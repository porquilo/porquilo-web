from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlmodel import Session, select

from porquilo.models import Food, FoodNutrient, FoodSource, NutrientDefinition, SyncLog
from porquilo.services.settings_service import get_setting

logger = logging.getLogger(__name__)

# DEMO_KEY is rate-limited to ~3 req/min. Free personal key available at api.nal.usda.gov.
_USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

USDA_NUTRIENT_MAP: dict[int, str] = {
    1008: "calories_kcal",
    1003: "protein_g",
    1005: "carbs_g",
    1004: "fat_g",
    1079: "fiber_g",
    2000: "sugar_g",
    1093: "sodium_mg",
    1258: "saturated_fat_g",
    1253: "cholesterol_mg",
    1092: "potassium_mg",
    1106: "vitamin_a_mcg",
    1162: "vitamin_c_mg",
    1114: "vitamin_d_mcg",
    1109: "vitamin_e_mg",
    1185: "vitamin_k_mcg",
    1165: "thiamin_mg",
    1166: "riboflavin_mg",
    1167: "niacin_mg",
    1175: "vitamin_b6_mg",
    1177: "folate_mcg",
    1178: "vitamin_b12_mcg",
    1087: "calcium_mg",
    1089: "iron_mg",
    1090: "magnesium_mg",
    1091: "phosphorus_mg",
    1095: "zinc_mg",
    1103: "selenium_mcg",
}

TOTAL_TRACKED_NUTRIENTS = 27

# Populated on first use; avoids N+1 SELECT per upsert call.
_nutrient_id_cache: dict[str, uuid.UUID] = {}


def _resolve_api_key(session: Session) -> str:
    return get_setting("usda_api_key", session) or os.environ.get("USDA_API_KEY") or "DEMO_KEY"


def _get_nutrient_id(key: str, session: Session) -> Optional[uuid.UUID]:
    if key not in _nutrient_id_cache:
        nd = session.execute(
            select(NutrientDefinition).where(NutrientDefinition.key == key)
        ).scalars().first()
        if nd is None:
            return None
        _nutrient_id_cache[key] = nd.id
    return _nutrient_id_cache[key]


def search_usda(query: str, session: Session, page_size: int = 10) -> list[dict]:
    api_key = _resolve_api_key(session)
    try:
        response = httpx.get(
            _USDA_SEARCH_URL,
            params={
                "query": query,
                "pageSize": page_size,
                "api_key": api_key,
                "dataType": ["Foundation", "Branded"],
            },
            timeout=8.0,
        )
    except httpx.TimeoutException:
        logger.warning("USDA search timed out for query %r", query)
        return []

    if response.status_code != 200:
        logger.warning("USDA search returned %d for query %r", response.status_code, query)
        return []

    try:
        return response.json().get("foods", [])
    except ValueError:
        logger.warning(
            "USDA search returned non-JSON body (status %d) for query %r",
            response.status_code,
            query,
        )
        return []


def upsert_usda_food(usda_food: dict, session: Session) -> Food:
    usda_source = session.execute(
        select(FoodSource).where(FoodSource.key == "usda")
    ).scalars().first()

    fdc_id = str(usda_food["fdcId"])
    existing = session.execute(
        select(Food).where(
            Food.food_source_id == usda_source.id,
            Food.external_source_id == fdc_id,
        )
    ).scalars().first()

    now = datetime.now(timezone.utc)
    brand = usda_food.get("brandOwner") or usda_food.get("brandName")

    # Parse nutrients first so source_completeness is ready before the food row is written.
    found_nutrients: list[tuple[str, float]] = []
    for n in usda_food.get("foodNutrients", []):
        try:
            nutrient_number = int(n.get("nutrientNumber") or 0)
        except (ValueError, TypeError):
            continue
        mapped_key = USDA_NUTRIENT_MAP.get(nutrient_number)
        if mapped_key is None:
            continue
        value = n.get("value")
        if value is None:
            continue
        found_nutrients.append((mapped_key, float(value)))

    source_completeness = round(len(found_nutrients) / TOTAL_TRACKED_NUTRIENTS, 4)

    is_insert = existing is None
    if is_insert:
        food = Food(
            name=usda_food["description"],
            brand=brand,
            food_source_id=usda_source.id,
            external_source_id=fdc_id,
            created_at=now,
            updated_at=now,
            source_fetched_at=now,
            source_completeness=source_completeness,
        )
        session.add(food)
        session.flush()
    else:
        food = existing
        food.name = usda_food["description"]
        food.brand = brand
        food.updated_at = now
        food.source_fetched_at = now
        food.source_completeness = source_completeness

    for mapped_key, value in found_nutrients:
        nutrient_id = _get_nutrient_id(mapped_key, session)
        if nutrient_id is None:
            continue
        fn = session.execute(
            select(FoodNutrient).where(
                FoodNutrient.food_id == food.id,
                FoodNutrient.nutrient_id == nutrient_id,
            )
        ).scalars().first()
        if fn is None:
            session.add(FoodNutrient(food_id=food.id, nutrient_id=nutrient_id, value_per_100=value))
        else:
            fn.value_per_100 = value

    if is_insert:
        session.add(
            SyncLog(
                food_source_id=usda_source.id,
                completed_at=now,
                record_count=1,
                duration_seconds=0.0,
                notes="usda_search_cache",
            )
        )

    return food
