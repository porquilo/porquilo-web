# Run against SQLite (default, no setup required):
#   pytest server/tests/test_foods_suggestions.py
#
# Run against PostgreSQL:
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost/porquilo_test \
#     pytest server/tests/test_foods_suggestions.py

import uuid
from datetime import datetime, timedelta, timezone

import pytest
import sqlalchemy as sa

# Seeded meal id from migration 001 (hardcoded, deterministic across fresh installs)
_BREAKFAST_ID = "7c8c92bd-f6b5-4923-ae42-77d883a70da6"

_NOW = datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc)


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


def _insert_food(db_session, *, name: str, source_key: str = "custom") -> str:
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


def _add_calories(db_session, food_id: str, value: float = 100.0) -> None:
    nid = _nutrient_id(db_session, "calories_kcal")
    db_session.execute(
        sa.text(
            "INSERT INTO food_nutrients (id, food_id, nutrient_id, value_per_100) "
            "VALUES (:id, :fid, :nid, :val)"
        ),
        {"id": uuid.uuid4().hex, "fid": food_id, "nid": nid, "val": value},
    )


def _insert_entry(
    db_session,
    *,
    food_id: str,
    user_id: str,
    eaten_at: datetime,
    meal_id: str = _BREAKFAST_ID,
) -> str:
    eid = uuid.uuid4().hex
    db_session.execute(
        sa.text(
            "INSERT INTO log_entries "
            "(id, food_id, meal_id, eaten_at, logged_at, weight_g, weight_source, weight_confidence, input_method, user_id) "
            "VALUES (:id, :fid, :mid, :eaten, :logged, 100.0, 'user', 'exact', 'manual', :uid)"
        ),
        {
            "id": eid,
            "fid": food_id,
            "mid": meal_id.replace("-", ""),
            "eaten": eaten_at,
            "logged": _NOW,
            "uid": user_id.replace("-", ""),
        },
    )
    return eid


@pytest.fixture
def second_user(db_session):
    from porquilo.services.auth_service import create_user
    user = create_user("seconduser", "secondpass", "member", db_session)
    db_session.commit()
    return user


@pytest.fixture
def second_auth_headers(db_session, second_user):
    from porquilo.services.auth_service import create_token
    token = create_token(second_user.id, db_session)
    db_session.commit()
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_no_history_returns_empty_arrays(client, auth_headers):
    resp = client.get("/api/foods/suggestions", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"recent": [], "frequent": []}


def test_recent_deduplicates_by_food_id(client, db_session, test_user, auth_headers):
    fid = _insert_food(db_session, name="Apple")
    _add_calories(db_session, fid)
    _insert_entry(db_session, food_id=fid, user_id=str(test_user.id), eaten_at=_NOW)
    _insert_entry(db_session, food_id=fid, user_id=str(test_user.id), eaten_at=_NOW + timedelta(hours=1))

    resp = client.get("/api/foods/suggestions", headers=auth_headers)
    assert resp.status_code == 200
    recent = resp.json()["recent"]
    assert len(recent) == 1
    assert recent[0]["food_id"] == fid or recent[0]["food_id"].replace("-", "") == fid


def test_recent_ordered_newest_first(client, db_session, test_user, auth_headers):
    fid1 = _insert_food(db_session, name="Coffee")
    fid2 = _insert_food(db_session, name="Toast")
    _add_calories(db_session, fid1)
    _add_calories(db_session, fid2)
    _insert_entry(db_session, food_id=fid1, user_id=str(test_user.id), eaten_at=_NOW)
    _insert_entry(db_session, food_id=fid2, user_id=str(test_user.id), eaten_at=_NOW + timedelta(hours=2))

    resp = client.get("/api/foods/suggestions", headers=auth_headers)
    recent = resp.json()["recent"]
    assert recent[0]["food_name"] == "Toast"
    assert recent[1]["food_name"] == "Coffee"


def test_recent_last_logged_at_is_most_recent_eat(client, db_session, test_user, auth_headers):
    fid = _insert_food(db_session, name="Banana")
    _add_calories(db_session, fid)
    _insert_entry(db_session, food_id=fid, user_id=str(test_user.id), eaten_at=_NOW)
    latest = _NOW + timedelta(days=1)
    _insert_entry(db_session, food_id=fid, user_id=str(test_user.id), eaten_at=latest)

    resp = client.get("/api/foods/suggestions", headers=auth_headers)
    recent = resp.json()["recent"]
    assert len(recent) == 1
    returned = datetime.fromisoformat(recent[0]["last_logged_at"].replace("Z", "+00:00"))
    assert returned.replace(tzinfo=None) == latest.replace(tzinfo=None)


def test_frequent_orders_by_log_count(client, db_session, test_user, auth_headers):
    fid_often = _insert_food(db_session, name="Rice")
    fid_rare = _insert_food(db_session, name="Quinoa")
    _add_calories(db_session, fid_often)
    _add_calories(db_session, fid_rare)
    for i in range(3):
        _insert_entry(db_session, food_id=fid_often, user_id=str(test_user.id), eaten_at=_NOW + timedelta(hours=i))
    _insert_entry(db_session, food_id=fid_rare, user_id=str(test_user.id), eaten_at=_NOW)

    resp = client.get("/api/foods/suggestions", headers=auth_headers)
    frequent = resp.json()["frequent"]
    assert frequent[0]["food_name"] == "Rice"
    assert frequent[0]["log_count"] == 3


def test_frequent_log_count_is_total_entries_not_unique_days(client, db_session, test_user, auth_headers):
    fid = _insert_food(db_session, name="Eggs")
    _add_calories(db_session, fid)
    for i in range(4):
        _insert_entry(db_session, food_id=fid, user_id=str(test_user.id), eaten_at=_NOW + timedelta(days=i))

    resp = client.get("/api/foods/suggestions", headers=auth_headers)
    frequent = resp.json()["frequent"]
    assert frequent[0]["log_count"] == 4


def test_arrays_cap_at_five(client, db_session, test_user, auth_headers):
    for i in range(8):
        fid = _insert_food(db_session, name=f"Food {i}")
        _add_calories(db_session, fid)
        _insert_entry(db_session, food_id=fid, user_id=str(test_user.id), eaten_at=_NOW + timedelta(hours=i))

    resp = client.get("/api/foods/suggestions", headers=auth_headers)
    data = resp.json()
    assert len(data["recent"]) == 5
    assert len(data["frequent"]) == 5


def test_user_isolation(client, db_session, test_user, second_user, auth_headers, second_auth_headers):
    fid_a = _insert_food(db_session, name="User A Food")
    fid_b = _insert_food(db_session, name="User B Food")
    _add_calories(db_session, fid_a)
    _add_calories(db_session, fid_b)
    _insert_entry(db_session, food_id=fid_a, user_id=str(test_user.id), eaten_at=_NOW)
    _insert_entry(db_session, food_id=fid_b, user_id=str(second_user.id), eaten_at=_NOW)

    resp_a = client.get("/api/foods/suggestions", headers=auth_headers)
    resp_b = client.get("/api/foods/suggestions", headers=second_auth_headers)

    names_a = {item["food_name"] for item in resp_a.json()["recent"]}
    names_b = {item["food_name"] for item in resp_b.json()["recent"]}
    assert names_a == {"User A Food"}
    assert names_b == {"User B Food"}


@pytest.mark.parametrize(
    "source_key,expected_display",
    [
        ("usda", "USDA"),
        ("open_food_facts", "Barcode"),
        ("custom", "Custom"),
    ],
)
def test_source_display_mapping(client, db_session, test_user, auth_headers, source_key, expected_display):
    fid = _insert_food(db_session, name="Mapped Food", source_key=source_key)
    _add_calories(db_session, fid)
    _insert_entry(db_session, food_id=fid, user_id=str(test_user.id), eaten_at=_NOW)

    resp = client.get("/api/foods/suggestions", headers=auth_headers)
    recent = resp.json()["recent"]
    assert recent[0]["source_display"] == expected_display


def test_unauthenticated_returns_401(client):
    resp = client.get("/api/foods/suggestions")
    assert resp.status_code == 401
