"""SQLAlchemy model for the idempotency_keys table."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Index, SmallInteger, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    # The PK is the client-supplied UUID key itself (not a surrogate).
    # Lookup is always by this PK: SELECT ... WHERE key = $1 AND expires_at > NOW()
    key: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
    )
    # The API endpoint that generated this key, e.g. 'POST /api/v1/groups'.
    # Stored for debugging and observability only.
    endpoint: Mapped[str] = mapped_column(String(100), nullable=False)
    # Full JSON response body stored as JSONB for efficient binary storage.
    # On a duplicate request, this value is returned directly without re-processing.
    response_body: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # HTTP status code of the original response (stored as SMALLINT to match DDL).
    status_code: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
    )
    # expires_at defaults to NOW() + 24 hours. A cleanup task or startup routine
    # runs: DELETE FROM idempotency_keys WHERE expires_at < NOW()
    # Server default expressed as a text literal because SQLAlchemy's func.now()
    # cannot be combined with an interval in a cross-dialect server_default.
    expires_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=text("NOW() + INTERVAL '24 hours'"),
    )

    __table_args__ = (
        # Plain index on expires_at (no WHERE clause).
        # Used by:
        #   1. The idempotency lookup query: WHERE key = $1 AND expires_at > NOW()
        #      (the PK handles the key lookup; this index helps with expiry filter)
        #   2. The cleanup query: DELETE FROM idempotency_keys WHERE expires_at < NOW()
        # NOTE: A partial index with WHERE expires_at > NOW() is invalid in PostgreSQL
        # because NOW() is a VOLATILE function — index predicates require IMMUTABLE
        # functions. A plain index is sufficient; the planner applies the volatile
        # filter at query runtime.
        Index(
            "idx_idempotency_keys_expires",
            "expires_at",
        ),
    )
