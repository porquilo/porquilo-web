import uuid
from datetime import datetime, timezone
from decimal import Decimal

import sqlalchemy as sa

_NOW = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)


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


def test_partial_name_match(client, db_session):
    fid = _insert_food(db_session, name="Apple Juice")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "apple"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Apple Juice"


def test_case_insensitive_name(client, db_session):
    fid = _insert_food(db_session, name="Broccoli Florets")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "BROCCOLI"})
    assert resp.status_code == 200
    assert any(f["name"] == "Broccoli Florets" for f in resp.json())


def test_brand_match(client, db_session):
    fid = _insert_food(db_session, name="Orange Juice", brand="Tropicana")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "tropicana"})
    assert resp.status_code == 200
    assert any(f["name"] == "Orange Juice" for f in resp.json())


def test_source_filter_matched_against_key(client, db_session):
    """source param filters against food_sources.key, not a column on foods."""
    fid_c = _insert_food(db_session, name="Custom Salad", source_key="custom")
    _add_nutrient(db_session, fid_c)

    fid_u = _insert_food(db_session, name="USDA Salad", source_key="usda")
    _add_nutrient(db_session, fid_u)

    resp = client.get("/api/foods", params={"q": "salad", "source": "custom"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["source"] == "custom"
    assert data[0]["name"] == "Custom Salad"


def test_source_filter_returns_key_string_not_uuid(client, db_session):
    fid = _insert_food(db_session, name="USDA Chicken", source_key="usda")
    _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "chicken", "source": "usda"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    # source must be the string key "usda", not a UUID
    assert data[0]["source"] == "usda"
    try:
        uuid.UUID(data[0]["source"])
        assert False, "source should be a key string, not a UUID"
    except ValueError:
        pass


def test_min_length_2_enforced(client):
    resp = client.get("/api/foods", params={"q": "a"})
    assert resp.status_code == 422


def test_missing_q_returns_422(client):
    resp = client.get("/api/foods")
    assert resp.status_code == 422


def test_foods_without_nutrients_excluded(client, db_session):
    fid_with = _insert_food(db_session, name="Banana")
    _add_nutrient(db_session, fid_with)

    _insert_food(db_session, name="Banana Split")  # no nutrients

    resp = client.get("/api/foods", params={"q": "banana"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["name"] == "Banana"


def test_limit_respected(client, db_session):
    for i in range(5):
        fid = _insert_food(db_session, name=f"Lime Product {i}")
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "lime", "limit": 3})
    assert resp.status_code == 200
    assert len(resp.json()) == 3


def test_limit_default_20(client, db_session):
    for i in range(25):
        fid = _insert_food(db_session, name=f"Grape Item {i:02d}")
        _add_nutrient(db_session, fid)

    resp = client.get("/api/foods", params={"q": "grape"})
    assert resp.status_code == 200
    assert len(resp.json()) == 20


def test_limit_max_50_enforced(client):
    resp = client.get("/api/foods", params={"q": "test", "limit": 51})
    assert resp.status_code == 422


def test_response_model_shape(client, db_session):
    fid = _insert_food(db_session, name="Brown Rice", brand="Generic")
    _add_nutrient(db_session, fid, nutrient_key="calories_kcal", value=360.0)
    _add_nutrient(db_session, fid, nutrient_key="protein_g", value=7.5)
    _add_variant(db_session, fid, name="1 cup cooked", amount=200.0, unit="g")

    resp = client.get("/api/foods", params={"q": "brown rice"})
    assert resp.status_code == 200
    data = resp.json()
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
    names = [f["name"] for f in resp.json()]
    assert names.index("mango") < names.index("mango smoothie")
    assert names.index("mango smoothie") < names.index("tropical mango blend")


def test_no_results_returns_empty_list(client, db_session):
    resp = client.get("/api/foods", params={"q": "zzz_no_such_food"})
    assert resp.status_code == 200
    assert resp.json() == []
