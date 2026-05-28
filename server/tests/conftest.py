import os
import tempfile

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config


def _alembic_cfg(url: str) -> Config:
    cfg = Config(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    cfg.attributes["configure_logger"] = False
    return cfg


@pytest.fixture(params=["sqlite", "pg"])
def engine(request, tmp_path):
    if request.param == "sqlite":
        db_file = tmp_path / "test.db"
        url = f"sqlite:///{db_file}"
        cfg = _alembic_cfg(url)
        command.upgrade(cfg, "001")
        eng = sa.create_engine(url)
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
