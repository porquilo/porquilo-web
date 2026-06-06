import sqlalchemy as sa
from sqlmodel import SQLModel

import porquilo.models  # noqa: F401 — registers all tables with SQLModel.metadata

EXPECTED_COLUMNS = {
    "nutrient_definitions": {"id", "key", "display_name", "unit", "sort_order", "created_at"},
    "meals": {"id", "name", "sort_order", "is_default", "created_at"},
    "tracked_nutrients": {
        "id", "nutrient_id", "display_order",
        "show_in_diary", "show_in_goals", "show_in_charts", "created_at",
    },
    "food_sources": {
        "id", "key", "display_name", "is_active",
        "last_synced_at", "sync_status", "sync_error", "created_at", "updated_at",
    },
    "foods": {
        "id", "name", "brand", "barcode",
        "food_source_id", "external_source_id", "default_unit", "created_at", "updated_at",
        "source_fetched_at", "source_completeness",
    },
    "food_nutrients": {"id", "food_id", "nutrient_id", "value_per_100"},
    "food_variants": {"id", "food_id", "name", "amount", "unit", "created_at"},
    "log_entries": {
        "id", "food_id", "recipe_id", "meal_id", "eaten_at", "logged_at",
        "weight_g", "weight_source", "weight_confidence", "input_method", "created_at",
    },
    "log_entry_nutrients": {"id", "log_entry_id", "nutrient_id", "value", "coverage"},
    "meal_skips": {"id", "meal_id", "skipped_on", "created_at"},
    "recipes": {
        "id", "name", "total_yield_g", "yield_estimated", "servings",
        "yield_description", "notes", "source", "source_id", "created_at", "updated_at",
    },
    "recipe_ingredients": {"id", "recipe_id", "food_id", "nested_recipe_id", "weight_g"},
    "goals": {"id", "calorie_mode", "calorie_target", "calorie_factor", "effective_from", "created_at"},
    "goal_nutrients": {"id", "goal_id", "nutrient_id", "target_value"},
    "body_metrics": {"id", "metric_type", "value", "measured_at", "source", "created_at"},
    "user_overrides": {
        "id", "food_id", "field", "nutrient_id", "original_value",
        "corrected_value", "corrected_at", "contributed_at", "contribution_status",
    },
    "sync_log": {
        "id", "food_source_id", "completed_at",
        "record_count", "duration_seconds", "file_hash", "notes",
    },
}


def test_model_columns_match_db(engine_009):
    inspector = sa.inspect(engine_009)

    for table_name, expected in EXPECTED_COLUMNS.items():
        db_cols = {col["name"] for col in inspector.get_columns(table_name)}
        declared_cols = set(SQLModel.metadata.tables[table_name].columns.keys())

        assert db_cols == expected, (
            f"{table_name}: DB columns {sorted(db_cols)} != expected {sorted(expected)}"
        )
        assert declared_cols == expected, (
            f"{table_name}: model columns {sorted(declared_cols)} != expected {sorted(expected)}"
        )
