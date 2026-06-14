# Run against SQLite (default, no setup required):
#   pytest server/tests/test_api_entries.py
#
# Run against PostgreSQL:
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost/porquilo_test \
#     pytest server/tests/test_api_entries.py

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import sqlalchemy as sa
from sqlmodel import select

from porquilo.models import LogEntry, LogEntryNutrient

_NOW = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)

# Breakfast meal seeded in migration 001
_BREAKFAST_ID = "7c8c92bd-f6b5-4923-ae42-77d883a70da6"


# ---------------------------------------------------------------------------
# Helpers
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


def _insert_food(db_session, *, name: str = "Test Food", source_key: str = "custom") -> str:
    fid = uuid.uuid4().hex
    src_id = _food_source_id(db_session, source_key)
    db_session.execute(
        sa.text(
            "INSERT INTO foods (id, name, food_source_id, default_unit, created_at, updated_at) "
            "VALUES (:id, :name, :src, 'g', :ts, :ts)"
        ),
        {"id": fid, "name": name, "src": src_id, "ts": _NOW},
    )
    return fid


def _add_nutrient(
    db_session, food_id: str, nutrient_key: str = "calories_kcal", value: float = 100.0
) -> None:
    nid = _nutrient_id(db_session, nutrient_key)
    db_session.execute(
        sa.text(
            "INSERT INTO food_nutrients (id, food_id, nutrient_id, value_per_100) "
            "VALUES (:id, :fid, :nid, :val)"
        ),
        {"id": uuid.uuid4().hex, "fid": food_id, "nid": nid, "val": value},
    )


def _payload(food_id_hex: str, meal_id: str = _BREAKFAST_ID, **overrides) -> dict:
    base = {
        "food_id": str(uuid.UUID(food_id_hex)),
        "meal_id": meal_id,
        "weight_g": "150.0",
        "eaten_at": "2026-06-01T08:00:00",
        "weight_source": "scale",
        "input_method": "manual",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# POST /api/entries
# ---------------------------------------------------------------------------


def test_create_entry_returns_201(client, db_session):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid))

    assert resp.status_code == 201
    data = resp.json()
    uuid.UUID(data["id"])
    assert "nutrients" in data
    assert "calories_kcal" in data["nutrients"]
    assert "value" in data["nutrients"]["calories_kcal"]
    assert "coverage" in data["nutrients"]["calories_kcal"]


def test_nutrients_scaled_correctly(client, db_session):
    fid = _insert_food(db_session, name="Rice")
    _add_nutrient(db_session, fid, "calories_kcal", 130.0)

    resp = client.post("/api/entries", json=_payload(fid, weight_g="100.0"))

    assert resp.status_code == 201
    assert Decimal(resp.json()["nutrients"]["calories_kcal"]["value"]) == Decimal("130.0")


def test_all_nutrient_keys_in_response(client, db_session):
    fid = _insert_food(db_session, name="Multi-Nutrient Food")
    _add_nutrient(db_session, fid, "calories_kcal", 200.0)
    _add_nutrient(db_session, fid, "protein_g", 15.0)
    _add_nutrient(db_session, fid, "fat_g", 8.0)

    resp = client.post("/api/entries", json=_payload(fid))

    assert resp.status_code == 201
    nutrients = resp.json()["nutrients"]
    assert "calories_kcal" in nutrients
    assert "protein_g" in nutrients
    assert "fat_g" in nutrients


def test_logged_at_set_server_side(client, db_session):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid))

    assert resp.status_code == 201
    entry = db_session.get(LogEntry, uuid.UUID(resp.json()["id"]))
    assert entry is not None
    assert entry.logged_at is not None


def test_logged_at_not_in_response(client, db_session):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid))

    assert resp.status_code == 201
    assert "logged_at" not in resp.json()


def test_eaten_at_from_client(client, db_session):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid, eaten_at="2026-06-01T12:30:00"))

    assert resp.status_code == 201
    entry = db_session.get(LogEntry, uuid.UUID(resp.json()["id"]))
    assert entry is not None
    assert entry.eaten_at.hour == 12
    assert entry.eaten_at.minute == 30


def test_log_entry_nutrient_rows_created(client, db_session):
    fid = _insert_food(db_session, name="Two-Nutrient Food")
    _add_nutrient(db_session, fid, "calories_kcal", 100.0)
    _add_nutrient(db_session, fid, "protein_g", 20.0)

    resp = client.post("/api/entries", json=_payload(fid))

    assert resp.status_code == 201
    entry_id = uuid.UUID(resp.json()["id"])
    rows = db_session.execute(
        select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == entry_id)
    ).scalars().all()
    assert len(rows) == 2


def test_food_id_set_recipe_id_null(client, db_session):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid))

    assert resp.status_code == 201
    entry = db_session.get(LogEntry, uuid.UUID(resp.json()["id"]))
    assert entry is not None
    assert entry.food_id is not None
    assert entry.recipe_id is None


def test_invalid_food_id_returns_422(client):
    payload = _payload(uuid.uuid4().hex)
    resp = client.post("/api/entries", json=payload)
    assert resp.status_code == 422


def test_invalid_meal_id_returns_422(client, db_session):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid, meal_id=str(uuid.uuid4())))
    assert resp.status_code == 422


def test_integer_food_id_returns_422(client):
    payload = {
        "food_id": 12345,
        "meal_id": _BREAKFAST_ID,
        "weight_g": "100.0",
        "eaten_at": "2026-06-01T08:00:00",
        "weight_source": "scale",
        "input_method": "manual",
    }
    resp = client.post("/api/entries", json=payload)
    assert resp.status_code == 422


def test_integer_meal_id_returns_422(client, db_session):
    fid = _insert_food(db_session)
    payload = {
        "food_id": str(uuid.UUID(fid)),
        "meal_id": 99999,
        "weight_g": "100.0",
        "eaten_at": "2026-06-01T08:00:00",
        "weight_source": "scale",
        "input_method": "manual",
    }
    resp = client.post("/api/entries", json=payload)
    assert resp.status_code == 422


def test_all_inserts_use_single_session(client, db_session):
    """Entry and its nutrients are visible together — no partial commit."""
    fid = _insert_food(db_session, name="Single Session Food")
    _add_nutrient(db_session, fid, "calories_kcal", 100.0)
    _add_nutrient(db_session, fid, "protein_g", 20.0)

    resp = client.post("/api/entries", json=_payload(fid))

    assert resp.status_code == 201
    entry_id = uuid.UUID(resp.json()["id"])
    entry = db_session.get(LogEntry, entry_id)
    nutrients = db_session.execute(
        select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == entry_id)
    ).scalars().all()
    assert entry is not None
    assert len(nutrients) == 2


# ---------------------------------------------------------------------------
# POST /api/entries/batch
# ---------------------------------------------------------------------------


def test_batch_returns_501(client):
    resp = client.post("/api/entries/batch", json=[])
    assert resp.status_code == 501


# ---------------------------------------------------------------------------
# GET /api/entries/{entry_id}
# ---------------------------------------------------------------------------


def test_get_entry_returns_200(client, db_session):
    fid = _insert_food(db_session, name="Chicken Breast")
    _add_nutrient(db_session, fid, "protein_g", 31.0)
    resp = client.post("/api/entries", json=_payload(fid))
    entry_id = resp.json()["id"]

    resp = client.get(f"/api/entries/{entry_id}")

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == entry_id


def test_get_entry_food_name(client, db_session):
    fid = _insert_food(db_session, name="Brown Rice")
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid))
    entry_id = resp.json()["id"]

    data = client.get(f"/api/entries/{entry_id}").json()

    assert data["food_name"] == "Brown Rice"


def test_get_entry_nutrients_keyed_by_definition_key(client, db_session):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid, "protein_g", 25.0)
    resp = client.post("/api/entries", json=_payload(fid))
    entry_id = resp.json()["id"]

    data = client.get(f"/api/entries/{entry_id}").json()

    nutrients = data["nutrients"]
    assert "protein_g" in nutrients
    for k in nutrients:
        try:
            uuid.UUID(k)
            assert False, f"nutrient key is a UUID: {k}"
        except ValueError:
            pass


def test_get_entry_logged_at_present_and_distinct_from_eaten_at(client, db_session):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid, eaten_at="2026-06-01T08:00:00"))
    entry_id = resp.json()["id"]

    data = client.get(f"/api/entries/{entry_id}").json()

    assert "logged_at" in data
    assert data["logged_at"] is not None
    assert data["eaten_at"] != data["logged_at"]


def test_get_entry_unknown_id_returns_404(client):
    resp = client.get(f"/api/entries/{uuid.uuid4()}")
    assert resp.status_code == 404
