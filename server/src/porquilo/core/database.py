from sqlalchemy import event
from sqlmodel import create_engine, Session
from porquilo.core.config import settings

engine = create_engine(settings.database_url)


@event.listens_for(engine, "connect")
def set_wal_mode(dbapi_conn, connection_record):
    if engine.dialect.name == "sqlite":
        dbapi_conn.execute("PRAGMA journal_mode=WAL")


def get_session():
    with Session(engine) as session:
        yield session