from __future__ import annotations

import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import duckdb
import openfoodfacts
from sqlmodel import Session, select

from porquilo.models import Food, FoodNutrient, FoodSource, NutrientDefinition

logger = logging.getLogger(__name__)

OFF_NUTRIENT_MAP: dict[str, tuple[str, float]] = {
    # Macros
    "energy-kcal_100g":          ("calories_kcal",          1.0),
    "proteins_100g":             ("protein_g",               1.0),
    "carbohydrates_100g":        ("carbs_g",                 1.0),
    "fat_100g":                  ("fat_g",                   1.0),
    "fiber_100g":                ("fiber_g",                 1.0),
    "sugars_100g":               ("sugar_g",                 1.0),
    "saturated-fat_100g":        ("saturated_fat_g",         1.0),
    "sodium_100g":               ("sodium_mg",               1000.0),
    "potassium_100g":            ("potassium_mg",            1000.0),
    # Additional fats (seeded in FD-S1b)
    "cholesterol_100g":          ("cholesterol_mg",          1000.0),
    "trans-fat_100g":            ("trans_fat_g",             1.0),
    "monounsaturated-fat_100g":  ("monounsaturated_fat_g",   1.0),
    "polyunsaturated-fat_100g":  ("polyunsaturated_fat_g",   1.0),
    # Minerals
    "calcium_100g":              ("calcium_mg",              1000.0),
    "iron_100g":                 ("iron_mg",                 1000.0),
    "magnesium_100g":            ("magnesium_mg",            1000.0),
    "phosphorus_100g":           ("phosphorus_mg",           1000.0),
    "zinc_100g":                 ("zinc_mg",                 1000.0),
    # Vitamins — keys match nutrient_definitions seed exactly
    "vitamin-a_100g":            ("vitamin_a_mcg",           1_000_000.0),
    "vitamin-c_100g":            ("vitamin_c_mg",            1000.0),
    "vitamin-d_100g":            ("vitamin_d_mcg",           1_000_000.0),
    "vitamin-e_100g":            ("vitamin_e_mg",            1000.0),
    "vitamin-b1_100g":           ("thiamin_mg",              1000.0),
    "vitamin-b2_100g":           ("riboflavin_mg",           1000.0),
    "vitamin-pp_100g":           ("niacin_mg",               1000.0),
    "vitamin-b6_100g":           ("vitamin_b6_mg",           1000.0),
    "vitamin-b12_100g":          ("vitamin_b12_mcg",         1_000_000.0),
    "folates_100g":              ("folate_mcg",              1_000_000.0),
}

NUTRIENT_GROUPS: dict[str, set[str]] = {
    "macros": {
        "energy-kcal_100g", "proteins_100g", "carbohydrates_100g",
        "fat_100g", "fiber_100g", "sugars_100g",
        "saturated-fat_100g", "sodium_100g", "potassium_100g",
    },
    "additional_fats": {
        "cholesterol_100g", "trans-fat_100g",
        "monounsaturated-fat_100g", "polyunsaturated-fat_100g",
    },
    "minerals": {
        "calcium_100g", "iron_100g", "magnesium_100g",
        "phosphorus_100g", "zinc_100g",
    },
    "vitamins": {
        "vitamin-a_100g", "vitamin-c_100g", "vitamin-d_100g",
        "vitamin-e_100g", "vitamin-b1_100g", "vitamin-b2_100g",
        "vitamin-pp_100g", "vitamin-b6_100g", "vitamin-b12_100g",
        "folates_100g",
    },
}

_TOTAL_NUTRIENTS = len(OFF_NUTRIENT_MAP)

# Pre-computed reverse map: OFF CSV column → group name.
_OFF_COL_TO_GROUP: dict[str, str] = {
    col: group
    for group, cols in NUTRIENT_GROUPS.items()
    for col in cols
}

# Populated on first use; avoids N+1 SELECT per upsert call.
_nutrient_id_cache: dict[str, uuid.UUID] = {}


def _get_nutrient_id(key: str, session: Session) -> Optional[uuid.UUID]:
    if key not in _nutrient_id_cache:
        nd = session.execute(
            select(NutrientDefinition).where(NutrientDefinition.key == key)
        ).scalars().first()
        if nd is None:
            return None
        _nutrient_id_cache[key] = nd.id
    return _nutrient_id_cache[key]


def _cache_dir() -> Path:
    base = os.environ.get("OFF_CACHE_DIR") or (Path.home() / ".cache" / "porquilo" / "off")
    path = Path(base)
    path.mkdir(parents=True, exist_ok=True)
    return path


def download_off_dataset() -> Path:
    """Download the OFF bulk CSV export if not already cached for today."""
    cache = _cache_dir()
    today = datetime.now(timezone.utc).date()
    # The SDK downloads a gzip-compressed CSV; DuckDB reads .gz natively.
    stamped = cache / f"off_{today}.csv.gz"
    if stamped.exists():
        logger.info("OFF dataset already cached for today: %s", stamped)
        return stamped

    logger.info("Downloading OFF dataset …")
    # get_dataset returns the path of the (cached) downloaded file.
    src = openfoodfacts.get_dataset(
        flavor=openfoodfacts.Flavor.off,
        dataset_type=openfoodfacts.DatasetType.csv,
    )
    shutil.copy(src, stamped)
    logger.info("OFF dataset ready: %s", stamped)
    return stamped


def import_off_dataset(session: Session) -> int:
    """
    Full import pipeline. Returns count of rows upserted.
    Called by the background task — commits in batches of 500.
    """
    csv_path = download_off_dataset()

    off_source: FoodSource = session.execute(
        select(FoodSource).where(FoodSource.key == "open_food_facts")
    ).scalars().first()

    off_source.sync_status = "running"
    off_source.sync_error = None
    session.commit()

    nutrient_cols = ", ".join(f'"{c}"' for c in OFF_NUTRIENT_MAP)
    query = f"""
        SELECT code, product_name, brands, {nutrient_cols}
        FROM read_csv(
            '{str(csv_path)}',
            header = true,
            sep = '\t',
            quote = '',
            ignore_errors = true
        )
        WHERE product_name IS NOT NULL AND product_name != ''
    """

    total = 0
    logger.info("OFF import started")
    try:
        with duckdb.connect() as con:
            rel = con.execute(query)
            col_names = [desc[0] for desc in rel.description]

            batch = rel.fetchmany(500)
            while batch:
                now = datetime.now(timezone.utc)
                for raw_row in batch:
                    row = dict(zip(col_names, raw_row))
                    _upsert_off_row(row, off_source, session, now)
                    total += 1

                session.commit()
                off_source.last_synced_at = datetime.now(timezone.utc)
                session.commit()

                if total % 50_000 == 0:
                    logger.info("OFF import progress: %d rows upserted", total)

                batch = rel.fetchmany(500)

        off_source.sync_status = "succeeded"
        off_source.last_synced_at = datetime.now(timezone.utc)
        session.commit()
        logger.info("OFF import complete: %d rows upserted", total)
        return total

    except Exception as e:
        logger.exception("OFF import failed after %d rows", total)
        off_source.sync_status = "failed"
        off_source.sync_error = str(e)
        try:
            session.commit()
        except Exception:
            pass
        raise


def _upsert_off_row(
    row: dict,
    off_source: FoodSource,
    session: Session,
    now: datetime,
) -> None:
    code = row.get("code")
    if not code:
        return

    # Parse nutrients, apply unit multipliers, track per-group presence.
    valid_nutrients: dict[str, float] = {}
    group_present: dict[str, int] = {g: 0 for g in NUTRIENT_GROUPS}

    for off_col, (porq_key, multiplier) in OFF_NUTRIENT_MAP.items():
        raw = row.get(off_col)
        if raw is None:
            continue
        try:
            value = float(raw) * multiplier
        except (TypeError, ValueError):
            continue
        valid_nutrients[porq_key] = value
        group = _OFF_COL_TO_GROUP.get(off_col)
        if group:
            group_present[group] += 1

    def _score(group: str) -> float:
        return round(group_present[group] / len(NUTRIENT_GROUPS[group]), 4)

    source_completeness = round(len(valid_nutrients) / _TOTAL_NUTRIENTS, 4)
    macro_completeness = _score("macros")
    fat_completeness = _score("additional_fats")
    mineral_completeness = _score("minerals")
    vitamin_completeness = _score("vitamins")

    name = (row.get("product_name") or "").strip()
    brand = (row.get("brands") or "").strip() or None
    barcode = str(code).strip()

    existing = session.execute(
        select(Food).where(
            Food.food_source_id == off_source.id,
            Food.external_source_id == barcode,
        )
    ).scalars().first()

    if existing is None:
        food = Food(
            name=name,
            brand=brand,
            barcode=barcode,
            food_source_id=off_source.id,
            external_source_id=barcode,
            created_at=now,
            updated_at=now,
            source_fetched_at=now,
            source_completeness=source_completeness,
            macro_completeness=macro_completeness,
            fat_completeness=fat_completeness,
            mineral_completeness=mineral_completeness,
            vitamin_completeness=vitamin_completeness,
            display_name_status="pending",
        )
        session.add(food)
        session.flush()
    else:
        food = existing
        food.name = name
        food.brand = brand
        food.updated_at = now
        food.source_fetched_at = now
        food.source_completeness = source_completeness
        food.macro_completeness = macro_completeness
        food.fat_completeness = fat_completeness
        food.mineral_completeness = mineral_completeness
        food.vitamin_completeness = vitamin_completeness

    for porq_key, value in valid_nutrients.items():
        nutrient_id = _get_nutrient_id(porq_key, session)
        if nutrient_id is None:
            continue
        fn = session.execute(
            select(FoodNutrient).where(
                FoodNutrient.food_id == food.id,
                FoodNutrient.nutrient_id == nutrient_id,
            )
        ).scalars().first()
        if fn is None:
            session.add(
                FoodNutrient(food_id=food.id, nutrient_id=nutrient_id, value_per_100=value)
            )
        else:
            fn.value_per_100 = value
