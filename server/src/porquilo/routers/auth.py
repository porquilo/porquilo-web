from fastapi import APIRouter, Depends, Header, Request
from pydantic import BaseModel
from sqlmodel import Session, select

from porquilo.core.database import get_session
from porquilo.core.deps import get_current_user
from porquilo.core.errors import raise_auth_error
from porquilo.core.limiter import limiter
from porquilo.models.user import User
from porquilo.services.auth_service import (
    create_token,
    hash_password,
    revoke_token,
    verify_password,
)

router = APIRouter()


class LoginBody(BaseModel):
    username: str
    password: str


class ChangePasswordBody(BaseModel):
    current_password: str
    new_password: str


@router.post("/auth/token")
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginBody,
    session: Session = Depends(get_session),
) -> dict:
    user = session.execute(select(User).where(User.username == body.username)).scalars().first()
    if user is None or not verify_password(body.password, user.hashed_password):
        raise_auth_error("invalid_credentials")
    if not user.is_active:
        raise_auth_error("account_deactivated")
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


@router.post("/auth/logout", status_code=204)
def logout(
    authorization: str | None = Header(default=None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    if token:
        revoke_token(token, session)
        session.commit()


@router.patch("/auth/password")
def change_password(
    body: ChangePasswordBody,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> dict:
    if not verify_password(body.current_password, current_user.hashed_password):
        raise_auth_error("invalid_credentials")
    current_user.hashed_password = hash_password(body.new_password)
    session.add(current_user)
    session.commit()
    return {"message": "Password updated."}
