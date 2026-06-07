"""Tests for POST /admin/normalize-names (FD-7 admin endpoint).

Covers the VERIFICATION checklist items:
  - Returns 400 when LLM is not configured
  - Processes only USDA foods with status 'pending' or 'failed'
  - Foods with status 'done' or 'skipped' are not reprocessed
  - Response counts (done, failed, skipped) are accurate after a run
  - Running the endpoint twice is safe — second run is a no-op for already-done foods
  - Tests use a mocked LLM client — no live API calls in CI
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, call, patch

import sqlalchemy as sa

from porquilo.models.food import Food


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _usda_source_id(db_session) -> uuid.UUID:
    row = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'usda'")
    ).fetchone()
    assert row is not None, "food_sources.usda not seeded"
    return uuid.UUID(str(row[0]))


def _custom_source_id(db_session) -> uuid.UUID:
    row = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'custom'")
    ).fetchone()
    assert row is not None, "food_sources.custom not seeded"
    return uuid.UUID(str(row[0]))


def _make_food(db_session, *, source_id: uuid.UUID, name: str, status: str | None) -> Food:
    food = Food(name=name, food_source_id=source_id, display_name_status=status)
    db_session.add(food)
    db_session.flush()
    return food


def _mock_normalize_done(food_id, session):
    """Side-effect: marks food as done (no commit — router reads via identity map)."""
    food = session.get(Food, food_id)
    food.display_name = "Normalized"
    food.display_name_status = "done"


def _mock_normalize_failed(food_id, session):
    """Side-effect: marks food as failed."""
    food = session.get(Food, food_id)
    food.display_name_status = "failed"


def _mock_normalize_skipped(food_id, session):
    """Side-effect: marks food as skipped."""
    food = session.get(Food, food_id)
    food.display_name_status = "skipped"


# ---------------------------------------------------------------------------
# 400 when LLM not configured
# ---------------------------------------------------------------------------


def test_normalize_names_returns_400_when_llm_not_configured(client):
    with patch("porquilo.routers.admin.is_llm_configured", return_value=False):
        resp = client.post("/admin/normalize-names")

    assert resp.status_code == 400
    assert resp.json() == {"error": "LLM not configured"}


# ---------------------------------------------------------------------------
# Only USDA foods with 'pending' or 'failed' status are processed
# ---------------------------------------------------------------------------


def test_normalize_names_processes_pending_and_failed_usda_foods(client, db_session):
    usda_id = _usda_source_id(db_session)
    custom_id = _custom_source_id(db_session)

    # USDA foods that should be processed
    pending = _make_food(db_session, source_id=usda_id, name="Apple, raw", status="pending")
    failed = _make_food(db_session, source_id=usda_id, name="Beef, ground", status="failed")

    # USDA foods that should NOT be processed
    _make_food(db_session, source_id=usda_id, name="Chicken, done", status="done")
    _make_food(db_session, source_id=usda_id, name="Salmon, skipped", status="skipped")

    # Custom food with pending status — should NOT be processed (wrong source)
    _make_food(db_session, source_id=custom_id, name="Custom pending", status="pending")

    processed_ids: list[uuid.UUID] = []

    def mock_normalize(food_id, session):
        processed_ids.append(food_id)
        _mock_normalize_done(food_id, session)

    with patch("porquilo.routers.admin.is_llm_configured", return_value=True), \
         patch("porquilo.routers.admin.normalize_and_store", side_effect=mock_normalize):
        resp = client.post("/admin/normalize-names")

    assert resp.status_code == 200
    data = resp.json()
    assert data["processed"] == 2
    assert data["done"] == 2
    assert data["failed"] == 0
    assert data["skipped"] == 0

    # Only the pending and failed USDA foods were normalized
    assert set(processed_ids) == {pending.id, failed.id}


# ---------------------------------------------------------------------------
# Response counts are accurate for mixed outcomes
# ---------------------------------------------------------------------------


def test_normalize_names_counts_reflect_final_status(client, db_session):
    usda_id = _usda_source_id(db_session)

    food_a = _make_food(db_session, source_id=usda_id, name="Food A", status="pending")
    food_b = _make_food(db_session, source_id=usda_id, name="Food B", status="pending")
    food_c = _make_food(db_session, source_id=usda_id, name="Food C", status="failed")

    outcomes = {
        food_a.id: _mock_normalize_done,
        food_b.id: _mock_normalize_failed,
        food_c.id: _mock_normalize_skipped,
    }

    def mock_normalize(food_id, session):
        outcomes[food_id](food_id, session)

    with patch("porquilo.routers.admin.is_llm_configured", return_value=True), \
         patch("porquilo.routers.admin.normalize_and_store", side_effect=mock_normalize):
        resp = client.post("/admin/normalize-names")

    assert resp.status_code == 200
    data = resp.json()
    assert data["processed"] == 3
    assert data["done"] == 1
    assert data["failed"] == 1
    assert data["skipped"] == 1


# ---------------------------------------------------------------------------
# Idempotency: second run is a no-op for already-done foods
# ---------------------------------------------------------------------------


def test_normalize_names_second_run_is_noop(client, db_session):
    """Use real normalize_and_store with a mocked LLM call so status is
    persisted correctly, then verify the second POST is a no-op."""
    usda_id = _usda_source_id(db_session)
    _make_food(db_session, source_id=usda_id, name="Apple, raw", status="pending")

    with patch("porquilo.routers.admin.is_llm_configured", return_value=True), \
         patch("porquilo.services.name_normalization.is_llm_configured", return_value=True), \
         patch("porquilo.services.name_normalization.normalize_food_name", return_value="Apple"):
        resp1 = client.post("/admin/normalize-names")
        resp2 = client.post("/admin/normalize-names")

    assert resp1.status_code == 200
    assert resp1.json()["processed"] == 1
    assert resp1.json()["done"] == 1

    # Second run finds no pending/failed foods — food is already "done"
    assert resp2.status_code == 200
    assert resp2.json()["processed"] == 0
    assert resp2.json()["done"] == 0


# ---------------------------------------------------------------------------
# Batching: sleep is called between batches (not after the last one)
# ---------------------------------------------------------------------------


def test_normalize_names_sleeps_between_batches_only(client, db_session):
    usda_id = _usda_source_id(db_session)

    # Create 21 foods — exactly one batch of 20 + one of 1 → one sleep between them
    for i in range(21):
        _make_food(db_session, source_id=usda_id, name=f"Food {i}", status="pending")

    def mock_normalize(food_id, session):
        _mock_normalize_done(food_id, session)

    with patch("porquilo.routers.admin.is_llm_configured", return_value=True), \
         patch("porquilo.routers.admin.normalize_and_store", side_effect=mock_normalize), \
         patch("porquilo.routers.admin.time") as mock_time:
        resp = client.post("/admin/normalize-names")

    assert resp.status_code == 200
    assert resp.json()["processed"] == 21
    # Sleep called exactly once (between batch 0 and batch 1)
    mock_time.sleep.assert_called_once_with(0.5)


# ---------------------------------------------------------------------------
# No sleep when all foods fit in one batch
# ---------------------------------------------------------------------------


def test_normalize_names_no_sleep_for_single_batch(client, db_session):
    usda_id = _usda_source_id(db_session)
    _make_food(db_session, source_id=usda_id, name="Apple", status="pending")

    def mock_normalize(food_id, session):
        _mock_normalize_done(food_id, session)

    with patch("porquilo.routers.admin.is_llm_configured", return_value=True), \
         patch("porquilo.routers.admin.normalize_and_store", side_effect=mock_normalize), \
         patch("porquilo.routers.admin.time") as mock_time:
        resp = client.post("/admin/normalize-names")

    assert resp.status_code == 200
    mock_time.sleep.assert_not_called()


# ---------------------------------------------------------------------------
# Empty result when there are no pending/failed USDA foods
# ---------------------------------------------------------------------------


def test_normalize_names_empty_when_nothing_to_process(client, db_session):
    usda_id = _usda_source_id(db_session)
    _make_food(db_session, source_id=usda_id, name="Already done", status="done")

    with patch("porquilo.routers.admin.is_llm_configured", return_value=True), \
         patch("porquilo.routers.admin.normalize_and_store") as mock_normalize:
        resp = client.post("/admin/normalize-names")

    assert resp.status_code == 200
    data = resp.json()
    assert data == {"processed": 0, "done": 0, "failed": 0, "skipped": 0}
    mock_normalize.assert_not_called()
