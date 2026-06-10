from __future__ import annotations

import re
import uuid

import sqlalchemy as sa
from sqlmodel import Session

from porquilo.models.food import Food
from porquilo.models.food_search_token import FoodSearchToken


def tokenize(text: str | None) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    parts = re.split(r"[^a-z0-9]+", lowered)
    seen: set[str] = set()
    result: list[str] = []
    for p in parts:
        if len(p) >= 2 and p not in seen:
            seen.add(p)
            result.append(p)
    return result


def reindex_food(food_id: uuid.UUID, session: Session) -> None:
    food = session.get(Food, food_id)
    if food is None:
        return
    tokens = set(tokenize(food.name)) | set(tokenize(food.brand))
    session.execute(
        sa.delete(FoodSearchToken).where(FoodSearchToken.food_id == food_id)
    )
    for token in tokens:
        session.add(FoodSearchToken(food_id=food_id, token=token))
