"""SQLAlchemy model for the members table."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Member(Base):
    __tablename__ = "members"

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
    display_name: Mapped[str] = mapped_column(String(40), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    joined_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
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
            "length(trim(display_name)) > 0",
            name="ck_members_display_name_nonempty",
        ),
        # Non-unique index on group_id.
        # Every group dashboard load queries: SELECT * FROM members WHERE group_id = $1
        # and the balance CTE also filters by group via members.group_id.
        # Without this index, every member list is a full table scan.
        Index("idx_members_group_id", "group_id"),
    )

    # Relationships
    group: Mapped["Group"] = relationship(  # type: ignore[name-defined]
        "Group",
        back_populates="members",
        lazy="noload",
    )
    expenses_paid: Mapped[list["Expense"]] = relationship(  # type: ignore[name-defined]
        "Expense",
        foreign_keys="Expense.payer_member_id",
        back_populates="payer",
        lazy="noload",
    )
    expenses_logged: Mapped[list["Expense"]] = relationship(  # type: ignore[name-defined]
        "Expense",
        foreign_keys="Expense.logged_by_member_id",
        back_populates="logged_by",
        lazy="noload",
    )
    expense_splits: Mapped[list["ExpenseSplit"]] = relationship(  # type: ignore[name-defined]
        "ExpenseSplit",
        back_populates="member",
        lazy="noload",
    )
    settlements_paid: Mapped[list["Settlement"]] = relationship(  # type: ignore[name-defined]
        "Settlement",
        foreign_keys="Settlement.payer_member_id",
        back_populates="payer",
        lazy="noload",
    )
    settlements_received: Mapped[list["Settlement"]] = relationship(  # type: ignore[name-defined]
        "Settlement",
        foreign_keys="Settlement.payee_member_id",
        back_populates="payee",
        lazy="noload",
    )
