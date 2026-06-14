# Run against SQLite (default, no setup required):
#   pytest server/tests/test_api_meals.py
#
# Run against PostgreSQL:
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost/porquilo_test \
#     pytest server/tests/test_api_meals.py

import uuid

# Seeded meal IDs from migration 001 (hardcoded, deterministic across fresh installs)
_BREAKFAST_ID = "7c8c92bd-f6b5-4923-ae42-77d883a70da6"
_LUNCH_ID = "f3ed9baf-01b3-4564-9c2b-095acc2245e7"
_DINNER_ID = "36e75e9e-297e-49cd-a4b3-bb6345fc91e0"
_SNACK_ID = "bb075e7e-320a-45e4-a9d8-f28a3939d50a"


def test_list_meals_returns_all_seeded_in_sort_order(client):
    resp = client.get("/api/meals")
    assert resp.status_code == 200
    meals = resp.json()

    assert len(meals) == 4
    names = [m["name"] for m in meals]
    assert names == ["Breakfast", "Lunch", "Dinner", "Snack"]


def test_list_meals_sort_order_ascending(client):
    resp = client.get("/api/meals")
    orders = [m["sort_order"] for m in resp.json()]
    assert orders == sorted(orders)


def test_list_meals_response_shape(client):
    resp = client.get("/api/meals")
    meals = resp.json()
    for meal in meals:
        assert set(meal.keys()) == {"id", "name", "sort_order", "is_default"}
        uuid.UUID(meal["id"])  # must be valid UUID
        assert isinstance(meal["name"], str)
        assert isinstance(meal["sort_order"], int)
        assert isinstance(meal["is_default"], bool)


def test_list_meals_known_ids(client):
    resp = client.get("/api/meals")
    ids = [m["id"] for m in resp.json()]
    assert _BREAKFAST_ID in ids
    assert _LUNCH_ID in ids
    assert _DINNER_ID in ids
    assert _SNACK_ID in ids


# ---------------------------------------------------------------------------
# POST /api/meals
# ---------------------------------------------------------------------------


def test_create_meal_returns_201_and_meal_out(client):
    resp = client.post("/api/meals", json={"name": "Evening Snack"})
    assert resp.status_code == 201
    data = resp.json()
    assert set(data.keys()) == {"id", "name", "sort_order", "is_default"}
    uuid.UUID(data["id"])
    assert data["name"] == "Evening Snack"
    assert isinstance(data["sort_order"], int)
    assert isinstance(data["is_default"], bool)


def test_create_meal_is_default_false(client):
    resp = client.post("/api/meals", json={"name": "Pre-Workout"})
    assert resp.status_code == 201
    assert resp.json()["is_default"] is False


def test_create_meal_sort_order_defaults_to_max_plus_one(client):
    # Seeded meals have sort_order 1–4; new meal should get 5
    resp = client.post("/api/meals", json={"name": "Late Night"})
    assert resp.status_code == 201
    assert resp.json()["sort_order"] == 5


def test_create_meal_explicit_sort_order_stored(client):
    resp = client.post("/api/meals", json={"name": "Brunch", "sort_order": 99})
    assert resp.status_code == 201
    assert resp.json()["sort_order"] == 99


def test_create_meal_missing_name_returns_422(client):
    resp = client.post("/api/meals", json={"sort_order": 5})
    assert resp.status_code == 422


def test_create_meal_appears_in_list_in_sort_order(client):
    client.post("/api/meals", json={"name": "Second Breakfast", "sort_order": 2})
    resp = client.get("/api/meals")
    assert resp.status_code == 200
    meals = resp.json()
    orders = [m["sort_order"] for m in meals]
    assert orders == sorted(orders)
    names = [m["name"] for m in meals]
    assert "Second Breakfast" in names
