# Run against SQLite (default, no setup required):
#   pytest server/tests/test_api_foods.py
#
# Run against PostgreSQL:
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost/porquilo_test \
#     pytest server/tests/test_api_foods.py

CALORIES_ONLY = {
    "name": "Plain Rice",
    "nutrients": [{"nutrient_key": "calories_kcal", "value_per_100": "130.0"}],
}

FULL_PAYLOAD = {
    "name": "Cheddar Cheese",
    "brand": "Tillamook",
    "barcode": "041800001234",
    "source": "custom",
    "source_id": "cheese-001",
    "default_unit": "g",
    "nutrients": [
        {"nutrient_key": "calories_kcal", "value_per_100": "403"},
        {"nutrient_key": "protein_g", "value_per_100": "25"},
        {"nutrient_key": "fat_g", "value_per_100": "33"},
        {"nutrient_key": "carbs_g", "value_per_100": "1.3"},
    ],
    "variants": [
        {"name": "1 oz slice", "amount": "28.35", "unit": "g"},
        {"name": "1 cup shredded", "amount": "113", "unit": "g"},
    ],
}


def test_basic_food_calories_only(client):
    resp = client.post("/api/foods", json=CALORIES_ONLY)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Plain Rice"
    assert data["source"] == "custom"
    assert data["default_unit"] == "g"
    assert len(data["nutrients"]) == 1
    assert data["nutrients"][0]["nutrient_key"] == "calories_kcal"
    assert data["variants"] == []
    assert "id" in data


def test_full_food_with_nutrients_and_variants(client):
    resp = client.post("/api/foods", json=FULL_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Cheddar Cheese"
    assert data["brand"] == "Tillamook"
    assert data["source"] == "custom"
    nutrient_keys = {n["nutrient_key"] for n in data["nutrients"]}
    assert {"calories_kcal", "protein_g", "fat_g", "carbs_g"} == nutrient_keys
    assert len(data["variants"]) == 2


def test_liquid_food_default_unit_ml(client):
    payload = {
        "name": "Whole Milk",
        "default_unit": "ml",
        "nutrients": [{"nutrient_key": "calories_kcal", "value_per_100": "61"}],
    }
    resp = client.post("/api/foods", json=payload)
    assert resp.status_code == 201
    assert resp.json()["default_unit"] == "ml"


def test_unknown_source_returns_422(client):
    payload = {
        "name": "Ghost Food",
        "source": "nonexistent_source",
        "nutrients": [{"nutrient_key": "calories_kcal", "value_per_100": "100"}],
    }
    resp = client.post("/api/foods", json=payload)
    assert resp.status_code == 422


def test_unknown_nutrient_key_returns_422(client):
    payload = {
        "name": "Bad Nutrient Food",
        "nutrients": [
            {"nutrient_key": "calories_kcal", "value_per_100": "100"},
            {"nutrient_key": "made_up_nutrient", "value_per_100": "5"},
        ],
    }
    resp = client.post("/api/foods", json=payload)
    assert resp.status_code == 422


def test_missing_calories_returns_422(client):
    payload = {
        "name": "No Calories Food",
        "nutrients": [{"nutrient_key": "protein_g", "value_per_100": "20"}],
    }
    resp = client.post("/api/foods", json=payload)
    assert resp.status_code == 422


def test_duplicate_barcode_returns_422(client):
    payload = {
        "name": "First Bar",
        "barcode": "000000000001",
        "nutrients": [{"nutrient_key": "calories_kcal", "value_per_100": "100"}],
    }
    resp = client.post("/api/foods", json=payload)
    assert resp.status_code == 201

    payload["name"] = "Second Bar"
    resp = client.post("/api/foods", json=payload)
    assert resp.status_code == 422


def test_duplicate_source_source_id_returns_422(client):
    payload = {
        "name": "USDA Apple",
        "source": "usda",
        "source_id": "FDC-APPLE-001",
        "nutrients": [{"nutrient_key": "calories_kcal", "value_per_100": "52"}],
    }
    resp = client.post("/api/foods", json=payload)
    assert resp.status_code == 201

    payload["name"] = "USDA Apple Duplicate"
    resp = client.post("/api/foods", json=payload)
    assert resp.status_code == 422


def test_atomic_rollback_on_unknown_nutrient(client):
    """Partial failure: unknown nutrient_key returns 422, no food is persisted."""
    payload = {
        "name": "Rollback Food",
        "nutrients": [
            {"nutrient_key": "calories_kcal", "value_per_100": "100"},
            {"nutrient_key": "nonexistent_key", "value_per_100": "1"},
        ],
    }
    resp = client.post("/api/foods", json=payload)
    assert resp.status_code == 422
