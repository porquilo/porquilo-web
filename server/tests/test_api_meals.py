# Run against SQLite (default, no setup required):
#   pytest server/tests/test_api_meals.py
#
# Run against PostgreSQL:
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost/porquilo_test \
#     pytest server/tests/test_api_meals.py

import uuid
from datetime import datetime

import sqlalchemy as sa

# Seeded meal IDs from migration 001 (hardcoded, deterministic across fresh installs)
_BREAKFAST_ID = "7c8c92bd-f6b5-4923-ae42-77d883a70da6"
_LUNCH_ID = "f3ed9baf-01b3-4564-9c2b-095acc2245e7"
_DINNER_ID = "36e75e9e-297e-49cd-a4b3-bb6345fc91e0"
_SNACK_ID = "bb075e7e-320a-45e4-a9d8-f28a3939d50a"


def test_list_meals_returns_all_seeded_in_sort_order(client, auth_headers):
    resp = client.get("/api/meals", headers=auth_headers)
    assert resp.status_code == 200
    meals = resp.json()

    assert len(meals) == 4
    names = [m["name"] for m in meals]
    assert names == ["Breakfast", "Lunch", "Dinner", "Snack"]


def test_list_meals_sort_order_ascending(client, auth_headers):
    resp = client.get("/api/meals", headers=auth_headers)
    orders = [m["sort_order"] for m in resp.json()]
    assert orders == sorted(orders)


def test_list_meals_response_shape(client, auth_headers):
    resp = client.get("/api/meals", headers=auth_headers)
    meals = resp.json()
    for meal in meals:
        assert set(meal.keys()) == {"id", "name", "sort_order", "is_default"}
        uuid.UUID(meal["id"])  # must be valid UUID
        assert isinstance(meal["name"], str)
        assert isinstance(meal["sort_order"], int)
        assert isinstance(meal["is_default"], bool)


def test_list_meals_known_ids(client, auth_headers):
    resp = client.get("/api/meals", headers=auth_headers)
    ids = [m["id"] for m in resp.json()]
    assert _BREAKFAST_ID in ids
    assert _LUNCH_ID in ids
    assert _DINNER_ID in ids
    assert _SNACK_ID in ids


# ---------------------------------------------------------------------------
# POST /api/meals
# ---------------------------------------------------------------------------


def test_create_meal_returns_201_and_meal_out(client, auth_headers):
    resp = client.post("/api/meals", json={"name": "Evening Snack"}, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert set(data.keys()) == {"id", "name", "sort_order", "is_default"}
    uuid.UUID(data["id"])
    assert data["name"] == "Evening Snack"
    assert isinstance(data["sort_order"], int)
    assert isinstance(data["is_default"], bool)


def test_create_meal_is_default_false(client, auth_headers):
    resp = client.post("/api/meals", json={"name": "Pre-Workout"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["is_default"] is False


def test_create_meal_sort_order_defaults_to_max_plus_one(client, auth_headers):
    # Seeded meals have sort_order 1–4; new meal should get 5
    resp = client.post("/api/meals", json={"name": "Late Night"}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["sort_order"] == 5


def test_create_meal_explicit_sort_order_stored(client, auth_headers):
    resp = client.post("/api/meals", json={"name": "Brunch", "sort_order": 99}, headers=auth_headers)
    assert resp.status_code == 201
    assert resp.json()["sort_order"] == 99


def test_create_meal_missing_name_returns_422(client, auth_headers):
    resp = client.post("/api/meals", json={"sort_order": 5}, headers=auth_headers)
    assert resp.status_code == 422


def test_create_meal_appears_in_list_in_sort_order(client, auth_headers):
    client.post("/api/meals", json={"name": "Second Breakfast", "sort_order": 2}, headers=auth_headers)
    resp = client.get("/api/meals", headers=auth_headers)
    assert resp.status_code == 200
    meals = resp.json()
    orders = [m["sort_order"] for m in meals]
    assert orders == sorted(orders)
    names = [m["name"] for m in meals]
    assert "Second Breakfast" in names


# ---------------------------------------------------------------------------
# DELETE /api/meals/{id}
# ---------------------------------------------------------------------------


def _food_source_id(db_session, key="custom"):
    row = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = :k"), {"k": key}
    ).fetchone()
    assert row is not None, f"food_source '{key}' not in DB"
    return str(row[0])


def _insert_food(db_session):
    fid = uuid.uuid4().hex
    src_id = _food_source_id(db_session)
    now = datetime.utcnow()
    db_session.execute(
        sa.text(
            "INSERT INTO foods (id, name, food_source_id, default_unit, created_at, updated_at) "
            "VALUES (:id, :name, :src, 'g', :ts, :ts)"
        ),
        {"id": fid, "name": "Test Food", "src": src_id, "ts": now},
    )
    return fid


def _insert_log_entry(db_session, meal_id, food_id):
    eid = uuid.uuid4().hex
    # Normalize to 32-char hex — SQLite stores sa.Uuid as hex (no hyphens)
    mid = uuid.UUID(meal_id).hex if "-" in meal_id else meal_id
    fid = uuid.UUID(food_id).hex if "-" in food_id else food_id
    now = datetime.utcnow()
    db_session.execute(
        sa.text(
            "INSERT INTO log_entries "
            "(id, food_id, meal_id, eaten_at, logged_at, weight_g, weight_source, weight_confidence, input_method, created_at) "
            "VALUES (:id, :fid, :mid, :ts, :ts, 100.0, 'scale', 'measured', 'manual', :ts)"
        ),
        {"id": eid, "fid": fid, "mid": mid, "ts": now},
    )
    return eid


def test_delete_meal_returns_204(client, auth_headers):
    resp = client.post("/api/meals", json={"name": "To Delete"}, headers=auth_headers)
    meal_id = resp.json()["id"]
    resp = client.delete(f"/api/meals/{meal_id}", headers=auth_headers)
    assert resp.status_code == 204


def test_deleted_meal_not_in_list(client, auth_headers):
    resp = client.post("/api/meals", json={"name": "Gone"}, headers=auth_headers)
    meal_id = resp.json()["id"]
    client.delete(f"/api/meals/{meal_id}", headers=auth_headers)
    ids = [m["id"] for m in client.get("/api/meals", headers=auth_headers).json()]
    assert meal_id not in ids


def test_delete_default_meal_returns_422(client, auth_headers):
    resp = client.delete(f"/api/meals/{_BREAKFAST_ID}", headers=auth_headers)
    assert resp.status_code == 422


def test_delete_meal_with_log_entries_returns_422(client, db_session, auth_headers):
    resp = client.post("/api/meals", json={"name": "Occupied"}, headers=auth_headers)
    meal_id = resp.json()["id"]
    fid = _insert_food(db_session)
    _insert_log_entry(db_session, meal_id, fid)
    resp = client.delete(f"/api/meals/{meal_id}", headers=auth_headers)
    assert resp.status_code == 422


def test_delete_unknown_meal_returns_404(client, auth_headers):
    resp = client.delete(f"/api/meals/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/meals/{id}
# ---------------------------------------------------------------------------


def test_patch_meal_name_renames_and_preserves_sort_order(client, auth_headers):
    resp = client.patch(f"/api/meals/{_SNACK_ID}", json={"name": "Evening Snack"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Evening Snack"
    # sort_order for Snack is 4 — must be unchanged
    assert data["sort_order"] == 4


def test_patch_meal_sort_order_reorders_and_preserves_name(client, auth_headers):
    resp = client.patch(f"/api/meals/{_BREAKFAST_ID}", json={"sort_order": 10}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sort_order"] == 10
    assert data["name"] == "Breakfast"


def test_patch_default_meal_works(client, auth_headers):
    resp = client.patch(f"/api/meals/{_BREAKFAST_ID}", json={"name": "Morning Meal"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Morning Meal"
    assert data["is_default"] is True


def test_patch_custom_meal_works(client, auth_headers):
    create_resp = client.post("/api/meals", json={"name": "Brunch"}, headers=auth_headers)
    assert create_resp.status_code == 201
    meal_id = create_resp.json()["id"]

    resp = client.patch(f"/api/meals/{meal_id}", json={"name": "Late Brunch", "sort_order": 99}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Late Brunch"
    assert data["sort_order"] == 99
    assert data["is_default"] is False


def test_patch_unknown_id_returns_404(client, auth_headers):
    resp = client.patch(f"/api/meals/{uuid.uuid4()}", json={"name": "Ghost"}, headers=auth_headers)
    assert resp.status_code == 404


def test_patch_response_is_meal_out_shape(client, auth_headers):
    resp = client.patch(f"/api/meals/{_LUNCH_ID}", json={"name": "Big Lunch"}, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert set(data.keys()) == {"id", "name", "sort_order", "is_default"}
    uuid.UUID(data["id"])
    assert isinstance(data["name"], str)
    assert isinstance(data["sort_order"], int)
    assert isinstance(data["is_default"], bool)


def test_patch_meal_appears_correctly_in_list(client, auth_headers):
    client.patch(f"/api/meals/{_DINNER_ID}", json={"name": "Supper", "sort_order": 3}, headers=auth_headers)
    resp = client.get("/api/meals", headers=auth_headers)
    assert resp.status_code == 200
    meals = resp.json()
    dinner = next(m for m in meals if m["id"] == _DINNER_ID)
    assert dinner["name"] == "Supper"
    assert dinner["sort_order"] == 3
