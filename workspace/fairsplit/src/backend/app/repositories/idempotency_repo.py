"""Data access layer for idempotency keys."""

from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import delete, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.idempotency_key import IdempotencyKey


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, key: uuid.UUID) -> IdempotencyKey | None:
        """Return an unexpired idempotency key record, or None."""
        # Use func.now() (server-side) to avoid offset-naive vs offset-aware
        # mismatch when comparing Python datetimes against TIMESTAMP WITHOUT
        # TIME ZONE columns via asyncpg.
        result = await self._session.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.key == key,
                IdempotencyKey.expires_at > func.now(),
            )
        )
        return result.scalar_one_or_none()

    async def store(
        self,
        key: uuid.UUID,
        endpoint: str,
        response_body: dict,
        status_code: int,
        ttl_hours: int = 24,
    ) -> None:
        """Persist an idempotency key with its response payload."""
        # expires_at is computed server-side to avoid timezone mismatch.
        # created_at uses the column server_default (func.now()).
        record = IdempotencyKey(
            key=key,
            endpoint=endpoint,
            response_body=response_body,
            status_code=status_code,
            expires_at=text(f"NOW() + INTERVAL '{ttl_hours} hours'"),
        )
        self._session.add(record)

    async def cleanup_expired(self) -> int:
        """Delete expired idempotency keys. Returns number of deleted rows."""
        result = await self._session.execute(
            delete(IdempotencyKey).where(IdempotencyKey.expires_at <= func.now())
        )
        return result.rowcount  # type: ignore[return-value]
