"""SQLAlchemy model for the groups table."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    invite_token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        default=uuid.uuid4,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
    )
    default_currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="USD",
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
        CheckConstraint("length(trim(name)) > 0", name="ck_groups_name_nonempty"),
        CheckConstraint("status IN ('active', 'archived')", name="ck_groups_status"),
        # Unique index on invite_token — used on every join flow.
        # Every group join (POST /join/{invite_token}) does a lookup by this column.
        # Without this index, every join is a full table scan.
        Index("idx_groups_invite_token", "invite_token", unique=True),
    )

    # Relationships
    members: Mapped[list["Member"]] = relationship(  # type: ignore[name-defined]
        "Member",
        back_populates="group",
        lazy="noload",
    )
    expenses: Mapped[list["Expense"]] = relationship(  # type: ignore[name-defined]
        "Expense",
        back_populates="group",
        lazy="noload",
    )
    settlements: Mapped[list["Settlement"]] = relationship(  # type: ignore[name-defined]
        "Settlement",
        back_populates="group",
        lazy="noload",
    )
