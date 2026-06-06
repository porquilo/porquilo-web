from __future__ import annotations

import logging
import os
from typing import Optional

from sqlmodel import Session

logger = logging.getLogger(__name__)

LLM_BASE_URL: str = os.environ.get("LLM_BASE_URL", "")
LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "ollama")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "gpt-4o-mini")
LLM_TIMEOUT_SECONDS: float = float(os.environ.get("LLM_TIMEOUT_SECONDS", "2.5"))

DEFAULT_FOOD_NAME_NORMALIZATION_PROMPT: str = (
    "You convert USDA food database descriptions into short, natural food names. USDA "
    "descriptions follow a bibliographic inversion format like 'Chicken, breast, boneless, "
    "skinless, raw'. Return only the natural name, nothing else. Examples: 'Chicken, breast, "
    "boneless, skinless, raw' → 'Boneless skinless chicken breast, raw'. 'Butter, salted' → "
    "'Salted butter'. 'Beef, ground, 80% lean meat / 20% fat, raw' → 'Ground beef (80/20), "
    "raw'. Never add explanations."
)


def is_llm_configured() -> bool:
    return bool(LLM_BASE_URL)


def normalize_food_name(raw_name: str, session: Session) -> Optional[str]:
    if not is_llm_configured():
        return None

    from porquilo.services.settings_service import get_setting

    system_prompt = (
        get_setting("llm.food_name_normalization_prompt", session)
        or DEFAULT_FOOD_NAME_NORMALIZATION_PROMPT
    )

    try:
        from openai import OpenAI

        client = OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": raw_name},
            ],
            timeout=LLM_TIMEOUT_SECONDS,
        )
        content = response.choices[0].message.content
        return content.strip() if content else None
    except Exception as exc:
        logger.debug("LLM normalization failed for %r: %s", raw_name, exc)
        return None
