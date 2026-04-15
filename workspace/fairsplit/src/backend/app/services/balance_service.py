"""Net balance computation service.

Runs the CTE query from technical-spec.md §3 Query 1. This is the most
performance-critical query in the application — called on every balance
view and every settle-up computation.

The query is purposely expressed as raw SQL via SQLAlchemy text() to match
the exact form analysed in the technical spec (with the defined indexes).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class MemberBalanceRow:
    """Raw balance data for a single member, as returned by the CTE query."""

    member_id: uuid.UUID
    display_name: str
    paid_total_cents: int
    owed_total_cents: int
    settled_out_cents: int
    settled_in_cents: int
    net_cents: int


async def compute_net_balances(
    session: AsyncSession,
    group_id: uuid.UUID,
) -> list[MemberBalanceRow]:
    """Compute net balances for all members in a group.

    Uses the CTE from technical-spec.md §3 Query 1. All partial amounts
    come back as Python ints (we CAST in the query to avoid Decimal issues
    from PostgreSQL SUM on INTEGER columns).

    Returns rows ordered by net_cents DESC (largest creditor first).
    """
    sql = text("""
        WITH paid AS (
            SELECT payer_member_id AS member_id,
                   SUM(amount_cents)::bigint AS paid_total
            FROM expenses
            WHERE group_id = :group_id
              AND deleted_at IS NULL
            GROUP BY payer_member_id
        ),
        owed AS (
            SELECT es.member_id,
                   SUM(es.amount_cents)::bigint AS owed_total
            FROM expense_splits es
            JOIN expenses e ON e.id = es.expense_id
            WHERE e.group_id = :group_id
              AND e.deleted_at IS NULL
            GROUP BY es.member_id
        ),
        settled_paid AS (
            SELECT payer_member_id AS member_id,
                   SUM(amount_cents)::bigint AS settled_out
            FROM settlements
            WHERE group_id = :group_id
              AND deleted_at IS NULL
            GROUP BY payer_member_id
        ),
        settled_received AS (
            SELECT payee_member_id AS member_id,
                   SUM(amount_cents)::bigint AS settled_in
            FROM settlements
            WHERE group_id = :group_id
              AND deleted_at IS NULL
            GROUP BY payee_member_id
        )
        SELECT
            m.id                                      AS member_id,
            m.display_name,
            COALESCE(p.paid_total, 0)::bigint         AS paid_total_cents,
            COALESCE(o.owed_total, 0)::bigint         AS owed_total_cents,
            COALESCE(sp.settled_out, 0)::bigint       AS settled_out_cents,
            COALESCE(sr.settled_in, 0)::bigint        AS settled_in_cents,
            (
              COALESCE(p.paid_total, 0)
              - COALESCE(o.owed_total, 0)
              + COALESCE(sp.settled_out, 0)
              - COALESCE(sr.settled_in, 0)
            )::bigint AS net_cents
        FROM members m
        LEFT JOIN paid            p  ON p.member_id  = m.id
        LEFT JOIN owed            o  ON o.member_id  = m.id
        LEFT JOIN settled_paid   sp  ON sp.member_id = m.id
        LEFT JOIN settled_received sr ON sr.member_id = m.id
        WHERE m.group_id = :group_id
        ORDER BY net_cents DESC
    """)

    result = await session.execute(sql, {"group_id": str(group_id)})
    rows = result.mappings().all()

    return [
        MemberBalanceRow(
            member_id=uuid.UUID(str(row["member_id"])),
            display_name=row["display_name"],
            paid_total_cents=int(row["paid_total_cents"]),
            owed_total_cents=int(row["owed_total_cents"]),
            settled_out_cents=int(row["settled_out_cents"]),
            settled_in_cents=int(row["settled_in_cents"]),
            net_cents=int(row["net_cents"]),
        )
        for row in rows
    ]


async def get_member_expense_count_paid(
    session: AsyncSession,
    group_id: uuid.UUID,
    member_id: uuid.UUID,
) -> int:
    """Count expenses where a specific member was the payer."""
    from sqlalchemy import func, select

    from app.models.expense import Expense

    result = await session.execute(
        select(func.count(Expense.id)).where(
            Expense.group_id == group_id,
            Expense.payer_member_id == member_id,
            Expense.deleted_at.is_(None),
        )
    )
    return int(result.scalar() or 0)
