"""Alembic migration environment for amz-ad-tracker.

This file is invoked by the ``alembic`` CLI. It wires Alembic's
``context`` to:

1. The project's SQLAlchemy metadata (``backend.models.Base``)
2. The runtime database URL (``backend.config.settings.DATABASE_URL``)

so that ``alembic revision --autogenerate`` compares the live schema
against the model definitions and produces a diff migration.

For tests the in-memory SQLite database is created via
``Base.metadata.create_all`` directly in ``tests/conftest.py`` — tests
do NOT go through Alembic.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Import Base and settings so autogenerate can diff models against DB.
from backend.config import settings
from backend.models import Base

# This is the Alembic Config object, which provides access to values
# within the .ini file.
config = context.config

# Override the sqlalchemy.url placeholder from alembic.ini with the
# runtime DATABASE_URL. This way a single env.py serves dev, test, and
# prod without duplicating connection strings.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Configure Python logging from the .ini file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata used by autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Emits SQL to stdout / file instead of executing against a live db.
    Useful for generating patch scripts for review.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite requires render_as_batch for ALTER TABLE rewrites
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode against a live database engine."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite requires render_as_batch for ALTER TABLE rewrites
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
