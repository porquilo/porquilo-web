from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models.app_setting import AppSetting
from porquilo.services.settings_service import KNOWN_SETTINGS_KEYS, set_setting

router = APIRouter(prefix="/api/settings", tags=["settings"])

_MASKED = "••••••••"


class SettingRead(BaseModel):
    key: str
    value: Optional[str]
    is_set: bool


class SettingUpdate(BaseModel):
    value: Optional[str]


def _to_read(row: Optional[AppSetting], key: str) -> SettingRead:
    value = row.value if row else None
    if key == "off_password" and value is not None:
        return SettingRead(key=key, value=_MASKED, is_set=True)
    return SettingRead(key=key, value=value, is_set=bool(value))


@router.get("", response_model=list[SettingRead])
def list_settings(session: Session = Depends(get_session)) -> list[SettingRead]:
    rows = {r.key: r for r in session.exec(select(AppSetting)).all()}
    return [_to_read(rows.get(k), k) for k in sorted(KNOWN_SETTINGS_KEYS)]


@router.get("/{key}", response_model=SettingRead)
def get_setting_endpoint(key: str, session: Session = Depends(get_session)) -> SettingRead:
    if key not in KNOWN_SETTINGS_KEYS:
        raise HTTPException(status_code=404, detail=f"Unknown settings key: {key!r}")
    row = session.get(AppSetting, key)
    return _to_read(row, key)


@router.put("/{key}", response_model=SettingRead)
def update_setting(
    key: str,
    body: SettingUpdate,
    session: Session = Depends(get_session),
) -> SettingRead:
    if key not in KNOWN_SETTINGS_KEYS:
        raise HTTPException(status_code=422, detail=f"Unknown settings key: {key!r}")
    row = set_setting(key, body.value, session)
    session.commit()
    session.refresh(row)
    return _to_read(row, key)
