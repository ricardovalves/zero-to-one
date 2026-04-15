"""Data access layer for settlements."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.settlement import Settlement


class SettlementRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        group_id: uuid.UUID,
        payer_member_id: uuid.UUID,
        payee_member_id: uuid.UUID,
        amount_cents: int,
        currency: str,
    ) -> Settlement:
        settlement = Settlement(
            id=uuid.uuid4(),
            group_id=group_id,
            payer_member_id=payer_member_id,
            payee_member_id=payee_member_id,
            amount_cents=amount_cents,
            currency=currency,
        )
        self._session.add(settlement)
        await self._session.flush()
        return await self.get_by_id(settlement.id)  # type: ignore[return-value]

    async def get_by_id(self, settlement_id: uuid.UUID) -> Settlement | None:
        result = await self._session.execute(
            select(Settlement)
            .where(
                Settlement.id == settlement_id,
                Settlement.deleted_at.is_(None),
            )
            .options(
                selectinload(Settlement.payer),
                selectinload(Settlement.payee),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_including_deleted(self, settlement_id: uuid.UUID) -> Settlement | None:
        result = await self._session.execute(
            select(Settlement)
            .where(Settlement.id == settlement_id)
            .options(
                selectinload(Settlement.payer),
                selectinload(Settlement.payee),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_group(
        self, group_id: uuid.UUID, page: int, per_page: int
    ) -> tuple[list[Settlement], int]:
        count_result = await self._session.execute(
            select(func.count(Settlement.id)).where(
                Settlement.group_id == group_id,
                Settlement.deleted_at.is_(None),
            )
        )
        total = int(count_result.scalar() or 0)

        offset = (page - 1) * per_page
        result = await self._session.execute(
            select(Settlement)
            .where(
                Settlement.group_id == group_id,
                Settlement.deleted_at.is_(None),
            )
            .options(
                selectinload(Settlement.payer),
                selectinload(Settlement.payee),
            )
            .order_by(Settlement.created_at.desc())
            .limit(per_page)
            .offset(offset)
        )
        return list(result.scalars().all()), total

    async def soft_delete(self, settlement_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Settlement)
            .where(Settlement.id == settlement_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
