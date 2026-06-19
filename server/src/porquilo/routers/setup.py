from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.models.user import User
from porquilo.services.auth_service import create_token, create_user

router = APIRouter(prefix="/setup", tags=["setup"])


class SetupStatus(BaseModel):
    initialized: bool


class SetupInitBody(BaseModel):
    username: str
    password: str
    name: Optional[str] = None


@router.get("/status", response_model=SetupStatus)
def setup_status(session: Session = Depends(get_session)) -> SetupStatus:
    existing = session.execute(select(User)).scalars().first()
    return SetupStatus(initialized=existing is not None)


@router.post("/init")
def setup_init(
    body: SetupInitBody,
    session: Session = Depends(get_session),
) -> dict:
    existing = session.execute(select(User)).scalars().first()
    if existing is not None:
        raise HTTPException(status_code=404)

    user = create_user(body.username, body.password, "admin", session)
    if body.name is not None:
        user.name = body.name
    session.commit()

    token = create_token(user.id, session)
    session.commit()

    return {
        "token": token,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "role": user.role,
        },
    }
