"""
Alembic async migration environment for FairSplit.

Uses SQLAlchemy 2.0 async engine pattern with NullPool for migrations.
DATABASE_URL is loaded from the environment — never hardcoded.

Import order is critical: all models must be imported before Base.metadata
is accessed, otherwise autogenerate will see an empty schema.

Base lives in app.database. All model files import from app.database, so
importing each model here causes them to register their Table objects against
the single shared Base.metadata before Alembic inspects it.
"""

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import Base first — this is the declarative base used by all models.
from app.database import Base  # noqa: F401

# Import all models so their Table objects register against Base.metadata.
# If any model is omitted here, autogenerate will miss it and the migration
# will not include that table's schema.
from app.models.group import Group  # noqa: F401
from app.models.member import Member  # noqa: F401
from app.models.expense import Expense  # noqa: F401
from app.models.expense_split import ExpenseSplit  # noqa: F401
from app.models.settlement import Settlement  # noqa: F401
from app.models.idempotency_key import IdempotencyKey  # noqa: F401

# Alembic Config object — gives access to alembic.ini values
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load DATABASE_URL from environment — never fall back to a hardcoded value.
# In local development this is set by docker-compose.
# In CI it is set as a GitHub Actions secret.
# In production it is a Fly.io or VPS environment secret.
database_url = os.environ["DATABASE_URL"]
config.set_main_option("sqlalchemy.url", database_url)

# SQLAlchemy MetaData for autogenerate support
target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    """Configure migration context and run migrations synchronously."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Compare server defaults so autogenerate catches DEFAULT changes
        compare_server_defaults=True,
        # Compare type changes
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine, connect, and run migrations synchronously via run_sync."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        # NullPool is mandatory for Alembic: migrations must not use connection
        # pooling since each migration should open and close its own connection.
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point called by Alembic when running in online mode."""
    asyncio.run(run_async_migrations())


run_migrations_online()
