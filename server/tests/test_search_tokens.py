# Run against SQLite (default, no setup required):
#   pytest server/tests/test_search_tokens.py
#
# Run against PostgreSQL:
#   DATABASE_URL=postgresql+psycopg2://user:pass@localhost/porquilo_test \
#     pytest server/tests/test_search_tokens.py

import uuid
from datetime import datetime, timezone

import pytest
import sqlalchemy as sa

from porquilo.services.search_tokens import reindex_food, tokenize

_NOW = datetime(2026, 6, 8, 0, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def _no_usda(monkeypatch):
    monkeypatch.setattr("porquilo.routers.foods.search_usda", lambda *_a, **_kw: [])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _food_source_id(db_session) -> str:
    row = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'custom'")
    ).fetchone()
    assert row is not None
    return str(row[0])


def _nutrient_id(db_session, key: str = "calories_kcal") -> str:
    row = db_session.execute(
        sa.text("SELECT id FROM nutrient_definitions WHERE key = :k"), {"k": key}
    ).fetchone()
    assert row is not None
    return str(row[0])


def _insert_food(db_session, *, name: str, brand: str | None = None) -> uuid.UUID:
    fid = uuid.uuid4()
    src_id = _food_source_id(db_session)
    db_session.execute(
        sa.text(
            "INSERT INTO foods (id, name, brand, food_source_id, default_unit, created_at, updated_at)"
            " VALUES (:id, :name, :brand, :src, 'g', :ts, :ts)"
        ),
        {"id": fid.hex, "name": name, "brand": brand, "src": src_id, "ts": _NOW},
    )
    return fid


def _add_nutrient(db_session, food_id: uuid.UUID) -> None:
    nid = _nutrient_id(db_session)
    db_session.execute(
        sa.text(
            "INSERT INTO food_nutrients (id, food_id, nutrient_id, value_per_100)"
            " VALUES (:id, :fid, :nid, 100)"
        ),
        {"id": uuid.uuid4().hex, "fid": food_id.hex, "nid": nid},
    )


def _token_count(db_session, food_id: uuid.UUID) -> int:
    from porquilo.models.food_search_token import FoodSearchToken
    from sqlmodel import select

    return db_session.execute(
        select(sa.func.count()).select_from(FoodSearchToken).where(
            FoodSearchToken.food_id == food_id
        )
    ).scalar_one()


def _token_set(db_session, food_id: uuid.UUID) -> set[str]:
    from porquilo.models.food_search_token import FoodSearchToken
    from sqlmodel import select

    rows = db_session.execute(
        select(FoodSearchToken.token).where(FoodSearchToken.food_id == food_id)
    ).scalars().all()
    return set(rows)


# ---------------------------------------------------------------------------
# tokenize — pure unit tests (no DB)
# ---------------------------------------------------------------------------


def test_tokenize_peanut_butter_chunky():
    assert tokenize("Peanut Butter, Chunky") == ["peanut", "butter", "chunky"]


def test_tokenize_coca_cola_zero():
    assert tokenize("Coca-Cola Zero") == ["coca", "cola", "zero"]


def test_tokenize_none_returns_empty():
    assert tokenize(None) == []


def test_tokenize_empty_string_returns_empty():
    assert tokenize("") == []


def test_tokenize_min_length_two():
    assert tokenize("ab") == ["ab"]
    assert tokenize("a") == []


def test_tokenize_single_char_tokens_discarded():
    assert tokenize("a b c") == []


def test_tokenize_deduplication():
    result = tokenize("apple apple juice")
    assert result.count("apple") == 1
    assert "juice" in result


def test_tokenize_uppercase_lowercased():
    assert tokenize("APPLE") == ["apple"]


def test_tokenize_alphanumeric_run_is_single_token():
    # "B100" has no separator — stays as one token "b100"
    result = tokenize("Vitamin B100")
    assert "vitamin" in result
    assert "b100" in result


# ---------------------------------------------------------------------------
# reindex_food — integration tests
# ---------------------------------------------------------------------------


def test_reindex_food_creates_tokens(db_session):
    fid = _insert_food(db_session, name="Peanut Butter", brand="Skippy")
    reindex_food(fid, db_session)

    tokens = _token_set(db_session, fid)
    assert "peanut" in tokens
    assert "butter" in tokens
    assert "skippy" in tokens


def test_reindex_food_is_idempotent(db_session):
    fid = _insert_food(db_session, name="Almond Milk", brand="Blue Diamond")
    reindex_food(fid, db_session)
    count_after_first = _token_count(db_session, fid)

    reindex_food(fid, db_session)
    count_after_second = _token_count(db_session, fid)

    assert count_after_first == count_after_second > 0


def test_reindex_food_unknown_id_is_noop(db_session):
    # Must not raise
    reindex_food(uuid.uuid4(), db_session)


def test_reindex_food_none_brand(db_session):
    fid = _insert_food(db_session, name="Oat Meal", brand=None)
    reindex_food(fid, db_session)
    tokens = _token_set(db_session, fid)
    assert "oat" in tokens
    assert "meal" in tokens


# ---------------------------------------------------------------------------
# Search endpoint — token-based search
# ---------------------------------------------------------------------------


def test_token_search_prefix_match(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Peanut Butter")
    _add_nutrient(db_session, fid)
    reindex_food(fid, db_session)

    resp = client.get("/api/foods", params={"q": "butter"}, headers=auth_headers)
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    assert "Peanut Butter" in names


def test_token_search_partial_prefix(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Peanut Butter")
    _add_nutrient(db_session, fid)
    reindex_food(fid, db_session)

    resp = client.get("/api/foods", params={"q": "pean"}, headers=auth_headers)
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    assert "Peanut Butter" in names


def test_token_search_no_match_returns_empty(client, db_session, auth_headers):
    resp = client.get("/api/foods", params={"q": "xyz_no_match_token"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"items": [], "total": 0}


def test_token_search_multi_word_query(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Brown Rice")
    _add_nutrient(db_session, fid)
    reindex_food(fid, db_session)

    resp = client.get("/api/foods", params={"q": "brown rice"}, headers=auth_headers)
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    assert "Brown Rice" in names


def test_browse_mode_no_token_filter(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Zucchini")
    _add_nutrient(db_session, fid)
    # No tokens — browse mode should still return the food

    resp = client.get("/api/foods", headers=auth_headers)
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    assert "Zucchini" in names


def test_short_q_browse_mode_no_token_filter(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Avocado")
    _add_nutrient(db_session, fid)
    # q shorter than 2 chars → browse mode, no token filtering

    resp = client.get("/api/foods", params={"q": "a"}, headers=auth_headers)
    assert resp.status_code == 200
    # just verify no 500
    assert "items" in resp.json()


def test_token_search_brand_match(client, db_session, auth_headers):
    fid = _insert_food(db_session, name="Orange Juice", brand="Tropicana")
    _add_nutrient(db_session, fid)
    reindex_food(fid, db_session)

    resp = client.get("/api/foods", params={"q": "tropicana"}, headers=auth_headers)
    assert resp.status_code == 200
    names = [f["name"] for f in resp.json()["items"]]
    assert "Orange Juice" in names


def test_total_count_matches_token_search(client, db_session, auth_headers):
    for i in range(3):
        fid = _insert_food(db_session, name=f"Kale Chip {i}")
        _add_nutrient(db_session, fid)
        reindex_food(fid, db_session)

    resp = client.get("/api/foods", params={"q": "kale"}, headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    assert len(body["items"]) == 3
