from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session

from porquilo.models.app_setting import AppSetting

KNOWN_SETTINGS_KEYS: frozenset[str] = frozenset(
    {
        "mealie_api_key",
        "mealie_url",
        "off_password",
        "off_username",
        "usda_api_key",
    }
)


def get_setting(key: str, session: Session) -> Optional[str]:
    row = session.get(AppSetting, key)
    return row.value if row else None


def set_setting(key: str, value: Optional[str], session: Session) -> AppSetting:
    if key not in KNOWN_SETTINGS_KEYS:
        raise ValueError(f"Unknown settings key: {key!r}")
    row = session.get(AppSetting, key)
    now = datetime.now(timezone.utc)
    if row is None:
        row = AppSetting(key=key, value=value, updated_at=now)
        session.add(row)
    else:
        row.value = value
        row.updated_at = now
    return row
