"""SQLAlchemy model for the expense_splits table."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExpenseSplit(Base):
    __tablename__ = "expense_splits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("expenses.id", ondelete="CASCADE"),
        nullable=False,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    # Stored for display purposes only; amount_cents is authoritative.
    # NUMERIC(6,3) stores values like 33.333 or 100.000.
    # Nullable: only populated when split_type='custom_percentage'.
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(6, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint("amount_cents >= 0", name="ck_expense_splits_amount_nonneg"),
        UniqueConstraint("expense_id", "member_id", name="uq_expense_splits_expense_member"),
        # Join path index: expenses → expense_splits.
        # Used in every expense detail view and in the balance CTE inner join:
        #   JOIN expense_splits es ON es.expense_id = e.id
        # Without this index, the join is a full scan of expense_splits.
        Index("idx_expense_splits_expense_id", "expense_id"),
        # Aggregation path index: balance CTE groups splits by member_id.
        #   SELECT member_id, SUM(amount_cents) FROM expense_splits ... GROUP BY member_id
        # This index allows the planner to use an Index Scan + aggregate instead
        # of a full sequential scan followed by sort.
        Index("idx_expense_splits_member_id", "member_id"),
    )

    # Relationships
    expense: Mapped["Expense"] = relationship(  # type: ignore[name-defined]
        "Expense",
        back_populates="splits",
        lazy="noload",
    )
    member: Mapped["Member"] = relationship(  # type: ignore[name-defined]
        "Member",
        back_populates="expense_splits",
        lazy="noload",
    )
