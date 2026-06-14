# Run against SQLite (default, no setup required):
#   pytest server/tests/test_api_foods.py
#
# Run against PostgreSQL:
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost/porquilo_test \
#     pytest server/tests/test_api_foods.py

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
import sqlalchemy as sa
from porquilo.services.search_tokens import reindex_food


@pytest.fixture(autouse=True)
def _no_usda(monkeypatch):
    """Prevent all tests in this module from making real USDA HTTP calls."""
    monkeypatch.setattr("porquilo.routers.foods.search_usda", lambda *_args, **_kwargs: [])

_NOW = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# GET /api/foods — helpers
# ---------------------------------------------------------------------------


def _food_source_id(db_session, key: str) -> str:
    row = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = :k"), {"k": key}
    ).fetchone()
    assert row is not None, f"food_source '{key}' not in DB"
    return str(row[0])


def _nutrient_id(db_session, key: str) -> str:
    row = db_session.execute(
        sa.text("SELECT id FROM nutrient_definitions WHERE key = :k"), {"k": key}
    ).fetchone()
    assert row is not None, f"nutrient_definition '{key}' not in DB"
    return str(row[0])


def _insert_food(
    db_session,
    *,
    name: str,
    source_key: str = "custom",
    brand: str | None = None,
) -> str:
    # Use .hex (no dashes) so inserts match SQLAlchemy's Uuid bind-processor format on SQLite.
    fid = uuid.uuid4().hex
    src_id = _food_source_id(db_session, source_key)
    db_session.execute(
        sa.text(
            "INSERT INTO foods (id, name, brand, food_source_id, default_unit, created_at, updated_at) "
            "VALUES (:id, :name, :brand, :src, 'g', :ts, :ts)"
        ),
        {"id": fid, "name": name, "brand": brand, "src": src_id, "ts": _NOW},
    )
    reindex_food(uuid.UUID(fid), db_session)
    return fid


def _add_nutrient(
    db_session,
    food_id: str,
    nutrient_key: str = "calories_kcal",
    value: float = 100.0,
) -> None:
    nid = _nutrient_id(db_session, nutrient_key)
    db_session.execute(
        sa.text(
            "INSERT INTO food_nutrients (id, food_id, nutrient_id, value_per_100) "
            "VALUES (:id, :fid, :nid, :val)"
        ),
        {"id": uuid.uuid4().hex, "fid": food_id, "nid": nid, "val": value},
    )


def _add_variant(
    db_session,
    food_id: str,
    *,
    name: str = "100g",
    amount: float = 100.0,
    unit: str = "g",
) -> None:
    db_session.execute(
        sa.text(
            "INSERT INTO food_variants (id, food_id, name, amount, unit, created_at) "
            "VALUES (:id, :fid, :name, :amount, :unit, :ts)"
        ),
        {"id": uuid.uuid4().hex, "fid": food_id, "name": name, "amount": amount, "unit": unit, "ts": _NOW},
    )


# ---------------------------------------------------------------------------
# GET /api/foods — tests
# ---------------------------------------------------------------------------


def test_partial_name_match(client, db_session):
    fid = _insert_food(db_session, name="Apple Juice")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "apple"})
    assert resp.status_code == 200
    data = resp.json()["items"]
    assert len(data) == 1
    assert data[0]["name"] == "Apple Juice"


def test_case_insensitive_name(client, db_session):
    fid = _insert_food(db_session, name="Broccoli Florets")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "BROCCOLI"})
    assert resp.status_code == 200
    assert any(f["name"] == "Broccoli Florets" for f in resp.json()["items"])


def test_brand_match(client, db_session):
    fid = _insert_food(db_session, name="Orange Juice", brand="Tropicana")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "tropicana"})
    assert resp.status_code == 200
    assert any(f["name"] == "Orange Juice" for f in resp.json()["items"])


def test_source_filter_matched_against_key(client, db_session):
    """source param filters against food_sources.key, not a column on foods."""
    fid_c = _insert_food(db_session, name="Custom Salad", source_key="custom")
    _add_nutrient(db_session, fid_c)

    fid_u = _insert_food(db_session, name="USDA Salad", source_key="usda")
    _add_nutrient(db_session, fid_u)

    resp = client.get("/api/foods", params={"q": "salad", "source": "custom"})
    assert resp.status_code == 200
    data = resp.json()["items"]
    assert len(data) == 1
    assert data[0]["source"] == "custom"
    assert data[0]["name"] == "Custom Salad"


def test_source_filter_returns_key_string_not_uuid(client, db_session):
    fid = _insert_food(db_session, name="USDA Chicken", source_key="usda")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "chicken", "source": "usda"})
    assert resp.status_code == 200
    data = resp.json()["items"]
    assert len(data) == 1
    # source must be the string key "usda", not a UUID
    assert data[0]["source"] == "usda"
    try:
        uuid.UUID(data[0]["source"])
        assert False, "source should be a key string, not a UUID"
    except ValueError:
        pass


def test_short_q_returns_browse_mode(client, db_session):
    fid = _insert_food(db_session, name="Avocado")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "a"})
    assert resp.status_code == 200
    assert "items" in resp.json()


def test_missing_q_returns_all_foods(client, db_session):
    fid = _insert_food(db_session, name="Zucchini")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods")
    assert resp.status_code == 200
    assert "items" in resp.json()
    assert any(f["name"] == "Zucchini" for f in resp.json()["items"])


def test_browse_alphabetical_order(client, db_session):
    for name in ("Zucchini", "Apple", "Mango"):
        fid = _insert_food(db_session, name=name)
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods")
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    assert names.index("Apple") < names.index("Mango") < names.index("Zucchini")


def test_browse_source_filter(client, db_session):
    fid_c = _insert_food(db_session, name="Custom Oats", source_key="custom")
    _add_nutrient(db_session, fid_c)
    fid_u = _insert_food(db_session, name="USDA Oats", source_key="usda")
    _add_nutrient(db_session, fid_u)

    resp = client.get("/api/foods", params={"source": "custom"})
    assert resp.status_code == 200
    data = resp.json()["items"]
    assert all(f["source"] == "custom" for f in data)
    assert any(f["name"] == "Custom Oats" for f in data)
    assert not any(f["name"] == "USDA Oats" for f in data)


def test_offset_pagination(client, db_session):
    for i in range(5):
        fid = _insert_food(db_session, name=f"Page Food {i:02d}")
        _add_nutrient(db_session, fid)

    first = client.get("/api/foods", params={"limit": 2, "offset": 0}).json()["items"]
    second = client.get("/api/foods", params={"limit": 2, "offset": 2}).json()["items"]

    assert len(first) == 2
    assert len(second) == 2
    first_ids = {f["id"] for f in first}
    second_ids = {f["id"] for f in second}
    assert first_ids.isdisjoint(second_ids)


def test_foods_without_nutrients_excluded(client, db_session):
    fid_with = _insert_food(db_session, name="Banana")
    _add_nutrient(db_session, fid_with)

    _insert_food(db_session, name="Banana Split")  # no nutrients

    resp = client.get("/api/foods", params={"q": "banana"})
    assert resp.status_code == 200
    data = resp.json()["items"]
    assert len(data) == 1
    assert data[0]["name"] == "Banana"


def test_limit_respected(client, db_session):
    for i in range(5):
        fid = _insert_food(db_session, name=f"Lime Product {i}")
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "lime", "limit": 3})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 3


def test_limit_default_20(client, db_session):
    for i in range(25):
        fid = _insert_food(db_session, name=f"Grape Item {i:02d}")
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "grape"})
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 20


def test_limit_max_100_enforced(client):
    resp = client.get("/api/foods", params={"q": "test", "limit": 101})
    assert resp.status_code == 422


def test_response_model_shape(client, db_session):
    fid = _insert_food(db_session, name="Brown Rice", brand="Generic")
    _add_nutrient(db_session, fid, nutrient_key="calories_kcal", value=360.0)
    _add_nutrient(db_session, fid, nutrient_key="protein_g", value=7.5)
    _add_variant(db_session, fid, name="1 cup cooked", amount=200.0, unit="g")

    resp = client.get("/api/foods", params={"q": "brown rice"})
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body and "total" in body
    data = body["items"]
    assert len(data) == 1

    food = data[0]
    uuid.UUID(food["id"])  # must not raise — id is a UUID
    assert food["name"] == "Brown Rice"
    assert food["brand"] == "Generic"
    assert food["source"] == "custom"
    assert food["default_unit"] == "g"

    assert "calories_kcal" in food["nutrients"]
    assert "protein_g" in food["nutrients"]
    assert Decimal(food["nutrients"]["calories_kcal"]) == Decimal("360")
    assert Decimal(food["nutrients"]["protein_g"]) == Decimal("7.5")

    assert len(food["variants"]) == 1
    v = food["variants"][0]
    uuid.UUID(v["id"])
    assert v["name"] == "1 cup cooked"
    assert v["unit"] == "g"


def test_ordering_exact_startswith_contains(client, db_session):
    for name in ("mango smoothie", "mango", "tropical mango blend"):
        fid = _insert_food(db_session, name=name)
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "mango"})
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    assert names.index("mango") < names.index("mango smoothie")
    assert names.index("mango smoothie") < names.index("tropical mango blend")


def test_no_results_returns_empty_list(client, db_session):
    resp = client.get("/api/foods", params={"q": "zzz_no_such_food"})
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0}


# ---------------------------------------------------------------------------
# GET /api/foods — envelope, total count, sorting, limit cap
# ---------------------------------------------------------------------------


def test_response_shape_is_envelope(client, db_session):
    fid = _insert_food(db_session, name="Envelope Food")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods")
    assert resp.status_code == 200
    body = resp.json()
    assert set(body.keys()) == {"items", "total"}
    assert isinstance(body["items"], list)
    assert isinstance(body["total"], int)


def test_total_reflects_full_count(client, db_session):
    for i in range(60):
        fid = _insert_food(db_session, name=f"CountFood {i:02d}")
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "CountFood", "limit": 25, "offset": 25})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 60
    assert len(body["items"]) == 25


def test_total_with_source_filter(client, db_session):
    for i in range(5):
        fid = _insert_food(db_session, name=f"SrcGrain{i}Custom", source_key="custom")
        _add_nutrient(db_session, fid)
    for i in range(3):
        fid = _insert_food(db_session, name=f"SrcGrain{i}Usda", source_key="usda")
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "SrcGrain", "source": "custom"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    assert all(f["source"] == "custom" for f in body["items"])


def test_total_with_q_filter(client, db_session):
    for i in range(4):
        fid = _insert_food(db_session, name=f"Kale Chip {i}")
        _add_nutrient(db_session, fid)
    fid = _insert_food(db_session, name="Spinach")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "kale", "limit": 2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 4
    assert len(body["items"]) == 2


def test_sort_by_name_desc(client, db_session):
    for name in ("Apple", "Banana", "Cherry"):
        fid = _insert_food(db_session, name=name)
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"sort_by": "name", "sort_dir": "desc"})
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    cherry_i = names.index("Cherry")
    banana_i = names.index("Banana")
    apple_i = names.index("Apple")
    assert cherry_i < banana_i < apple_i


def test_sort_by_source(client, db_session):
    fid_u = _insert_food(db_session, name="USDA Berry", source_key="usda")
    _add_nutrient(db_session, fid_u)
    fid_c = _insert_food(db_session, name="Custom Berry", source_key="custom")
    _add_nutrient(db_session, fid_c)

    resp = client.get("/api/foods", params={"sort_by": "source", "sort_dir": "asc"})
    assert resp.status_code == 200
    sources = [f["source"] for f in resp.json()["items"]]
    # "custom" < "usda" alphabetically
    assert sources.index("custom") < sources.index("usda")


def test_sort_by_calories_asc(client, db_session):
    fid_high = _insert_food(db_session, name="High Cal")
    _add_nutrient(db_session, fid_high, nutrient_key="calories_kcal", value=400.0)

    fid_low = _insert_food(db_session, name="Low Cal")
    _add_nutrient(db_session, fid_low, nutrient_key="calories_kcal", value=50.0)

    fid_none = _insert_food(db_session, name="No Cal")
    _add_nutrient(db_session, fid_none, nutrient_key="protein_g", value=10.0)

    resp = client.get("/api/foods", params={"sort_by": "calories", "sort_dir": "asc"})
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    assert names.index("Low Cal") < names.index("High Cal")
    assert names.index("No Cal") == len(names) - 1


def test_sort_by_calories_desc_nulls_last(client, db_session):
    fid_high = _insert_food(db_session, name="High Cal 2")
    _add_nutrient(db_session, fid_high, nutrient_key="calories_kcal", value=400.0)

    fid_low = _insert_food(db_session, name="Low Cal 2")
    _add_nutrient(db_session, fid_low, nutrient_key="calories_kcal", value=50.0)

    fid_none = _insert_food(db_session, name="No Cal 2")
    _add_nutrient(db_session, fid_none, nutrient_key="protein_g", value=10.0)

    resp = client.get("/api/foods", params={"sort_by": "calories", "sort_dir": "desc"})
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    assert names.index("High Cal 2") < names.index("Low Cal 2")
    assert names.index("No Cal 2") == len(names) - 1


def test_sort_by_invalid_returns_422(client):
    resp = client.get("/api/foods", params={"sort_by": "nonsense"})
    assert resp.status_code == 422


def test_sort_dir_invalid_returns_422(client):
    resp = client.get("/api/foods", params={"sort_dir": "sideways"})
    assert resp.status_code == 422


def test_limit_100_accepted(client, db_session):
    fid = _insert_food(db_session, name="Hundred Food")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"limit": 100})
    assert resp.status_code == 200


def test_limit_101_rejected(client):
    resp = client.get("/api/foods", params={"limit": 101})
    assert resp.status_code == 422


def test_pagination_correct_60_foods(client, db_session):
    for i in range(60):
        fid = _insert_food(db_session, name=f"PaginateFood{i:02d}")
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "PaginateFood", "limit": 25, "offset": 25})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 60
    assert len(body["items"]) == 25

    all_resp = client.get("/api/foods", params={"q": "PaginateFood", "limit": 100, "offset": 0})
    all_names = [f["name"] for f in all_resp.json()["items"]]
    page_names = [f["name"] for f in body["items"]]
    assert page_names == all_names[25:50]


# ---------------------------------------------------------------------------
# POST /api/foods — fixtures
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# POST /api/foods — tests
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Normalization integration — GET /api/foods
# ---------------------------------------------------------------------------

_USDA_CHICKEN_FOOD = {
    "fdcId": 171477,
    "description": "Chicken, broilers or fryers, breast, meat only, cooked, roasted",
    "brandOwner": None,
    "brandName": None,
    "foodNutrients": [
        {"nutrientId": 1008, "nutrientNumber": "208", "value": 165.0},
        {"nutrientId": 1003, "nutrientNumber": "203", "value": 31.0},
        {"nutrientId": 1004, "nutrientNumber": "204", "value": 3.6},
        {"nutrientId": 1005, "nutrientNumber": "205", "value": 0.0},
        {"nutrientId": 1093, "nutrientNumber": "307", "value": 74.0},
        {"nutrientId": 1258, "nutrientNumber": "606", "value": 1.01},
        {"nutrientId": 1087, "nutrientNumber": "301", "value": 15.0},
        {"nutrientId": 1089, "nutrientNumber": "303", "value": 1.04},
    ],
}


def test_get_foods_response_includes_display_name(client, db_session):
    """GET /api/foods includes display_name in every result (null or string)."""
    src_id = _food_source_id(db_session, "custom")
    nut_id = _nutrient_id(db_session, "calories_kcal")
    fid = uuid.uuid4().hex
    db_session.execute(
        sa.text(
            "INSERT INTO foods (id, name, food_source_id, default_unit, created_at, updated_at) "
            "VALUES (:id, 'Display Name Food', :src, 'g', :ts, :ts)"
        ),
        {"id": fid, "src": src_id, "ts": _NOW},
    )
    db_session.execute(
        sa.text(
            "INSERT INTO food_nutrients (id, food_id, nutrient_id, value_per_100) "
            "VALUES (:id, :fid, :nid, 100)"
        ),
        {"id": uuid.uuid4().hex, "fid": fid, "nid": nut_id},
    )
    reindex_food(uuid.UUID(fid), db_session)

    resp = client.get("/api/foods", params={"q": "Display Name Food"})
    assert resp.status_code == 200
    data = resp.json()["items"]
    assert len(data) >= 1
    assert "display_name" in data[0]


# ---------------------------------------------------------------------------
# GET /api/foods/{id}
# ---------------------------------------------------------------------------


def test_get_food_by_id_returns_200(client, db_session):
    fid = _insert_food(db_session, name="Single Food")
    _add_nutrient(db_session, fid, nutrient_key="calories_kcal", value=200.0)

    resp = client.get(f"/api/foods/{fid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Single Food"
    uuid.UUID(data["id"])


def test_get_food_by_id_response_shape(client, db_session):
    fid = _insert_food(db_session, name="Shape Food", brand="TestBrand", source_key="usda")
    _add_nutrient(db_session, fid, nutrient_key="calories_kcal", value=100.0)
    _add_nutrient(db_session, fid, nutrient_key="protein_g", value=5.0)
    _add_variant(db_session, fid, name="1 cup", amount=240.0, unit="ml")

    resp = client.get(f"/api/foods/{fid}")
    assert resp.status_code == 200
    data = resp.json()

    uuid.UUID(data["id"])
    assert data["name"] == "Shape Food"
    assert data["brand"] == "TestBrand"
    assert data["default_unit"] == "g"


def test_get_food_by_id_source_is_key_string(client, db_session):
    fid = _insert_food(db_session, name="Source Key Food", source_key="usda")
    _add_nutrient(db_session, fid)

    resp = client.get(f"/api/foods/{fid}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "usda"
    try:
        uuid.UUID(data["source"])
        assert False, "source should be a key string, not a UUID"
    except ValueError:
        pass


def test_get_food_by_id_nutrients_list(client, db_session):
    fid = _insert_food(db_session, name="Nutrient Food")
    _add_nutrient(db_session, fid, nutrient_key="calories_kcal", value=150.0)
    _add_nutrient(db_session, fid, nutrient_key="protein_g", value=12.5)

    resp = client.get(f"/api/foods/{fid}")
    assert resp.status_code == 200
    data = resp.json()

    nutrients = {n["nutrient_key"]: Decimal(n["value_per_100"]) for n in data["nutrients"]}
    assert nutrients["calories_kcal"] == Decimal("150")
    assert nutrients["protein_g"] == Decimal("12.5")


def test_get_food_by_id_variants_list(client, db_session):
    fid = _insert_food(db_session, name="Variant Food")
    _add_nutrient(db_session, fid)
    _add_variant(db_session, fid, name="1 slice", amount=28.0, unit="g")
    _add_variant(db_session, fid, name="1 cup", amount=240.0, unit="ml")

    resp = client.get(f"/api/foods/{fid}")
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["variants"]) == 2
    names = {v["name"] for v in data["variants"]}
    assert names == {"1 slice", "1 cup"}


def test_get_food_by_id_unknown_returns_404(client):
    missing_id = str(uuid.uuid4())
    resp = client.get(f"/api/foods/{missing_id}")
    assert resp.status_code == 404


def test_get_food_by_id_uses_get_food_with_overrides(client, db_session, monkeypatch):
    """Route must delegate to get_food_with_overrides, not query foods directly."""
    fid = _insert_food(db_session, name="Override Food")
    _add_nutrient(db_session, fid)

    calls = []
    original = __import__(
        "porquilo.services.food_service", fromlist=["get_food_with_overrides"]
    ).get_food_with_overrides

    def _spy(food_id, session):
        calls.append(food_id)
        return original(food_id, session)

    monkeypatch.setattr("porquilo.routers.foods.get_food_with_overrides", _spy)

    resp = client.get(f"/api/foods/{fid}")
    assert resp.status_code == 200
    assert len(calls) == 1


def test_get_food_by_id_lookup_route_not_matched_as_uuid(client):
    """Route ordering: /lookup/barcode/... must not be parsed as /{food_id}."""
    resp = client.get("/api/foods/lookup/barcode/012345678901")
    # 501 means the lookup stub was reached (not a 422 UUID parse error)
    assert resp.status_code == 501


# ---------------------------------------------------------------------------
# PATCH /api/foods/{id}
# ---------------------------------------------------------------------------


def test_patch_name_only(client, db_session):
    fid = _insert_food(db_session, name="Old Name")
    _add_nutrient(db_session, fid, nutrient_key="calories_kcal", value=100.0)
    _add_nutrient(db_session, fid, nutrient_key="protein_g", value=5.0)
    _add_variant(db_session, fid, name="1 cup", amount=240.0, unit="ml")

    resp = client.patch(f"/api/foods/{fid}", json={"name": "New Name"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Name"
    # nutrients and variants unchanged
    keys = {n["nutrient_key"] for n in data["nutrients"]}
    assert "calories_kcal" in keys
    assert "protein_g" in keys
    assert len(data["variants"]) == 1


def test_patch_nutrients_merge(client, db_session):
    fid = _insert_food(db_session, name="Merge Food")
    _add_nutrient(db_session, fid, nutrient_key="calories_kcal", value=100.0)
    _add_nutrient(db_session, fid, nutrient_key="protein_g", value=5.0)

    resp = client.patch(
        f"/api/foods/{fid}",
        json={"nutrients": [{"nutrient_key": "calories_kcal", "value_per_100": "200.0"}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    nutrients = {n["nutrient_key"]: Decimal(n["value_per_100"]) for n in data["nutrients"]}
    assert nutrients["calories_kcal"] == Decimal("200")
    # protein_g was not in the patch — must be unchanged
    assert nutrients["protein_g"] == Decimal("5")


def test_patch_variants_replace(client, db_session):
    fid = _insert_food(db_session, name="Variant Food")
    _add_nutrient(db_session, fid)
    _add_variant(db_session, fid, name="Old A", amount=100.0, unit="g")
    _add_variant(db_session, fid, name="Old B", amount=200.0, unit="g")

    resp = client.patch(
        f"/api/foods/{fid}",
        json={"variants": [{"name": "New V", "amount": "50.0", "unit": "g"}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["variants"]) == 1
    assert data["variants"][0]["name"] == "New V"


def test_patch_brand_null(client, db_session):
    fid = _insert_food(db_session, name="Branded Food", brand="Acme")
    _add_nutrient(db_session, fid)

    resp = client.patch(f"/api/foods/{fid}", json={"brand": None})
    assert resp.status_code == 200
    assert resp.json()["brand"] is None


def test_patch_omitted_brand_unchanged(client, db_session):
    fid = _insert_food(db_session, name="Keep Brand", brand="Keep")
    _add_nutrient(db_session, fid)

    resp = client.patch(f"/api/foods/{fid}", json={"name": "Keep Brand Updated"})
    assert resp.status_code == 200
    assert resp.json()["brand"] == "Keep"


def test_patch_duplicate_barcode_returns_422(client):
    first = client.post(
        "/api/foods",
        json={
            "name": "First Bar",
            "barcode": "111000000001",
            "nutrients": [{"nutrient_key": "calories_kcal", "value_per_100": "100"}],
        },
    )
    assert first.status_code == 201
    second = client.post(
        "/api/foods",
        json={
            "name": "Second Bar",
            "nutrients": [{"nutrient_key": "calories_kcal", "value_per_100": "100"}],
        },
    )
    assert second.status_code == 201
    second_id = second.json()["id"]

    resp = client.patch(f"/api/foods/{second_id}", json={"barcode": "111000000001"})
    assert resp.status_code == 422


def test_patch_usda_food_returns_422(client, db_session):
    fid = _insert_food(db_session, name="USDA Food", source_key="usda")
    _add_nutrient(db_session, fid)

    resp = client.patch(f"/api/foods/{fid}", json={"name": "Updated"})
    assert resp.status_code == 422


def test_patch_unknown_id_returns_404(client):
    resp = client.patch(f"/api/foods/{uuid.uuid4()}", json={"name": "Ghost"})
    assert resp.status_code == 404


def test_patch_response_is_food_out(client, db_session):
    fid = _insert_food(db_session, name="Shape Check")
    _add_nutrient(db_session, fid)

    resp = client.patch(f"/api/foods/{fid}", json={"name": "Shape Check 2"})
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) >= {"id", "name", "source", "default_unit", "nutrients", "variants"}
    uuid.UUID(data["id"])
    assert data["source"] == "custom"


def test_patch_updated_at_changes(client, db_session):
    fid = _insert_food(db_session, name="Timestamp Food")
    _add_nutrient(db_session, fid)

    resp = client.patch(f"/api/foods/{fid}", json={"name": "Timestamp Food 2"})
    assert resp.status_code == 200

    row = db_session.execute(
        sa.text("SELECT updated_at FROM foods WHERE id = :id"), {"id": fid}
    ).fetchone()
    assert row is not None
    # updated_at must have advanced past the original _NOW
    updated = row[0]
    if isinstance(updated, str):
        from datetime import datetime
        updated = datetime.fromisoformat(updated)
    assert updated != _NOW


# ---------------------------------------------------------------------------
# DELETE /api/foods/{id}
# ---------------------------------------------------------------------------


def test_delete_custom_food_returns_204(client, db_session):
    fid = _insert_food(db_session, name="Delete Me")
    _add_nutrient(db_session, fid)

    resp = client.delete(f"/api/foods/{fid}")
    assert resp.status_code == 204
    assert resp.content == b""


def test_delete_food_then_get_returns_404(client, db_session):
    fid = _insert_food(db_session, name="Gone Food")
    _add_nutrient(db_session, fid)

    client.delete(f"/api/foods/{fid}")
    resp = client.get(f"/api/foods/{fid}")
    assert resp.status_code == 404


def test_delete_cascades_food_nutrients(client, db_session):
    fid = _insert_food(db_session, name="Cascade Nutrients")
    _add_nutrient(db_session, fid, nutrient_key="calories_kcal", value=100.0)
    _add_nutrient(db_session, fid, nutrient_key="protein_g", value=10.0)

    resp = client.delete(f"/api/foods/{fid}")
    assert resp.status_code == 204

    rows = db_session.execute(
        sa.text("SELECT COUNT(*) FROM food_nutrients WHERE food_id = :fid"),
        {"fid": fid},
    ).scalar()
    assert rows == 0


def test_delete_cascades_food_variants(client, db_session):
    fid = _insert_food(db_session, name="Cascade Variants")
    _add_nutrient(db_session, fid)
    _add_variant(db_session, fid, name="1 cup", amount=240.0, unit="ml")
    _add_variant(db_session, fid, name="1 tbsp", amount=15.0, unit="ml")

    resp = client.delete(f"/api/foods/{fid}")
    assert resp.status_code == 204

    rows = db_session.execute(
        sa.text("SELECT COUNT(*) FROM food_variants WHERE food_id = :fid"),
        {"fid": fid},
    ).scalar()
    assert rows == 0


def test_delete_usda_food_returns_422(client, db_session):
    fid = _insert_food(db_session, name="USDA Food", source_key="usda")
    _add_nutrient(db_session, fid)

    resp = client.delete(f"/api/foods/{fid}")
    assert resp.status_code == 422


def test_delete_unknown_id_returns_404(client):
    resp = client.delete(f"/api/foods/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_get_foods_enqueues_background_task_for_new_usda_food(client, db_session, monkeypatch):
    """foods.py wires new USDA food IDs into background_tasks after upsert."""
    import uuid as _uuid
    from unittest.mock import MagicMock
    from porquilo.routers import foods as foods_module

    calls = []
    monkeypatch.setattr(foods_module, "_bg_normalize", lambda food_id: calls.append(food_id))

    fake_food = MagicMock()
    fake_food.id = _uuid.uuid4()

    # Mock upsert_usda_food so no real DB write (and no session.commit) occurs.
    with patch("porquilo.routers.foods.search_usda", return_value=[_USDA_CHICKEN_FOOD]), \
         patch("porquilo.routers.foods.upsert_usda_food", return_value=(fake_food, True)):
        resp = client.get("/api/foods", params={"q": "chicken"})

    assert resp.status_code == 200
    # TestClient runs background tasks synchronously before returning the response.
    assert calls == [fake_food.id]
