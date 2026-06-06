"""Tests for porquilo.services.name_normalization (FD-6).

Covers the VERIFICATION checklist items:
  - normalize_and_store sets display_name and display_name_status='done' when
    mocked LLM returns a non-empty string
  - normalize_and_store sets display_name_status='failed' when mocked LLM returns None
    and LLM is configured
  - normalize_and_store sets display_name_status='skipped' when LLM is not configured
  - normalize_and_store is idempotent: calling it on a food with status 'done' is a no-op
  - normalize_and_store returns early without error for an unknown food_id
  - try_normalize_inline does not raise when the inner call times out
  - try_normalize_inline does not raise when normalize_and_store raises

Tests run against both SQLite and PostgreSQL by switching DATABASE_URL.
"""

from __future__ import annotations

import concurrent.futures
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import sqlalchemy as sa

from porquilo.models.food import Food
from porquilo.services.name_normalization import normalize_and_store, try_normalize_inline

_NOW = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _food_source_id(db_session) -> uuid.UUID:
    row = db_session.execute(
        sa.text("SELECT id FROM food_sources WHERE key = 'custom'")
    ).fetchone()
    assert row is not None, "food_sources.custom not seeded"
    return uuid.UUID(str(row[0]))


def _make_food(
    db_session,
    *,
    name: str = "Test Food",
    display_name: str | None = None,
    display_name_status: str | None = None,
) -> Food:
    food = Food(
        name=name,
        food_source_id=_food_source_id(db_session),
        display_name=display_name,
        display_name_status=display_name_status,
    )
    db_session.add(food)
    db_session.flush()
    return food


def _get_food(db_session, food_id: uuid.UUID) -> Food | None:
    return db_session.get(Food, food_id)


# ---------------------------------------------------------------------------
# normalize_and_store: happy path — LLM returns a name
# ---------------------------------------------------------------------------


def test_normalize_and_store_sets_done_on_success(db_session, monkeypatch):
    food = _make_food(db_session)
    food_id = food.id

    with patch("porquilo.services.name_normalization.normalize_food_name", return_value="Apple juice"), \
         patch("porquilo.services.name_normalization.is_llm_configured", return_value=True):
        normalize_and_store(food_id, db_session)

    refreshed = _get_food(db_session, food_id)
    assert refreshed.display_name == "Apple juice"
    assert refreshed.display_name_status == "done"


# ---------------------------------------------------------------------------
# normalize_and_store: LLM configured but returns None → failed
# ---------------------------------------------------------------------------


def test_normalize_and_store_sets_failed_when_llm_returns_none(db_session, monkeypatch):
    food = _make_food(db_session)
    food_id = food.id

    with patch("porquilo.services.name_normalization.normalize_food_name", return_value=None), \
         patch("porquilo.services.name_normalization.is_llm_configured", return_value=True):
        normalize_and_store(food_id, db_session)

    refreshed = _get_food(db_session, food_id)
    assert refreshed.display_name_status == "failed"
    assert refreshed.display_name is None


# ---------------------------------------------------------------------------
# normalize_and_store: LLM not configured → skipped
# ---------------------------------------------------------------------------


def test_normalize_and_store_sets_skipped_when_llm_not_configured(db_session, monkeypatch):
    food = _make_food(db_session)
    food_id = food.id

    with patch("porquilo.services.name_normalization.normalize_food_name", return_value=None), \
         patch("porquilo.services.name_normalization.is_llm_configured", return_value=False):
        normalize_and_store(food_id, db_session)

    refreshed = _get_food(db_session, food_id)
    assert refreshed.display_name_status == "skipped"
    assert refreshed.display_name is None


# ---------------------------------------------------------------------------
# normalize_and_store: idempotency — status 'done' is a no-op
# ---------------------------------------------------------------------------


def test_normalize_and_store_is_noop_when_status_is_done(db_session, monkeypatch):
    food = _make_food(db_session, display_name="Original name", display_name_status="done")
    food_id = food.id

    with patch("porquilo.services.name_normalization.normalize_food_name", return_value="New name") as mock_llm:
        normalize_and_store(food_id, db_session)

    mock_llm.assert_not_called()
    refreshed = _get_food(db_session, food_id)
    assert refreshed.display_name == "Original name"
    assert refreshed.display_name_status == "done"


# ---------------------------------------------------------------------------
# normalize_and_store: unknown food_id — returns without error
# ---------------------------------------------------------------------------


def test_normalize_and_store_no_error_for_unknown_food_id(db_session):
    unknown_id = uuid.uuid4()
    # Should not raise
    normalize_and_store(unknown_id, db_session)


# ---------------------------------------------------------------------------
# try_normalize_inline: does not raise on timeout
# ---------------------------------------------------------------------------


def test_try_normalize_inline_no_raise_on_timeout(db_session):
    food = _make_food(db_session)

    mock_future = MagicMock()
    mock_future.result.side_effect = concurrent.futures.TimeoutError()

    with patch("porquilo.services.name_normalization.concurrent.futures.ThreadPoolExecutor") as mock_executor_cls:
        mock_executor = MagicMock()
        mock_executor.__enter__ = MagicMock(return_value=mock_executor)
        mock_executor.__exit__ = MagicMock(return_value=False)
        mock_executor.submit.return_value = mock_future
        mock_executor_cls.return_value = mock_executor

        # Must not raise
        try_normalize_inline(food.id, db_session)


# ---------------------------------------------------------------------------
# try_normalize_inline: does not raise when normalize_and_store raises
# ---------------------------------------------------------------------------


def test_try_normalize_inline_no_raise_when_normalize_and_store_raises(db_session):
    food = _make_food(db_session)

    mock_future = MagicMock()
    mock_future.result.side_effect = RuntimeError("unexpected inner error")

    with patch("porquilo.services.name_normalization.concurrent.futures.ThreadPoolExecutor") as mock_executor_cls:
        mock_executor = MagicMock()
        mock_executor.__enter__ = MagicMock(return_value=mock_executor)
        mock_executor.__exit__ = MagicMock(return_value=False)
        mock_executor.submit.return_value = mock_future
        mock_executor_cls.return_value = mock_executor

        # Must not raise
        try_normalize_inline(food.id, db_session)
