"""SQLAlchemy model for the expenses table."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    payer_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    logged_by_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    split_type: Mapped[str] = mapped_column(String(20), nullable=False)
    expense_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        server_default=func.current_date(),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "length(trim(description)) > 0",
            name="ck_expenses_description_nonempty",
        ),
        CheckConstraint("amount_cents > 0", name="ck_expenses_amount_positive"),
        CheckConstraint(
            "split_type IN ('equal', 'custom_amount', 'custom_percentage')",
            name="ck_expenses_split_type",
        ),
        # Composite partial index: the primary read path for the expense list.
        # Query pattern: WHERE group_id = $1 AND deleted_at IS NULL ORDER BY created_at DESC
        # Column order — group_id (equality) first, created_at DESC (sort) second.
        # The partial WHERE clause keeps the index small: only active (non-deleted)
        # expenses are indexed, reducing both index size and write amplification.
        Index(
            "idx_expenses_group_id_active",
            "group_id",
            "created_at",
            postgresql_where="deleted_at IS NULL",
        ),
        # Separate partial index for the balance CTE aggregation.
        # The balance query does: WHERE group_id = $1 AND deleted_at IS NULL
        # without an ORDER BY, so this simpler index avoids the overhead of
        # storing created_at in the index structure for aggregation-only queries.
        Index(
            "idx_expenses_group_id_not_deleted",
            "group_id",
            postgresql_where="deleted_at IS NULL",
        ),
        # Permission check index.
        # Used in: PATCH /expenses/{id} and DELETE /expenses/{id}
        # to verify: SELECT * FROM expenses WHERE logged_by_member_id = $1 AND id = $2
        Index("idx_expenses_logged_by", "logged_by_member_id"),
    )

    # Relationships
    group: Mapped["Group"] = relationship(  # type: ignore[name-defined]
        "Group",
        back_populates="expenses",
        lazy="noload",
    )
    payer: Mapped["Member"] = relationship(  # type: ignore[name-defined]
        "Member",
        foreign_keys=[payer_member_id],
        back_populates="expenses_paid",
        lazy="noload",
    )
    logged_by: Mapped["Member"] = relationship(  # type: ignore[name-defined]
        "Member",
        foreign_keys=[logged_by_member_id],
        back_populates="expenses_logged",
        lazy="noload",
    )
    splits: Mapped[list["ExpenseSplit"]] = relationship(  # type: ignore[name-defined]
        "ExpenseSplit",
        back_populates="expense",
        cascade="all, delete-orphan",
        lazy="noload",
    )
