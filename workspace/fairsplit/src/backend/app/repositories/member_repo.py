"""Data access layer for members."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.member import Member


class MemberRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        group_id: uuid.UUID,
        display_name: str,
        is_admin: bool = False,
    ) -> Member:
        member = Member(
            id=uuid.uuid4(),
            group_id=group_id,
            display_name=display_name,
            is_admin=is_admin,
        )
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def get_by_id(self, member_id: uuid.UUID) -> Member | None:
        result = await self._session.execute(
            select(Member).where(Member.id == member_id)
        )
        return result.scalar_one_or_none()

    async def list_by_group(self, group_id: uuid.UUID) -> list[Member]:
        result = await self._session.execute(
            select(Member)
            .where(Member.group_id == group_id)
            .order_by(Member.display_name.asc())
        )
        return list(result.scalars().all())

    async def list_display_names(self, group_id: uuid.UUID) -> list[str]:
        result = await self._session.execute(
            select(Member.display_name).where(Member.group_id == group_id)
        )
        return list(result.scalars().all())

    async def resolve_unique_display_name(
        self, group_id: uuid.UUID, requested_name: str
    ) -> str:
        """Ensure uniqueness within a group by appending (2), (3), etc.

        Duplicate display names are allowed by design, but the server
        disambiguates them automatically.
        """
        existing = await self.list_display_names(group_id)
        existing_set = set(existing)

        if requested_name not in existing_set:
            return requested_name

        suffix = 2
        while True:
            candidate = f"{requested_name} ({suffix})"
            if candidate not in existing_set:
                return candidate
            suffix += 1
