from __future__ import annotations

import logging
import os
from typing import Optional

from sqlmodel import Session

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS: float = float(os.environ.get("LLM_TIMEOUT_SECONDS", "10"))

_PROMPT_SETTINGS_KEY = "food_name_normalization_prompt"

DEFAULT_FOOD_NAME_NORMALIZATION_PROMPT = (
    "You are a food name normalizer. "
    "Given a raw food product name, return a clean, concise, human-readable display name "
    "in sentence case. Remove packaging details and redundant modifiers. "
    "Return only the normalized name — no explanation, no surrounding punctuation."
)


def is_llm_configured() -> bool:
    return bool(os.environ.get("LLM_BASE_URL"))


def normalize_food_name(food_name: str, session: Session) -> Optional[str]:
    if not is_llm_configured():
        return None

    from porquilo.models.app_setting import AppSetting

    row = session.get(AppSetting, _PROMPT_SETTINGS_KEY)
    system_prompt = (
        (row.value if row and row.value else None)
        or DEFAULT_FOOD_NAME_NORMALIZATION_PROMPT
    )

    try:
        from openai import OpenAI

        client = OpenAI(
            base_url=os.environ["LLM_BASE_URL"],
            api_key=os.environ.get("LLM_API_KEY", "not-needed"),
            timeout=LLM_TIMEOUT_SECONDS,
        )
        model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": food_name},
            ],
        )
        result = response.choices[0].message.content
        return result.strip() if result else None
    except Exception:
        logger.debug("LLM call failed for %r", food_name, exc_info=True)
        return None
