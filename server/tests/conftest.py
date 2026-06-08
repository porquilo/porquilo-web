import os
import tempfile
import warnings

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool


def _alembic_cfg(url: str) -> Config:
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.attributes["configure_logger"] = False
    return cfg


def _sqlite_engine(url: str) -> sa.Engine:
    eng = sa.create_engine(url)

    @event.listens_for(eng, "connect")
    def _set_fk_pragma(dbapi_conn, _rec):
        dbapi_conn.execute("PRAGMA foreign_keys = ON")

    return eng


def _make_engine_fixture(target_revision: str):
    @pytest.fixture(params=["sqlite", "pg"])
    def _engine(request, tmp_path):
        if request.param == "sqlite":
            db_file = tmp_path / "test.db"
            url = f"sqlite:///{db_file}"
            cfg = _alembic_cfg(url)
            command.upgrade(cfg, target_revision)
            eng = _sqlite_engine(url)
            yield eng
            eng.dispose()
            command.downgrade(cfg, "base")

        elif request.param == "pg":
            try:
                from testcontainers.postgres import PostgresContainer
            except ImportError:
                pytest.skip("testcontainers not installed")

            try:
                with PostgresContainer("postgres:16") as pg:
                    url = pg.get_connection_url()
                    cfg = _alembic_cfg(url)
                    command.upgrade(cfg, target_revision)
                    eng = sa.create_engine(url)
                    yield eng
                    eng.dispose()
                    command.downgrade(cfg, "base")
            except Exception as exc:
                pytest.skip(f"Docker unavailable: {exc}")

    return _engine


engine_002 = _make_engine_fixture("002")
engine_003 = _make_engine_fixture("003")
engine_004 = _make_engine_fixture("004")
engine_005 = _make_engine_fixture("005")
engine_006 = _make_engine_fixture("006")
engine_007 = _make_engine_fixture("007")
engine_008 = _make_engine_fixture("008")
engine_009 = _make_engine_fixture("009")
engine_010 = _make_engine_fixture("010")
engine_011 = _make_engine_fixture("011")
engine_012 = _make_engine_fixture("012")
engine_013 = _make_engine_fixture("013")


@pytest.fixture(params=["sqlite", "pg"])
def engine_001(request, tmp_path):
    if request.param == "sqlite":
        db_file = tmp_path / "test.db"
        url = f"sqlite:///{db_file}"
        cfg = _alembic_cfg(url)
        command.upgrade(cfg, "001")
        eng = _sqlite_engine(url)
        yield eng
        eng.dispose()
        command.downgrade(cfg, "base")

    elif request.param == "pg":
        try:
            from testcontainers.postgres import PostgresContainer
        except ImportError:
            pytest.skip("testcontainers not installed")

        try:
            with PostgresContainer("postgres:16") as pg:
                url = pg.get_connection_url()
                cfg = _alembic_cfg(url)
                command.upgrade(cfg, "001")
                eng = sa.create_engine(url)
                yield eng
                eng.dispose()
                command.downgrade(cfg, "base")
        except Exception as exc:
            pytest.skip(f"Docker unavailable: {exc}")


# ---------------------------------------------------------------------------
# API-layer test infrastructure
# Reads DATABASE_URL from the environment; falls back to in-memory SQLite.
# Switch databases by setting DATABASE_URL — no test code changes required.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def engine():
    # Suppress deprecation warning about date adapter in Python 3.12+
    warnings.filterwarnings("ignore", message=".*default date adapter is deprecated.*")
    
    url = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    if url.startswith("sqlite:"):
        pool_kwargs = {"poolclass": StaticPool} if url == "sqlite:///:memory:" else {}
        eng = sa.create_engine(url, connect_args={"check_same_thread": False}, **pool_kwargs)

        @event.listens_for(eng, "connect")
        def _fk(dbapi_conn, _rec):
            dbapi_conn.execute("PRAGMA foreign_keys = ON")
    else:
        eng = sa.create_engine(url)

    # Run migrations through the engine's own connection so that in-memory
    # SQLite shares the same database (Alembic would otherwise open a separate
    # :memory: connection and discard it immediately).
    cfg = _alembic_cfg(url)
    with eng.connect() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, "head")

    yield eng
    eng.dispose()


@pytest.fixture
def db_session(engine):
    with engine.connect() as conn:
        with conn.begin() as tx:
            with Session(conn, join_transaction_mode="create_savepoint") as session:
                yield session
            tx.rollback()


@pytest.fixture
def override_get_session(db_session):
    from porquilo.main import app
    from porquilo.core.database import get_session

    def _override():
        yield db_session

    app.dependency_overrides[get_session] = _override
    yield
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def client(override_get_session):
    from fastapi.testclient import TestClient
    from porquilo.main import app

    return TestClient(app)
