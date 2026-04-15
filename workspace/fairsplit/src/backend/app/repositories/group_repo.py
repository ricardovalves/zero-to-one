"""Data access layer for groups and members."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.expense import Expense
from app.models.group import Group
from app.models.member import Member


class GroupRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        name: str,
        description: str | None,
        default_currency: str,
    ) -> Group:
        group = Group(
            id=uuid.uuid4(),
            name=name,
            description=description,
            invite_token=uuid.uuid4(),
            status="active",
            default_currency=default_currency,
        )
        self._session.add(group)
        await self._session.flush()  # populate DB-generated fields
        await self._session.refresh(group)
        return group

    async def get_by_id(self, group_id: uuid.UUID) -> Group | None:
        result = await self._session.execute(
            select(Group).where(Group.id == group_id)
        )
        return result.scalar_one_or_none()

    async def get_by_invite_token(self, invite_token: uuid.UUID) -> Group | None:
        result = await self._session.execute(
            select(Group).where(Group.invite_token == invite_token)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        group_id: uuid.UUID,
        **kwargs: object,
    ) -> Group | None:
        kwargs["updated_at"] = datetime.now(timezone.utc)
        await self._session.execute(
            update(Group).where(Group.id == group_id).values(**kwargs)
        )
        return await self.get_by_id(group_id)

    async def regenerate_invite_token(self, group_id: uuid.UUID) -> uuid.UUID:
        new_token = uuid.uuid4()
        await self._session.execute(
            update(Group)
            .where(Group.id == group_id)
            .values(invite_token=new_token, updated_at=datetime.now(timezone.utc))
        )
        return new_token

    async def get_member_count(self, group_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(Member.id)).where(Member.group_id == group_id)
        )
        return int(result.scalar() or 0)

    async def get_expense_count(self, group_id: uuid.UUID) -> int:
        result = await self._session.execute(
            select(func.count(Expense.id)).where(
                Expense.group_id == group_id,
                Expense.deleted_at.is_(None),
            )
        )
        return int(result.scalar() or 0)
