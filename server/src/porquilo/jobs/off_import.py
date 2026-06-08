"""Standalone OFF import job — run as: python -m porquilo.jobs.off_import

Creates its own database engine and session. Does not import from database.py
or any FastAPI app code. Clears sync_pid on exit regardless of outcome.
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from sqlalchemy import event
from sqlmodel import Session, create_engine, select

from porquilo.core.config import settings
from porquilo.models import FoodSource
from porquilo.services.off_import_service import import_off_dataset


def _log_file_path() -> Path | None:
    """Return a log file path next to porquilo.db, or None for in-memory/pg."""
    db_url = settings.database_url
    if not db_url.startswith("sqlite:///"):
        return None
    # sqlite:///./porquilo.db  or  sqlite:////data/porquilo.db
    file_part = db_url[len("sqlite:///"):]
    if not file_part or file_part == ":memory:":
        return None
    db_path = Path(file_part)
    return db_path.parent / "porquilo_off_import.log"


def _configure_logging() -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    log_path = _log_file_path()
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=3))
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> int:
    _configure_logging()
    logger = logging.getLogger(__name__)

    db_url = settings.database_url
    engine = create_engine(db_url)

    @event.listens_for(engine, "connect")
    def set_wal_mode(dbapi_conn, connection_record):
        if engine.dialect.name == "sqlite":
            dbapi_conn.execute("PRAGMA journal_mode=WAL")

    success = False
    with Session(engine) as session:
        try:
            import_off_dataset(session)
            success = True
        except Exception:
            logger.exception("OFF import job failed")
        finally:
            off_source = session.execute(
                select(FoodSource).where(FoodSource.key == "open_food_facts")
            ).scalars().first()
            if off_source is not None:
                off_source.sync_pid = None
                try:
                    session.commit()
                except Exception:
                    logger.exception("Failed to clear sync_pid")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
