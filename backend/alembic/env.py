from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Ensure the backend package root is on sys.path so our models are importable
# when running alembic from the backend/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import the SQLAlchemy declarative Base and all model classes so alembic
# can reflect the full schema for autogenerate support.
from infrastructure.persistence.sql.models import Base  # noqa: E402

# Alembic Config object (gives access to alembic.ini values)
config = context.config

# Set up loggers from alembic.ini if a config file is present
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata

# Override the sqlalchemy.url from the SQL_URL environment variable so the
# same alembic setup works in all environments (SQLite for local dev,
# PostgreSQL for staging/prod) without editing alembic.ini.
sql_url = os.getenv("SQL_URL")
if sql_url:
    config.set_main_option("sqlalchemy.url", sql_url)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (SQL script output, no live DB)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Render AS IDENTITY instead of SERIAL for PostgreSQL
        render_as_batch=False,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (live DB connection)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # SQLite requires batch mode for ALTER TABLE support
            render_as_batch=connection.dialect.name == "sqlite",
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
