"""Data access layer for expenses and expense splits."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import Select, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.member import Member


class ExpenseRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        group_id: uuid.UUID,
        payer_member_id: uuid.UUID,
        logged_by_member_id: uuid.UUID,
        description: str,
        amount_cents: int,
        currency: str,
        split_type: str,
        expense_date: date,
        splits: list[dict],  # [{"member_id": UUID, "amount_cents": int, "percentage": Decimal|None}]
    ) -> Expense:
        expense = Expense(
            id=uuid.uuid4(),
            group_id=group_id,
            payer_member_id=payer_member_id,
            logged_by_member_id=logged_by_member_id,
            description=description,
            amount_cents=amount_cents,
            currency=currency,
            split_type=split_type,
            expense_date=expense_date,
        )
        self._session.add(expense)
        await self._session.flush()

        for split_data in splits:
            split = ExpenseSplit(
                id=uuid.uuid4(),
                expense_id=expense.id,
                member_id=split_data["member_id"],
                amount_cents=split_data["amount_cents"],
                percentage=split_data.get("percentage"),
            )
            self._session.add(split)

        await self._session.flush()
        return await self.get_by_id(expense.id)  # type: ignore[return-value]

    async def get_by_id(self, expense_id: uuid.UUID) -> Expense | None:
        result = await self._session.execute(
            select(Expense)
            .where(Expense.id == expense_id, Expense.deleted_at.is_(None))
            .options(
                selectinload(Expense.payer),
                selectinload(Expense.logged_by),
                selectinload(Expense.splits).selectinload(ExpenseSplit.member),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_id_including_deleted(self, expense_id: uuid.UUID) -> Expense | None:
        """Used for permission checks on already-deleted expenses."""
        result = await self._session.execute(
            select(Expense)
            .where(Expense.id == expense_id)
            .options(
                selectinload(Expense.payer),
                selectinload(Expense.logged_by),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_group(
        self, group_id: uuid.UUID, page: int, per_page: int
    ) -> tuple[list[dict], int]:
        """Return paginated expense summaries and total count.

        Returns a list of dicts to avoid N+1 queries on split counts.
        """
        # Count query
        count_result = await self._session.execute(
            select(func.count(Expense.id)).where(
                Expense.group_id == group_id,
                Expense.deleted_at.is_(None),
            )
        )
        total = int(count_result.scalar() or 0)

        # Fetch expenses with payer and logger eagerly loaded
        offset = (page - 1) * per_page
        expense_result = await self._session.execute(
            select(Expense)
            .where(Expense.group_id == group_id, Expense.deleted_at.is_(None))
            .options(
                selectinload(Expense.payer),
                selectinload(Expense.logged_by),
                selectinload(Expense.splits),
            )
            .order_by(Expense.created_at.desc())
            .limit(per_page)
            .offset(offset)
        )
        expenses = list(expense_result.scalars().all())

        summaries = [
            {
                "id": e.id,
                "description": e.description,
                "amount_cents": e.amount_cents,
                "currency": e.currency,
                "split_type": e.split_type,
                "split_count": len(e.splits),
                "payer_id": e.payer_member_id,
                "payer_name": e.payer.display_name,
                "logged_by_name": e.logged_by.display_name,
                "expense_date": e.expense_date,
                "created_at": e.created_at,
            }
            for e in expenses
        ]

        return summaries, total

    async def soft_delete(self, expense_id: uuid.UUID) -> None:
        await self._session.execute(
            update(Expense)
            .where(Expense.id == expense_id)
            .values(deleted_at=datetime.now(timezone.utc))
        )

    async def update(
        self,
        expense_id: uuid.UUID,
        splits: list[dict] | None,
        **kwargs: object,
    ) -> Expense | None:
        """Update expense fields. If splits is provided, replace all splits."""
        kwargs["updated_at"] = datetime.now(timezone.utc)

        await self._session.execute(
            update(Expense).where(Expense.id == expense_id).values(**kwargs)
        )

        if splits is not None:
            # Delete existing splits
            existing_result = await self._session.execute(
                select(ExpenseSplit).where(ExpenseSplit.expense_id == expense_id)
            )
            for es in existing_result.scalars().all():
                await self._session.delete(es)
            await self._session.flush()

            # Insert new splits
            for split_data in splits:
                split = ExpenseSplit(
                    id=uuid.uuid4(),
                    expense_id=expense_id,
                    member_id=split_data["member_id"],
                    amount_cents=split_data["amount_cents"],
                    percentage=split_data.get("percentage"),
                )
                self._session.add(split)

        await self._session.flush()
        return await self.get_by_id(expense_id)
