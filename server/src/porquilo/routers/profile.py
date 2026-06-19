from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from porquilo.core.database import get_session
from porquilo.core.deps import get_current_user
from porquilo.core.errors import PorquiloError
from porquilo.models.user import User

router = APIRouter(prefix="/profile", tags=["profile"])

_VALID_UNITS_PREFERENCE = {"metric", "imperial"}


class ProfileRead(BaseModel):
    name: Optional[str]
    units_preference: Optional[str]
    timezone: Optional[str]


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    units_preference: Optional[str] = None
    timezone: Optional[str] = None


@router.get("", response_model=ProfileRead)
def get_profile(current_user: User = Depends(get_current_user)) -> ProfileRead:
    return ProfileRead.model_validate(current_user, from_attributes=True)


@router.patch("", response_model=ProfileRead)
def update_profile(
    body: ProfileUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> ProfileRead:
    if body.units_preference is not None and body.units_preference not in _VALID_UNITS_PREFERENCE:
        raise PorquiloError(
            code="validation_error",
            message="units_preference must be 'metric' or 'imperial'.",
            status_code=422,
        )

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    session.add(current_user)
    session.commit()

    return ProfileRead.model_validate(current_user, from_attributes=True)
