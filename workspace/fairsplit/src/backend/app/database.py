"""Async SQLAlchemy engine and session factory.

One engine is created at startup and reused for all requests. Sessions are
provided per-request via the get_db dependency. Transactions are managed at
the service layer.

Base (DeclarativeBase) is defined here — all model files import from this
module. This ensures every model registers against the same metadata instance,
which is required for Alembic autogenerate to work correctly.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a database session per request.

    The session is closed after the request completes. Transactions
    are managed by service-layer code using `async with session.begin()`.
    """
    async with AsyncSessionLocal() as session:
        yield session


async def check_db_connection() -> bool:
    """Probe the database with a trivial query.

    Used by GET /api/v1/health to determine if the database is reachable.
    Returns True if the connection succeeds, False if any exception is raised.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
