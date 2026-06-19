import os
import tempfile
import warnings

import pytest

# Auto-detect OrbStack's Docker socket when the standard socket is absent or broken.
# /var/run/docker.sock may exist as a symlink but resolve to a missing target.
_ORBSTACK_SOCK = os.path.expanduser("~/.orbstack/run/docker.sock")
if (
    os.path.exists(_ORBSTACK_SOCK)
    and not os.path.exists("/var/run/docker.sock")
    and "DOCKER_HOST" not in os.environ
):
    os.environ["DOCKER_HOST"] = f"unix://{_ORBSTACK_SOCK}"
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


def _snapshot_pks(engine):
    """Record existing primary-key values for every table so a test's writes
    can be undone without tearing down the (expensive) module-scoped engine."""
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)
    snapshot = {}
    with engine.connect() as conn:
        for table in metadata.sorted_tables:
            pk_cols = list(table.primary_key.columns)
            if not pk_cols:
                continue
            rows = conn.execute(sa.select(*pk_cols)).fetchall()
            snapshot[table.name] = {tuple(row) for row in rows}
    return metadata, snapshot


def _restore_pks(engine, metadata, snapshot):
    """Delete any rows inserted since the snapshot, children first to respect FKs."""
    with engine.begin() as conn:
        for table in reversed(metadata.sorted_tables):
            pk_cols = list(table.primary_key.columns)
            if not pk_cols:
                continue
            keep = snapshot.get(table.name, set())
            current_rows = conn.execute(sa.select(*pk_cols)).fetchall()
            to_delete = [tuple(row) for row in current_rows if tuple(row) not in keep]
            if not to_delete:
                continue
            if len(pk_cols) == 1:
                col = pk_cols[0]
                conn.execute(sa.delete(table).where(col.in_([v[0] for v in to_delete])))
            else:
                for vals in to_delete:
                    cond = sa.and_(*(col == val for col, val in zip(pk_cols, vals)))
                    conn.execute(sa.delete(table).where(cond))


def _make_engine_fixture(target_revision: str):
    module_fixture_name = f"_module_engine_{target_revision}"

    @pytest.fixture(scope="module", params=["sqlite", "pg"], name=module_fixture_name)
    def _module_engine(request, tmp_path_factory):
        if request.param == "sqlite":
            db_file = tmp_path_factory.mktemp("db") / "test.db"
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

    # Module-scoped fixtures are only discovered by pytest's fixture scanner
    # when bound to a module attribute; closures alone aren't enough.
    globals()[module_fixture_name] = _module_engine

    # The per-test wrapper must statically declare the module fixture as a
    # parameter (not via request.getfixturevalue) so pytest propagates the
    # sqlite/pg parametrization and test IDs correctly. The fixture name is
    # only known at runtime, so build the function with exec.
    namespace: dict = {}
    exec(
        f"def _engine_outer({module_fixture_name}):\n"
        f"    metadata, snapshot = _snapshot_pks({module_fixture_name})\n"
        f"    yield {module_fixture_name}\n"
        f"    _restore_pks({module_fixture_name}, metadata, snapshot)\n",
        {"_snapshot_pks": _snapshot_pks, "_restore_pks": _restore_pks},
        namespace,
    )
    return pytest.fixture(namespace["_engine_outer"])


engine_001 = _make_engine_fixture("001")
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
engine_014 = _make_engine_fixture("014")
engine_015 = _make_engine_fixture("015")
engine_016 = _make_engine_fixture("016")


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
            # Disable pysqlite's implicit transaction management so that
            # conn.begin() → SAVEPOINT nesting works correctly for test isolation.
            # Without this, pysqlite doesn't issue BEGIN before SAVEPOINT, so
            # RELEASE SAVEPOINT commits to disk and tx.rollback() becomes a no-op.
            dbapi_conn.isolation_level = None

        @event.listens_for(eng, "begin")
        def _begin(conn):
            conn.exec_driver_sql("BEGIN")
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
    from contextlib import asynccontextmanager

    from fastapi.testclient import TestClient
    from porquilo.main import app

    @asynccontextmanager
    async def _noop_lifespan(app):
        yield

    original = app.router.lifespan_context
    app.router.lifespan_context = _noop_lifespan
    try:
        yield TestClient(app)
    finally:
        app.router.lifespan_context = original


@pytest.fixture
def test_user(db_session):
    from porquilo.services.auth_service import create_user
    user = create_user("testuser", "testpass", "member", db_session)
    db_session.commit()
    return user


@pytest.fixture
def auth_token(db_session, test_user):
    from porquilo.services.auth_service import create_token
    token = create_token(test_user.id, db_session)
    db_session.commit()
    return token


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_user(db_session):
    from porquilo.services.auth_service import create_user
    user = create_user("admin", "adminpass", "admin", db_session)
    db_session.commit()
    return user


@pytest.fixture
def admin_token(db_session, admin_user):
    from porquilo.services.auth_service import create_token
    token = create_token(admin_user.id, db_session)
    db_session.commit()
    return token


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}
