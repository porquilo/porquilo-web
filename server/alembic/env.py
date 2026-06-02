import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine

from alembic import context

# Ensure the src/ package root is on sys.path. The editable-install .pth file
# that hatchling writes is not always processed (e.g. Python 3.14 venv quirk),
# so we add it explicitly here as a fallback.
_src = os.path.join(os.path.dirname(__file__), "..", "src")
if _src not in sys.path:
    sys.path.insert(0, os.path.abspath(_src))

from sqlmodel import SQLModel
from porquilo.core.config import settings
import porquilo.models

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Tests may pass a live connection via cfg.attributes["connection"] so that
    # in-memory SQLite (or any pre-opened connection) is reused rather than a
    # new engine being created from the URL.
    if "connection" in config.attributes:
        connection = config.attributes["connection"]
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()
        return

    # Prefer an explicit URL from the config (e.g. set by tests); fall back to
    # the application settings so the default alembic.ini placeholder is ignored.
    url = config.get_main_option("sqlalchemy.url")
    if not url or url == "driver://user:pass@localhost/dbname":
        url = settings.database_url

    connectable = create_engine(url)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
