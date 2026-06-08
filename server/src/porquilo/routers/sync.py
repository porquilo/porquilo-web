from __future__ import annotations

import logging
import subprocess
import sys
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models import FoodSource

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])


class SyncStatus(BaseModel):
    status: Optional[str]
    last_synced_at: Optional[str]
    error: Optional[str]
    sync_pid: Optional[int]
    sync_progress: Optional[int]
    sync_total: Optional[int]


@router.post("/off", status_code=202)
def trigger_off_sync(session: Session = Depends(get_session)) -> dict:
    off_source = session.execute(
        select(FoodSource).where(FoodSource.key == "open_food_facts")
    ).scalars().first()

    if off_source is None:
        raise HTTPException(status_code=500, detail="open_food_facts food source not found")

    if off_source.sync_status in ("running", "queued"):
        raise HTTPException(status_code=409, detail="OFF sync already running")

    off_source.sync_status = "queued"
    off_source.sync_pid = None
    off_source.sync_progress = None
    off_source.sync_total = None
    off_source.sync_error = None
    session.commit()

    process = subprocess.Popen(
        [sys.executable, "-m", "porquilo.jobs.off_import"],
        close_fds=True,
    )
    off_source.sync_pid = process.pid
    session.commit()

    return {"status": "queued"}


@router.get("/off/status", response_model=SyncStatus)
def get_off_sync_status(session: Session = Depends(get_session)) -> SyncStatus:
    off_source = session.execute(
        select(FoodSource).where(FoodSource.key == "open_food_facts")
    ).scalars().first()

    if off_source is None:
        return SyncStatus(
            status=None,
            last_synced_at=None,
            error=None,
            sync_pid=None,
            sync_progress=None,
            sync_total=None,
        )

    return SyncStatus(
        status=off_source.sync_status,
        last_synced_at=(
            off_source.last_synced_at.isoformat() if off_source.last_synced_at else None
        ),
        error=off_source.sync_error,
        sync_pid=off_source.sync_pid,
        sync_progress=off_source.sync_progress,
        sync_total=off_source.sync_total,
    )
