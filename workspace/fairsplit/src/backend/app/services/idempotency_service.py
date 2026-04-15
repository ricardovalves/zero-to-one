"""Idempotency key check and store service.

Idempotency keys prevent double-submission on slow or unreliable connections.
The client generates a UUID when a form opens and sends it in X-Idempotency-Key
on every submit (including retries). The server checks this table before
processing any mutation; if the key exists and is not expired, it returns the
stored response without re-processing.

The 24-hour TTL means a retry storm lasting more than 24 hours would create
duplicates. This is acceptable — no real retry scenario exceeds 24 hours.

Implementation note: idempotency key check + store must happen INSIDE the
same transaction as the mutation. This prevents a race where two concurrent
requests with the same key both pass the check and both insert.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.idempotency_repo import IdempotencyRepository


async def check_idempotency(
    session: AsyncSession,
    idempotency_key: uuid.UUID | None,
) -> dict | None:
    """Check whether this idempotency key has already been processed.

    Returns the stored response body dict if the key exists and is not expired,
    or None if the key is new (request should be processed).

    If idempotency_key is None, always returns None (key is optional).
    """
    if idempotency_key is None:
        return None

    repo = IdempotencyRepository(session)
    existing = await repo.get(idempotency_key)
    if existing is not None:
        return existing.response_body

    return None


async def store_idempotency(
    session: AsyncSession,
    idempotency_key: uuid.UUID | None,
    endpoint: str,
    response_body: dict,
    status_code: int,
) -> None:
    """Store the idempotency key and its response payload.

    Must be called inside the same transaction as the mutation so that the
    key is stored atomically with the mutation's effects.

    If idempotency_key is None, this is a no-op.
    """
    if idempotency_key is None:
        return

    repo = IdempotencyRepository(session)
    await repo.store(
        key=idempotency_key,
        endpoint=endpoint,
        response_body=response_body,
        status_code=status_code,
    )
