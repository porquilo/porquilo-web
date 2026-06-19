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


def test_create_entry_returns_201(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)

    assert resp.status_code == 201
    data = resp.json()
    uuid.UUID(data["id"])
    assert "nutrients" in data
    assert "calories_kcal" in data["nutrients"]
    assert "value" in data["nutrients"]["calories_kcal"]
    assert "coverage" in data["nutrients"]["calories_kcal"]


def test_nutrients_scaled_correctly(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Rice")
    _add_nutrient(db_session, fid, "calories_kcal", 130.0)

    resp = client.post("/api/entries", json=_payload(fid, weight_g="100.0"), headers=auth_headers)

    assert resp.status_code == 201
    assert Decimal(resp.json()["nutrients"]["calories_kcal"]["value"]) == Decimal("130.0")


def test_all_nutrient_keys_in_response(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Multi-Nutrient Food")
    _add_nutrient(db_session, fid, "calories_kcal", 200.0)
    _add_nutrient(db_session, fid, "protein_g", 15.0)
    _add_nutrient(db_session, fid, "fat_g", 8.0)

    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)

    assert resp.status_code == 201
    nutrients = resp.json()["nutrients"]
    assert "calories_kcal" in nutrients
    assert "protein_g" in nutrients
    assert "fat_g" in nutrients


def test_logged_at_set_server_side(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)

    assert resp.status_code == 201
    entry = db_session.get(LogEntry, uuid.UUID(resp.json()["id"]))
    assert entry is not None
    assert entry.logged_at is not None


def test_logged_at_not_in_response(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)

    assert resp.status_code == 201
    assert "logged_at" not in resp.json()


def test_eaten_at_from_client(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid, eaten_at="2026-06-01T12:30:00"), headers=auth_headers)

    assert resp.status_code == 201
    entry = db_session.get(LogEntry, uuid.UUID(resp.json()["id"]))
    assert entry is not None
    assert entry.eaten_at.hour == 12
    assert entry.eaten_at.minute == 30


def test_log_entry_nutrient_rows_created(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Two-Nutrient Food")
    _add_nutrient(db_session, fid, "calories_kcal", 100.0)
    _add_nutrient(db_session, fid, "protein_g", 20.0)

    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)

    assert resp.status_code == 201
    entry_id = uuid.UUID(resp.json()["id"])
    rows = db_session.execute(
        select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == entry_id)
    ).scalars().all()
    assert len(rows) == 2


def test_food_id_set_recipe_id_null(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)

    assert resp.status_code == 201
    entry = db_session.get(LogEntry, uuid.UUID(resp.json()["id"]))
    assert entry is not None
    assert entry.food_id is not None
    assert entry.recipe_id is None


def test_invalid_food_id_returns_422(client, auth_headers):
    payload = _payload(uuid.uuid4().hex)
    resp = client.post("/api/entries", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_invalid_meal_id_returns_422(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)

    resp = client.post("/api/entries", json=_payload(fid, meal_id=str(uuid.uuid4())), headers=auth_headers)
    assert resp.status_code == 422


def test_integer_food_id_returns_422(client, auth_headers):
    payload = {
        "food_id": 12345,
        "meal_id": _BREAKFAST_ID,
        "weight_g": "100.0",
        "eaten_at": "2026-06-01T08:00:00",
        "weight_source": "scale",
        "input_method": "manual",
    }
    resp = client.post("/api/entries", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_integer_meal_id_returns_422(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    payload = {
        "food_id": str(uuid.UUID(fid)),
        "meal_id": 99999,
        "weight_g": "100.0",
        "eaten_at": "2026-06-01T08:00:00",
        "weight_source": "scale",
        "input_method": "manual",
    }
    resp = client.post("/api/entries", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_all_inserts_use_single_session(client, db_session, auth_headers):
    """Entry and its nutrients are visible together — no partial commit."""
    fid = _insert_food(db_session, name="Single Session Food")
    _add_nutrient(db_session, fid, "calories_kcal", 100.0)
    _add_nutrient(db_session, fid, "protein_g", 20.0)

    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)

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


def test_batch_returns_501(client, auth_headers):
    resp = client.post("/api/entries/batch", json=[], headers=auth_headers)
    assert resp.status_code == 501


# ---------------------------------------------------------------------------
# GET /api/entries/{entry_id}
# ---------------------------------------------------------------------------


def test_get_entry_returns_200(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Chicken Breast")
    _add_nutrient(db_session, fid, "protein_g", 31.0)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]

    resp = client.get(f"/api/entries/{entry_id}", headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == entry_id


def test_get_entry_food_name(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Brown Rice")
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]

    data = client.get(f"/api/entries/{entry_id}", headers=auth_headers).json()

    assert data["food_name"] == "Brown Rice"


def test_get_entry_nutrients_keyed_by_definition_key(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid, "protein_g", 25.0)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]

    data = client.get(f"/api/entries/{entry_id}", headers=auth_headers).json()

    nutrients = data["nutrients"]
    assert "protein_g" in nutrients
    for k in nutrients:
        try:
            uuid.UUID(k)
            assert False, f"nutrient key is a UUID: {k}"
        except ValueError:
            pass


def test_get_entry_logged_at_present_and_distinct_from_eaten_at(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid, eaten_at="2026-06-01T08:00:00"), headers=auth_headers)
    entry_id = resp.json()["id"]

    data = client.get(f"/api/entries/{entry_id}", headers=auth_headers).json()

    assert "logged_at" in data
    assert data["logged_at"] is not None
    assert data["eaten_at"] != data["logged_at"]


def test_get_entry_unknown_id_returns_404(client, auth_headers):
    resp = client.get(f"/api/entries/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


def test_get_entry_other_user_returns_404(client, db_session, auth_headers, admin_headers):
    """An entry created by one user is not visible to another user."""
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    assert resp.status_code == 201
    entry_id = resp.json()["id"]

    resp = client.get(f"/api/entries/{entry_id}", headers=admin_headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/entries/{entry_id}
# ---------------------------------------------------------------------------

# Lunch meal seeded in migration 001
_LUNCH_ID = "f3ed9baf-01b3-4564-9c2b-095acc2245e7"


def _create_entry(client, db_session, auth_headers, *, nutrient_key="calories_kcal", value=200.0, **payload_overrides):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid, nutrient_key, value)
    resp = client.post("/api/entries", json=_payload(fid, **payload_overrides), headers=auth_headers)
    assert resp.status_code == 201
    return fid, resp.json()["id"]


def test_patch_meal_id_only(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]
    old_nutrients = db_session.execute(
        select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == uuid.UUID(entry_id))
    ).scalars().all()

    resp = client.patch(f"/api/entries/{entry_id}", json={"meal_id": _LUNCH_ID}, headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["meal_id"] == _LUNCH_ID
    new_nutrients = db_session.execute(
        select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == uuid.UUID(entry_id))
    ).scalars().all()
    assert len(new_nutrients) == len(old_nutrients)


def test_patch_eaten_at_only(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid, eaten_at="2026-06-01T08:00:00"), headers=auth_headers)
    entry_id = resp.json()["id"]

    resp = client.patch(f"/api/entries/{entry_id}", json={"eaten_at": "2026-06-01T20:00:00"}, headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert "20:00:00" in data["eaten_at"] or data["eaten_at"].startswith("2026-06-01T20")
    new_nutrients = db_session.execute(
        select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == uuid.UUID(entry_id))
    ).scalars().all()
    assert len(new_nutrients) == 1


def test_patch_weight_g_recomputes_nutrients(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid, "calories_kcal", 100.0)
    resp = client.post("/api/entries", json=_payload(fid, weight_g="100.0"), headers=auth_headers)
    entry_id = resp.json()["id"]

    resp = client.patch(f"/api/entries/{entry_id}", json={"weight_g": "200.0"}, headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["nutrients"]["calories_kcal"]["value"]) == Decimal("200.0")
    assert Decimal(data["weight_g"]) == Decimal("200.0")


def test_patch_weight_source_recomputes_and_updates_confidence(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid, "calories_kcal", 100.0)
    resp = client.post("/api/entries", json=_payload(fid, weight_source="scale"), headers=auth_headers)
    entry_id = resp.json()["id"]
    assert client.get(f"/api/entries/{entry_id}", headers=auth_headers).json()["weight_confidence"] == "measured"

    resp = client.patch(f"/api/entries/{entry_id}", json={"weight_source": "estimated"}, headers=auth_headers)

    assert resp.status_code == 200
    data = resp.json()
    assert data["weight_source"] == "estimated"
    assert data["weight_confidence"] == "estimated"


def test_patch_old_nutrients_deleted_new_inserted(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid, "calories_kcal", 100.0)
    _add_nutrient(db_session, fid, "protein_g", 20.0)
    resp = client.post("/api/entries", json=_payload(fid, weight_g="100.0"), headers=auth_headers)
    entry_id = resp.json()["id"]
    old_ids = {
        row.id for row in db_session.execute(
            select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == uuid.UUID(entry_id))
        ).scalars().all()
    }
    assert len(old_ids) == 2

    client.patch(f"/api/entries/{entry_id}", json={"weight_g": "50.0"}, headers=auth_headers)

    new_rows = db_session.execute(
        select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == uuid.UUID(entry_id))
    ).scalars().all()
    new_ids = {row.id for row in new_rows}
    assert len(new_ids) == 2
    assert old_ids.isdisjoint(new_ids)


def test_patch_unknown_meal_id_returns_422(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]

    resp = client.patch(f"/api/entries/{entry_id}", json={"meal_id": str(uuid.uuid4())}, headers=auth_headers)

    assert resp.status_code == 422


def test_patch_unknown_entry_id_returns_404(client, auth_headers):
    resp = client.patch(f"/api/entries/{uuid.uuid4()}", json={"eaten_at": "2026-06-01T12:00:00"}, headers=auth_headers)
    assert resp.status_code == 404


def test_patch_other_user_entry_returns_404(client, db_session, auth_headers, admin_headers):
    """PATCH for an entry owned by a different user returns 404."""
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]

    resp = client.patch(f"/api/entries/{entry_id}", json={"eaten_at": "2026-06-01T12:00:00"}, headers=admin_headers)
    assert resp.status_code == 404


def test_patch_response_is_entry_detail_out(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Oats")
    _add_nutrient(db_session, fid, "calories_kcal", 380.0)
    resp = client.post("/api/entries", json=_payload(fid, weight_g="50.0"), headers=auth_headers)
    entry_id = resp.json()["id"]

    data = client.patch(f"/api/entries/{entry_id}", json={"weight_g": "75.0"}, headers=auth_headers).json()

    for field in ("id", "food_id", "food_name", "meal_id", "eaten_at", "logged_at",
                  "weight_g", "weight_source", "weight_confidence", "nutrients"):
        assert field in data, f"missing field: {field}"
    assert data["food_name"] == "Oats"
    assert Decimal(data["nutrients"]["calories_kcal"]["value"]) == Decimal("285.0")


def test_patch_logged_at_unchanged(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]
    original_logged_at = client.get(f"/api/entries/{entry_id}", headers=auth_headers).json()["logged_at"]

    data = client.patch(f"/api/entries/{entry_id}", json={"eaten_at": "2026-06-02T09:00:00"}, headers=auth_headers).json()

    assert data["logged_at"] == original_logged_at


def test_patch_no_weight_fields_nutrients_unchanged(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid, "calories_kcal", 100.0)
    _add_nutrient(db_session, fid, "protein_g", 10.0)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]
    before_ids = {
        row.id for row in db_session.execute(
            select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == uuid.UUID(entry_id))
        ).scalars().all()
    }

    client.patch(f"/api/entries/{entry_id}", json={"eaten_at": "2026-06-03T10:00:00"}, headers=auth_headers)

    after_ids = {
        row.id for row in db_session.execute(
            select(LogEntryNutrient).where(LogEntryNutrient.log_entry_id == uuid.UUID(entry_id))
        ).scalars().all()
    }
    assert before_ids == after_ids


# ---------------------------------------------------------------------------
# DELETE /api/entries/{entry_id}
# ---------------------------------------------------------------------------


def test_delete_entry_returns_204(client, db_session, auth_headers):
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]

    resp = client.delete(f"/api/entries/{entry_id}", headers=auth_headers)
    assert resp.status_code == 204


def test_delete_other_user_entry_returns_404(client, db_session, auth_headers, admin_headers):
    """DELETE for an entry owned by a different user returns 404."""
    fid = _insert_food(db_session)
    _add_nutrient(db_session, fid)
    resp = client.post("/api/entries", json=_payload(fid), headers=auth_headers)
    entry_id = resp.json()["id"]

    resp = client.delete(f"/api/entries/{entry_id}", headers=admin_headers)
    assert resp.status_code == 404
