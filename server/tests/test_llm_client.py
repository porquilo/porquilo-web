"""Tests for porquilo.core.llm (FD-5).

Covers the VERIFICATION checklist items:
  - is_llm_configured() returns False when LLM_BASE_URL is not set
  - normalize_food_name returns None immediately when LLM is not configured
  - normalize_food_name reads system prompt from app_settings when row is present
  - normalize_food_name falls back to DEFAULT_FOOD_NAME_NORMALIZATION_PROMPT when
    app_settings row is absent or value is null
  - normalize_food_name returns None (does not raise) on connection error
  - normalize_food_name returns None (does not raise) on timeout

All openai client calls are mocked — no live API calls.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import sqlalchemy as sa

from porquilo.core.llm import DEFAULT_FOOD_NAME_NORMALIZATION_PROMPT, is_llm_configured, normalize_food_name

_NOW = datetime(2026, 6, 6, 12, 0, 0, tzinfo=timezone.utc)

_PROMPT_KEY = "food_name_normalization_prompt"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_openai_client(response_text: str) -> MagicMock:
    """Return a mock OpenAI() instance that returns response_text from chat.completions.create."""
    msg = MagicMock()
    msg.content = response_text
    choice = MagicMock()
    choice.message = msg
    completion = MagicMock()
    completion.choices = [choice]

    client = MagicMock()
    client.chat.completions.create.return_value = completion
    return client


def _set_prompt_setting(db_session, value):
    db_session.execute(
        sa.text(
            "INSERT INTO app_settings (key, value, updated_at) VALUES (:k, :v, :ts)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value"
        ),
        {"k": _PROMPT_KEY, "v": value, "ts": _NOW},
    )


# ---------------------------------------------------------------------------
# is_llm_configured
# ---------------------------------------------------------------------------


def test_is_llm_configured_false_when_base_url_absent(monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    assert is_llm_configured() is False


def test_is_llm_configured_true_when_base_url_set(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    assert is_llm_configured() is True


# ---------------------------------------------------------------------------
# normalize_food_name: early return when not configured
# ---------------------------------------------------------------------------


def test_normalize_food_name_returns_none_when_not_configured(db_session, monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    result = normalize_food_name("Apple", db_session)
    assert result is None


def test_normalize_food_name_does_not_call_openai_when_not_configured(db_session, monkeypatch):
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    with patch("openai.OpenAI") as mock_cls:
        normalize_food_name("Apple", db_session)
    mock_cls.assert_not_called()


# ---------------------------------------------------------------------------
# normalize_food_name: system prompt selection
# ---------------------------------------------------------------------------


def test_normalize_food_name_uses_app_settings_prompt(db_session, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    custom_prompt = "Custom normalization prompt"
    _set_prompt_setting(db_session, custom_prompt)

    mock_client = _mock_openai_client("Apple juice")
    with patch("openai.OpenAI", return_value=mock_client):
        normalize_food_name("APPLE JUICE BLEND 1L", db_session)

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    messages = call_kwargs["messages"]
    system_msg = next(m for m in messages if m["role"] == "system")
    assert system_msg["content"] == custom_prompt


def test_normalize_food_name_falls_back_to_default_prompt_when_no_row(db_session, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    # No app_settings row for the prompt key — expect the default prompt.
    mock_client = _mock_openai_client("Apple juice")
    with patch("openai.OpenAI", return_value=mock_client):
        normalize_food_name("APPLE JUICE BLEND 1L", db_session)

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    messages = call_kwargs["messages"]
    system_msg = next(m for m in messages if m["role"] == "system")
    assert system_msg["content"] == DEFAULT_FOOD_NAME_NORMALIZATION_PROMPT


def test_normalize_food_name_falls_back_to_default_prompt_when_value_is_null(db_session, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    _set_prompt_setting(db_session, None)  # Row exists but value is NULL

    mock_client = _mock_openai_client("Apple juice")
    with patch("openai.OpenAI", return_value=mock_client):
        normalize_food_name("APPLE JUICE BLEND 1L", db_session)

    call_kwargs = mock_client.chat.completions.create.call_args[1]
    messages = call_kwargs["messages"]
    system_msg = next(m for m in messages if m["role"] == "system")
    assert system_msg["content"] == DEFAULT_FOOD_NAME_NORMALIZATION_PROMPT


# ---------------------------------------------------------------------------
# normalize_food_name: return value
# ---------------------------------------------------------------------------


def test_normalize_food_name_returns_stripped_response(db_session, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    mock_client = _mock_openai_client("  Apple juice  ")
    with patch("openai.OpenAI", return_value=mock_client):
        result = normalize_food_name("APPLE JUICE", db_session)
    assert result == "Apple juice"


# ---------------------------------------------------------------------------
# normalize_food_name: error handling
# ---------------------------------------------------------------------------


def test_normalize_food_name_returns_none_on_connection_error(db_session, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = ConnectionError("refused")
    with patch("openai.OpenAI", return_value=mock_client):
        result = normalize_food_name("Apple", db_session)
    assert result is None


def test_normalize_food_name_returns_none_on_timeout(db_session, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    import httpx

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = httpx.TimeoutException("timeout")
    with patch("openai.OpenAI", return_value=mock_client):
        result = normalize_food_name("Apple", db_session)
    assert result is None


def test_normalize_food_name_does_not_raise_on_unexpected_exception(db_session, monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "http://localhost:11434/v1")
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("unexpected")
    with patch("openai.OpenAI", return_value=mock_client):
        result = normalize_food_name("Apple", db_session)
    assert result is None
