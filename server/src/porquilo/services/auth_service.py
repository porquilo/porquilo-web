import secrets
import uuid
from datetime import datetime, timezone

import bcrypt
from sqlmodel import Session, select

from porquilo.models.auth_token import AuthToken
from porquilo.models.user import User


def hash_password(plaintext: str) -> str:
    return bcrypt.hashpw(plaintext.encode(), bcrypt.gensalt()).decode()


def verify_password(plaintext: str, hashed: str) -> bool:
    return bcrypt.checkpw(plaintext.encode(), hashed.encode())


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def create_token(user_id: uuid.UUID, session: Session) -> str:
    token = generate_token()
    row = AuthToken(
        user_id=user_id,
        token=token,
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(row)
    return token


def revoke_token(token: str, session: Session) -> None:
    row = session.execute(select(AuthToken).where(AuthToken.token == token)).scalars().first()
    if row is not None:
        session.delete(row)


def revoke_all_tokens(user_id: uuid.UUID, session: Session) -> None:
    rows = session.execute(select(AuthToken).where(AuthToken.user_id == user_id)).scalars().all()
    for row in rows:
        session.delete(row)


def get_user_by_token(token: str, session: Session) -> User | None:
    statement = (
        select(User)
        .join(AuthToken, AuthToken.user_id == User.id)
        .where(AuthToken.token == token)
    )
    user = session.execute(statement).scalars().first()
    if user is None:
        return None
    auth_row = session.execute(
        select(AuthToken).where(AuthToken.token == token)
    ).scalars().first()
    if auth_row is not None:
        auth_row.last_used_at = datetime.now(timezone.utc).replace(tzinfo=None)
        session.add(auth_row)
    return user


def create_user(
    username: str,
    plaintext_password: str,
    role: str,
    session: Session,
) -> User:
    user = User(
        username=username,
        hashed_password=hash_password(plaintext_password),
        role=role,
    )
    session.add(user)
    return user
