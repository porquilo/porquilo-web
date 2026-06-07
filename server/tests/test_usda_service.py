"""Tests for usda_service — all USDA HTTP calls are mocked; no live network needed."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
import sqlalchemy as sa
from sqlalchemy.orm import Session

from porquilo.models import Food
from porquilo.services import usda_service
from porquilo.services.usda_service import search_usda, upsert_usda_food

# ---------------------------------------------------------------------------
# Realistic USDA API response fixture
# ---------------------------------------------------------------------------

_USDA_CHICKEN_FOOD = {
    "fdcId": 171477,
    "description": "Chicken, broilers or fryers, breast, meat only, cooked, roasted",
    "brandOwner": None,
    "brandName": None,
    "foodNutrients": [
        {"nutrientId": 1008, "nutrientNumber": "208", "value": 165.0},   # calories_kcal
        {"nutrientId": 1003, "nutrientNumber": "203", "value": 31.0},    # protein_g
        {"nutrientId": 1004, "nutrientNumber": "204", "value": 3.6},     # fat_g
        {"nutrientId": 1005, "nutrientNumber": "205", "value": 0.0},     # carbs_g
        {"nutrientId": 1093, "nutrientNumber": "307", "value": 74.0},    # sodium_mg
        {"nutrientId": 1258, "nutrientNumber": "606", "value": 1.01},    # saturated_fat_g
        {"nutrientId": 1087, "nutrientNumber": "301", "value": 15.0},    # calcium_mg
        {"nutrientId": 1089, "nutrientNumber": "303", "value": 1.04},    # iron_mg
    ],
}

_USDA_SEARCH_RESPONSE = {
    "foods": [_USDA_CHICKEN_FOOD],
    "totalHits": 1,
    "currentPage": 1,
    "totalPages": 1,
}


def _mock_200(body: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = body
    return resp


def _mock_error(status: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = {}
    return resp


# ---------------------------------------------------------------------------
# search_usda — API key resolution
# ---------------------------------------------------------------------------


def test_search_usda_uses_demo_key_fallback(db_session):
    """No DB setting, no env var → DEMO_KEY is used."""
    with patch("porquilo.services.usda_service.httpx.get", return_value=_mock_200(_USDA_SEARCH_RESPONSE)) as mock_get:
        with patch.dict("os.environ", {}, clear=False):
            import os
            os.environ.pop("USDA_API_KEY", None)
            result = search_usda("chicken", db_session)

    call_params = mock_get.call_args[1]["params"]
    assert call_params["api_key"] == "DEMO_KEY"
    assert result == _USDA_SEARCH_RESPONSE["foods"]


def test_search_usda_uses_db_setting(db_session):
    """usda_api_key in app_settings → that key is sent."""
    db_session.execute(
        sa.text("UPDATE app_settings SET value = :v WHERE key = 'usda_api_key'"),
        {"v": "MY_DB_KEY"},
    )

    with patch("porquilo.services.usda_service.httpx.get", return_value=_mock_200(_USDA_SEARCH_RESPONSE)) as mock_get:
        search_usda("chicken", db_session)

    call_params = mock_get.call_args[1]["params"]
    assert call_params["api_key"] == "MY_DB_KEY"

    # Restore to null so subsequent tests are unaffected.
    db_session.execute(
        sa.text("UPDATE app_settings SET value = NULL WHERE key = 'usda_api_key'")
    )


def test_search_usda_uses_env_var_when_no_db_setting(db_session):
    """USDA_API_KEY env var used when DB setting is null."""
    with patch("porquilo.services.usda_service.httpx.get", return_value=_mock_200(_USDA_SEARCH_RESPONSE)) as mock_get:
        with patch.dict("os.environ", {"USDA_API_KEY": "ENV_KEY"}):
            search_usda("chicken", db_session)

    call_params = mock_get.call_args[1]["params"]
    assert call_params["api_key"] == "ENV_KEY"


# ---------------------------------------------------------------------------
# search_usda — error handling
# ---------------------------------------------------------------------------


def test_search_usda_returns_empty_on_timeout(db_session):
    import httpx as _httpx

    with patch("porquilo.services.usda_service.httpx.get", side_effect=_httpx.TimeoutException("timed out")):
        result = search_usda("chicken", db_session)

    assert result == []


def test_search_usda_returns_empty_on_non_200(db_session):
    with patch("porquilo.services.usda_service.httpx.get", return_value=_mock_error(500)):
        result = search_usda("chicken", db_session)

    assert result == []


def test_search_usda_returns_empty_on_non_json_200(db_session):
    """USDA occasionally returns a 200 with an empty/non-JSON body on rate-limit edges."""
    resp = MagicMock()
    resp.status_code = 200
    resp.json.side_effect = ValueError("Expecting value: line 1 column 1 (char 0)")
    with patch("porquilo.services.usda_service.httpx.get", return_value=resp):
        result = search_usda("chicken", db_session)

    assert result == []


def test_search_usda_sends_correct_data_types(db_session):
    """dataType filter includes Foundation; Branded and SR Legacy excluded."""
    with patch("porquilo.services.usda_service.httpx.get", return_value=_mock_200(_USDA_SEARCH_RESPONSE)) as mock_get:
        search_usda("apple", db_session, page_size=5)

    params = mock_get.call_args[1]["params"]
    assert set(params["dataType"]) == {"Foundation"}
    assert params["pageSize"] == 5
    assert params["query"] == "apple"


# ---------------------------------------------------------------------------
# upsert_usda_food — INSERT path
# ---------------------------------------------------------------------------


def test_upsert_creates_food_and_nutrients(db_session):
    # Clear module-level cache so each test resolves cleanly.
    usda_service._nutrient_id_cache.clear()

    with patch("porquilo.services.usda_service.try_normalize_inline"):
        food, _ = upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()

    row = db_session.execute(
        sa.text("SELECT id, name, external_source_id FROM foods WHERE external_source_id = '171477'")
    ).fetchone()
    assert row is not None
    assert "Chicken" in row[1]

    nutrient_count = db_session.execute(
        sa.text("SELECT COUNT(*) FROM food_nutrients WHERE food_id = :fid"),
        {"fid": food.id.hex},
    ).scalar()
    assert nutrient_count == len(_USDA_CHICKEN_FOOD["foodNutrients"])


def test_upsert_writes_sync_log_on_insert(db_session):
    usda_service._nutrient_id_cache.clear()

    usda_source_id = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'usda'")
    ).scalar()

    with patch("porquilo.services.usda_service.try_normalize_inline"):
        upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()

    log_count = db_session.execute(
        sa.text("SELECT COUNT(*) FROM sync_log WHERE food_source_id = :sid AND notes = 'usda_search_cache'"),
        {"sid": str(usda_source_id)},
    ).scalar()
    assert log_count == 1


def test_source_completeness_range(db_session):
    usda_service._nutrient_id_cache.clear()

    with patch("porquilo.services.usda_service.try_normalize_inline"):
        food, _ = upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()

    assert food.source_completeness is not None
    assert 0.0 <= food.source_completeness <= 1.0
    # 8 of 27 nutrients present in fixture
    assert food.source_completeness == round(8 / 27, 4)


def test_upsert_calories_max_wins_across_methodology_variants(db_session):
    """When 1008, 2047, and 2048 all appear, the highest kcal value is stored."""
    usda_service._nutrient_id_cache.clear()

    food_with_variants = {
        "fdcId": 999001,
        "description": "Test Foundation Food",
        "brandOwner": None,
        "brandName": None,
        "foodNutrients": [
            {"nutrientId": 1008, "nutrientNumber": "208", "value": 0.0},    # calories via 1008 (absent)
            {"nutrientId": 2047, "nutrientNumber": "2047", "value": 150.0}, # Atwater General
            {"nutrientId": 2048, "nutrientNumber": "2048", "value": 163.0}, # Atwater Specific (highest)
            {"nutrientId": 1003, "nutrientNumber": "203", "value": 25.0},   # protein
        ],
    }

    with patch("porquilo.services.usda_service.try_normalize_inline"):
        food, _ = upsert_usda_food(food_with_variants, db_session)
        db_session.flush()

    # Only one calories_kcal row should exist, with value 163 (the max).
    cal_nutrient_id = db_session.execute(
        sa.text("SELECT id FROM nutrient_definitions WHERE key = 'calories_kcal'")
    ).scalar()
    rows = db_session.execute(
        sa.text(
            "SELECT value_per_100 FROM food_nutrients WHERE food_id = :fid AND nutrient_id = :nid"
        ),
        {"fid": food.id.hex, "nid": str(cal_nutrient_id)},
    ).fetchall()
    assert len(rows) == 1
    assert float(rows[0][0]) == 163.0


# ---------------------------------------------------------------------------
# upsert_usda_food — UPDATE path
# ---------------------------------------------------------------------------


def test_upsert_updates_on_second_call(db_session):
    usda_service._nutrient_id_cache.clear()

    with patch("porquilo.services.usda_service.try_normalize_inline"):
        upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()

    modified = {**_USDA_CHICKEN_FOOD, "description": "Chicken Breast Updated"}
    food, is_new = upsert_usda_food(modified, db_session)
    db_session.flush()

    # Only one row should exist for this fdcId.
    count = db_session.execute(
        sa.text("SELECT COUNT(*) FROM foods WHERE external_source_id = '171477'")
    ).scalar()
    assert count == 1
    assert is_new is False
    assert food.name == "Chicken Breast Updated"


def test_upsert_no_sync_log_on_update(db_session):
    usda_service._nutrient_id_cache.clear()

    usda_source_id = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'usda'")
    ).scalar()

    with patch("porquilo.services.usda_service.try_normalize_inline"):
        upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()

    upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
    db_session.flush()

    log_count = db_session.execute(
        sa.text("SELECT COUNT(*) FROM sync_log WHERE food_source_id = :sid AND notes = 'usda_search_cache'"),
        {"sid": str(usda_source_id)},
    ).scalar()
    assert log_count == 1


def test_upsert_updates_source_fetched_at_on_second_call(db_session):
    usda_service._nutrient_id_cache.clear()

    with patch("porquilo.services.usda_service.try_normalize_inline"):
        food1, _ = upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()
    ts1 = food1.source_fetched_at

    import time
    time.sleep(0.01)

    food2, _ = upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
    db_session.flush()
    ts2 = food2.source_fetched_at

    assert ts2 >= ts1


# ---------------------------------------------------------------------------
# GET /api/foods — two-pass integration
# ---------------------------------------------------------------------------


def test_get_foods_calls_usda_when_cache_empty(client, db_session):
    """When local results < limit, search_usda and upsert_usda_food are both called."""
    with patch("porquilo.routers.foods.search_usda", return_value=[_USDA_CHICKEN_FOOD]) as mock_search:
        with patch("porquilo.routers.foods.upsert_usda_food", return_value=(MagicMock(), False)) as mock_upsert:
            resp = client.get("/api/foods", params={"q": "chicken"})

    assert resp.status_code == 200
    mock_search.assert_called_once()
    mock_upsert.assert_called_once()


def test_get_foods_no_usda_on_cache_hit(client, db_session):
    """When local results already satisfy limit, USDA is not called."""
    usda_source_id = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'usda'")
    ).scalar()
    nutrient_id = db_session.execute(
        sa.text("SELECT id FROM nutrient_definitions WHERE key = 'calories_kcal'")
    ).scalar()

    # Insert enough foods to fill the default limit (20).
    for i in range(20):
        fid = uuid.uuid4().hex
        db_session.execute(
            sa.text(
                "INSERT INTO foods (id, name, food_source_id, default_unit, created_at, updated_at) "
                "VALUES (:id, :name, :src, 'g', datetime('now'), datetime('now'))"
            ),
            {"id": fid, "name": f"Chicken Item {i:02d}", "src": str(usda_source_id)},
        )
        db_session.execute(
            sa.text(
                "INSERT INTO food_nutrients (id, food_id, nutrient_id, value_per_100) "
                "VALUES (:id, :fid, :nid, 100)"
            ),
            {"id": uuid.uuid4().hex, "fid": fid, "nid": str(nutrient_id)},
        )

    with patch("porquilo.routers.foods.search_usda") as mock_search:
        resp = client.get("/api/foods", params={"q": "chicken", "limit": 20})

    assert resp.status_code == 200
    assert len(resp.json()) == 20
    mock_search.assert_not_called()


def test_get_foods_no_usda_without_q(client, db_session):
    with patch("porquilo.routers.foods.search_usda") as mock_search:
        resp = client.get("/api/foods")

    assert resp.status_code == 200
    mock_search.assert_not_called()


def test_get_foods_no_usda_short_q(client, db_session):
    with patch("porquilo.routers.foods.search_usda") as mock_search:
        resp = client.get("/api/foods", params={"q": "c"})

    assert resp.status_code == 200
    mock_search.assert_not_called()


def test_get_foods_returns_local_on_usda_failure(client, db_session):
    """If USDA returns [], local results are returned without error."""
    usda_source_id = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'custom'")
    ).scalar()
    nutrient_id = db_session.execute(
        sa.text("SELECT id FROM nutrient_definitions WHERE key = 'calories_kcal'")
    ).scalar()

    fid = uuid.uuid4().hex
    db_session.execute(
        sa.text(
            "INSERT INTO foods (id, name, food_source_id, default_unit, created_at, updated_at) "
            "VALUES (:id, 'Chicken Salad', :src, 'g', datetime('now'), datetime('now'))"
        ),
        {"id": fid, "src": str(usda_source_id)},
    )
    db_session.execute(
        sa.text(
            "INSERT INTO food_nutrients (id, food_id, nutrient_id, value_per_100) VALUES (:id, :fid, :nid, 200)"
        ),
        {"id": uuid.uuid4().hex, "fid": fid, "nid": str(nutrient_id)},
    )

    with patch("porquilo.routers.foods.search_usda", return_value=[]):
        resp = client.get("/api/foods", params={"q": "chicken"})

    assert resp.status_code == 200
    assert any(f["name"] == "Chicken Salad" for f in resp.json())


# ---------------------------------------------------------------------------
# upsert_usda_food — normalization integration
# ---------------------------------------------------------------------------


def test_upsert_sets_pending_and_calls_try_normalize_inline_on_insert(db_session):
    """INSERT sets display_name_status='pending' and calls try_normalize_inline with that food."""
    usda_service._nutrient_id_cache.clear()

    calls = []

    def _capture(food_id, session):
        # Record status at the moment try_normalize_inline is invoked.
        f = session.get(Food, food_id)
        calls.append({"id": food_id, "status": f.display_name_status if f else None})

    with patch("porquilo.services.usda_service.try_normalize_inline", side_effect=_capture):
        food, is_new = upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()

    assert is_new is True
    assert len(calls) == 1
    assert calls[0]["id"] == food.id
    assert calls[0]["status"] == "pending"


def test_upsert_does_not_reset_display_name_on_update(db_session):
    """Second upsert (UPDATE path) does not touch display_name or display_name_status."""
    usda_service._nutrient_id_cache.clear()

    with patch("porquilo.services.usda_service.try_normalize_inline"):
        food, _ = upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()

    # Force a known display_name state after first insert.
    food.display_name = "My Display Name"
    food.display_name_status = "done"
    db_session.flush()

    # Second upsert — UPDATE path; try_normalize_inline must NOT be called.
    with patch("porquilo.services.usda_service.try_normalize_inline") as mock_normalize:
        food2, is_new2 = upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()

    assert is_new2 is False
    mock_normalize.assert_not_called()
    db_session.refresh(food2)
    assert food2.display_name == "My Display Name"
    assert food2.display_name_status == "done"


def test_normalize_and_store_sets_display_name_when_llm_responds(db_session):
    """normalize_and_store (called inline by try_normalize_inline) sets display_name when LLM is fast.

    Tests the real DB mutation without threading to avoid savepoint leak in tests.
    The threading/timeout wrapper is tested separately in test_name_normalization_service.py.
    """
    from porquilo.models import Food as _Food
    from porquilo.services.name_normalization import normalize_and_store

    usda_source_id = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'usda'")
    ).scalar()

    import uuid as _uuid
    food = _Food(
        name="Chicken, broilers or fryers, breast",
        food_source_id=_uuid.UUID(str(usda_source_id)),
        display_name_status="pending",
    )
    db_session.add(food)
    db_session.flush()

    with patch("porquilo.services.name_normalization.normalize_food_name", return_value="Chicken Breast"), \
         patch("porquilo.services.name_normalization.is_llm_configured", return_value=True):
        normalize_and_store(food.id, db_session)

    db_session.refresh(food)
    assert food.display_name == "Chicken Breast"
    assert food.display_name_status == "done"


def test_upsert_inline_normalize_timeout_food_still_returned(db_session):
    """When try_normalize_inline's thread times out, upsert still returns the food.

    Mocks the ThreadPoolExecutor so no real thread (and no session commit) runs.
    """
    import concurrent.futures

    usda_service._nutrient_id_cache.clear()

    mock_future = MagicMock()
    mock_future.result.side_effect = concurrent.futures.TimeoutError()

    with patch("porquilo.services.name_normalization.concurrent.futures.ThreadPoolExecutor") as mock_cls:
        mock_executor = MagicMock()
        mock_executor.__enter__ = MagicMock(return_value=mock_executor)
        mock_executor.__exit__ = MagicMock(return_value=False)
        mock_executor.submit.return_value = mock_future
        mock_cls.return_value = mock_executor

        food, is_new = upsert_usda_food(_USDA_CHICKEN_FOOD, db_session)
        db_session.flush()

    assert is_new is True
    assert food is not None
    assert food.id is not None
