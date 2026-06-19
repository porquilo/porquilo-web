from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.core.deps import require_admin
from porquilo.core.errors import PorquiloError
from porquilo.models.user import User
from porquilo.services.auth_service import create_user, hash_password, revoke_all_tokens

router = APIRouter(prefix="/users", tags=["users"])


class UserRead(BaseModel):
    id: uuid.UUID
    username: str
    role: str
    name: Optional[str]
    is_active: bool
    created_at: Optional[datetime]


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "member"
    name: Optional[str] = None


class UserUpdate(BaseModel):
    is_active: bool


class ResetPasswordBody(BaseModel):
    new_password: str


@router.get("", response_model=list[UserRead])
def list_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
) -> list[UserRead]:
    users = session.execute(select(User)).scalars().all()
    return [UserRead.model_validate(u, from_attributes=True) for u in users]


@router.post("", response_model=UserRead, status_code=201)
def create_user_route(
    body: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
) -> UserRead:
    existing = session.execute(
        select(User).where(User.username == body.username)
    ).scalars().first()
    if existing is not None:
        raise PorquiloError(
            code="username_taken",
            message="That username is already in use.",
            status_code=422,
        )
    user = create_user(body.username, body.password, body.role, session)
    if body.name is not None:
        user.name = body.name
    session.commit()
    return UserRead.model_validate(user, from_attributes=True)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
) -> UserRead:
    user = session.get(User, user_id)
    if user is None:
        raise PorquiloError(code="not_found", message="User not found.", status_code=404)

    if body.is_active is False and user.id == current_user.id:
        raise PorquiloError(
            code="cannot_deactivate_self",
            message="You can't deactivate your own account.",
            status_code=409,
        )

    user.is_active = body.is_active
    session.add(user)
    session.commit()

    if body.is_active is False:
        revoke_all_tokens(user.id, session)
        session.commit()

    return UserRead.model_validate(user, from_attributes=True)


@router.post("/{user_id}/reset-password")
def reset_password(
    user_id: uuid.UUID,
    body: ResetPasswordBody,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_admin),
) -> dict:
    user = session.get(User, user_id)
    if user is None:
        raise PorquiloError(code="not_found", message="User not found.", status_code=404)

    user.hashed_password = hash_password(body.new_password)
    session.add(user)
    session.commit()

    revoke_all_tokens(user.id, session)
    session.commit()

    return {"message": "Password reset."}
