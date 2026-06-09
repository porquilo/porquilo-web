from __future__ import annotations

import concurrent.futures
import logging
from uuid import UUID

from sqlmodel import Session

from porquilo.core.llm import LLM_TIMEOUT_SECONDS, is_llm_configured, normalize_food_name
from porquilo.models.food import Food
from porquilo.services.search_tokens import reindex_food

logger = logging.getLogger(__name__)


def normalize_and_store(food_id: UUID, session: Session) -> None:
    food = session.get(Food, food_id)
    if food is None:
        return

    reindex_food(food_id, session)
    session.commit()

    if food.display_name_status == "done":
        return

    food.display_name_status = "processing"
    session.commit()

    result = normalize_food_name(food.name, session)

    if result:
        food.display_name = result
        food.display_name_status = "done"
    elif is_llm_configured():
        food.display_name_status = "failed"
    else:
        food.display_name_status = "skipped"

    session.commit()


def try_normalize_inline(food_id: UUID, session: Session) -> None:
    timeout = LLM_TIMEOUT_SECONDS + 0.5
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(normalize_and_store, food_id, session)
            future.result(timeout=timeout)
    except Exception:
        pass
