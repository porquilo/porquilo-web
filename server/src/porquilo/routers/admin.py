from __future__ import annotations

import time

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.core.deps import require_admin
from porquilo.core.llm import is_llm_configured
from porquilo.models.food import Food
from porquilo.models.food_source import FoodSource
from porquilo.models.user import User
from porquilo.services.name_normalization import normalize_and_store

router = APIRouter(prefix="/admin", tags=["admin"])

_BATCH_SIZE = 20
_BATCH_SLEEP = 0.5


class NormalizeNamesResult(BaseModel):
    processed: int
    done: int
    failed: int
    skipped: int


@router.post("/normalize-names", response_model=NormalizeNamesResult)
def normalize_names(session: Session = Depends(get_session), current_user: User = Depends(require_admin)):
    if not is_llm_configured():
        return JSONResponse(status_code=400, content={"error": "LLM not configured"})

    usda_source = session.execute(
        select(FoodSource).where(FoodSource.key == "usda")
    ).scalars().first()
    if usda_source is None:
        return NormalizeNamesResult(processed=0, done=0, failed=0, skipped=0)

    foods = session.execute(
        select(Food).where(
            Food.food_source_id == usda_source.id,
            Food.display_name_status.in_(["pending", "failed"]),
        )
    ).scalars().all()

    processed = 0
    done = 0
    failed = 0
    skipped = 0

    for i in range(0, len(foods), _BATCH_SIZE):
        batch = foods[i : i + _BATCH_SIZE]
        for food in batch:
            normalize_and_store(food.id, session)
            processed += 1
            status = food.display_name_status
            if status == "done":
                done += 1
            elif status == "failed":
                failed += 1
            elif status == "skipped":
                skipped += 1

        if i + _BATCH_SIZE < len(foods):
            time.sleep(_BATCH_SLEEP)

    return NormalizeNamesResult(processed=processed, done=done, failed=failed, skipped=skipped)
