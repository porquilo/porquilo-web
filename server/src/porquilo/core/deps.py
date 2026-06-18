from fastapi import Depends, Header
from sqlmodel import Session

from porquilo.core.database import get_session
from porquilo.core.errors import raise_auth_error
from porquilo.models.user import User
from porquilo.services.auth_service import get_user_by_token


def get_current_user(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> User:
    token: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()

    if not token:
        raise_auth_error("token_revoked")

    user = get_user_by_token(token, session)
    if user is None:
        raise_auth_error("token_revoked")

    if not user.is_active:
        raise_auth_error("account_deactivated")

    session.commit()
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise_auth_error("insufficient_role")
    return current_user
