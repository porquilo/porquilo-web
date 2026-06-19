import sys

from sqlmodel import Session, create_engine, select

from porquilo.core.config import settings
from porquilo.models.user import User
from porquilo.services.auth_service import hash_password, revoke_all_tokens


def reset_password(username: str, new_password: str) -> int:
    engine = create_engine(settings.database_url)
    with Session(engine) as session:
        user = session.execute(select(User).where(User.username == username)).scalars().first()
        if user is None:
            print(f"No user found with username '{username}'.")
            return 1

        user.hashed_password = hash_password(new_password)
        session.add(user)
        session.commit()

        revoke_all_tokens(user.id, session)
        session.commit()

        print(f"Password updated for {username}.")
        return 0


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: porquilo-server <command> [args]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "reset-password":
        if len(sys.argv) != 4:
            print("Usage: porquilo-server reset-password <username> <new_password>")
            sys.exit(1)
        username, new_password = sys.argv[2], sys.argv[3]
        sys.exit(reset_password(username, new_password))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
