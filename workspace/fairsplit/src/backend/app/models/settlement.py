"""SQLAlchemy model for the settlements table."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Settlement(Base):
    __tablename__ = "settlements"

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
    payee_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
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
        CheckConstraint("amount_cents > 0", name="ck_settlements_amount_positive"),
        CheckConstraint(
            "payer_member_id != payee_member_id",
            name="ck_settlements_different_members",
        ),
        # Partial index: balance CTE queries active settlements by group.
        # Query pattern:
        #   SELECT payer_member_id, payee_member_id, SUM(amount_cents)
        #   FROM settlements
        #   WHERE group_id = $1 AND deleted_at IS NULL
        #   GROUP BY payer_member_id, payee_member_id
        # The WHERE deleted_at IS NULL clause keeps the index compact:
        # reversed settlements are excluded, reducing index size and write cost.
        Index(
            "idx_settlements_group_id_active",
            "group_id",
            postgresql_where="deleted_at IS NULL",
        ),
    )

    # Relationships
    group: Mapped["Group"] = relationship(  # type: ignore[name-defined]
        "Group",
        back_populates="settlements",
        lazy="noload",
    )
    payer: Mapped["Member"] = relationship(  # type: ignore[name-defined]
        "Member",
        foreign_keys=[payer_member_id],
        back_populates="settlements_paid",
        lazy="noload",
    )
    payee: Mapped["Member"] = relationship(  # type: ignore[name-defined]
        "Member",
        foreign_keys=[payee_member_id],
        back_populates="settlements_received",
        lazy="noload",
    )
