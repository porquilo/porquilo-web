import os
import tempfile

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy import event


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


@pytest.fixture(params=["sqlite", "pg"])
def engine(request, tmp_path):
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
