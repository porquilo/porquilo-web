"""Tests for the break-glass `porquilo-server reset-password` CLI.

Verification checklist:
  - CLI reset-password updates hash and revokes tokens when run against the database
"""

from __future__ import annotations

from unittest.mock import patch

from sqlmodel import Session, select

from porquilo.cli import reset_password
from porquilo.models.auth_token import AuthToken
from porquilo.models.user import User
from porquilo.services.auth_service import create_token, create_user, verify_password


def test_reset_password_updates_hash_and_revokes_tokens(engine):
    with Session(engine) as session:
        user = create_user("clitest", "oldpassword", "member", session)
        session.commit()
        create_token(user.id, session)
        session.commit()
        user_id = user.id

    with patch("porquilo.cli.create_engine", return_value=engine):
        exit_code = reset_password("clitest", "newpassword")

    assert exit_code == 0

    with Session(engine) as session:
        refreshed = session.get(User, user_id)
        assert verify_password("newpassword", refreshed.hashed_password)
        assert not verify_password("oldpassword", refreshed.hashed_password)

        remaining_tokens = session.execute(
            select(AuthToken).where(AuthToken.user_id == user_id)
        ).scalars().all()
        assert remaining_tokens == []


def test_reset_password_unknown_user(engine, capsys):
    with patch("porquilo.cli.create_engine", return_value=engine):
        exit_code = reset_password("nosuchuser", "whatever")

    assert exit_code == 1
    assert "No user found" in capsys.readouterr().out
