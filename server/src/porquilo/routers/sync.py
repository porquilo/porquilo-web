from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models import FoodSource
from porquilo.services.off_import_service import import_off_dataset

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])


class SyncStatus(BaseModel):
    status: Optional[str]
    last_synced_at: Optional[str]
    error: Optional[str]


def _run_off_import() -> None:
    from porquilo.core.database import engine
    from sqlmodel import Session as _Session

    with _Session(engine) as session:
        try:
            import_off_dataset(session)
        except Exception:
            logger.exception("OFF background import failed")


@router.post("/off", status_code=202)
def trigger_off_sync(
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
) -> dict:
    off_source = session.execute(
        select(FoodSource).where(FoodSource.key == "open_food_facts")
    ).scalars().first()

    if off_source is None:
        raise HTTPException(status_code=500, detail="open_food_facts food source not found")

    if off_source.sync_status == "running":
        raise HTTPException(status_code=409, detail="OFF sync already running")

    off_source.sync_status = "queued"
    off_source.sync_error = None
    session.commit()

    background_tasks.add_task(_run_off_import)
    return {"status": "queued"}


@router.get("/off/status", response_model=SyncStatus)
def get_off_sync_status(session: Session = Depends(get_session)) -> SyncStatus:
    off_source = session.execute(
        select(FoodSource).where(FoodSource.key == "open_food_facts")
    ).scalars().first()

    if off_source is None:
        return SyncStatus(status=None, last_synced_at=None, error=None)

    return SyncStatus(
        status=off_source.sync_status,
        last_synced_at=(
            off_source.last_synced_at.isoformat() if off_source.last_synced_at else None
        ),
        error=off_source.sync_error,
    )
