from __future__ import annotations

import logging
import os
from typing import Optional

from sqlmodel import Session

logger = logging.getLogger(__name__)

LLM_TIMEOUT_SECONDS: float = float(os.environ.get("LLM_TIMEOUT_SECONDS", "2.5"))

_PROMPT_SETTINGS_KEY = "food_name_normalization_prompt"

DEFAULT_FOOD_NAME_NORMALIZATION_PROMPT: str = (
    "You convert USDA food database descriptions into short, natural food names. USDA "
    "descriptions follow a bibliographic inversion format like 'Chicken, breast, boneless, "
    "skinless, raw'. Return only the natural name, nothing else. Examples: 'Chicken, breast, "
    "boneless, skinless, raw' → 'Boneless skinless chicken breast, raw'. 'Butter, salted' → "
    "'Salted butter'. 'Beef, ground, 80% lean meat / 20% fat, raw' → 'Ground beef (80/20), "
    "raw'. Never add explanations."
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
