"""Balance computation endpoints.

GET /api/v1/groups/{id}/balances           — net balances for all members
GET /api/v1/groups/{id}/balances/{member_id} — detailed balance for one member

The balances endpoint is polled every 10 seconds by the frontend. It must
complete in < 200ms at p95 for groups with up to 200 expenses and 50 members.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

import app.schemas as schemas
from app.database import get_db
from app.middleware.auth_middleware import MemberContext, get_current_member
from app.repositories.group_repo import GroupRepository
from app.services.balance_service import (
    compute_net_balances,
    get_member_expense_count_paid,
)

router = APIRouter(prefix="/api/v1", tags=["balances"])
logger = logging.getLogger(__name__)


@router.get("/groups/{group_id}/balances")
async def get_balances(
    group_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.BalancesResponse:
    """Compute and return net balances for all group members.

    Polled every 10 seconds by the frontend. Computed fresh on every request
    from the current state of expenses and settlements — never cached.
    """
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    group_repo = GroupRepository(session)
    group = await group_repo.get_by_id(group_id)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    rows = await compute_net_balances(session, group_id)

    members = []
    for row in rows:
        if row.net_cents > 0:
            status = "creditor"
        elif row.net_cents < 0:
            status = "debtor"
        else:
            status = "settled"

        members.append(
            schemas.MemberBalance(
                member_id=row.member_id,
                display_name=row.display_name,
                net_cents=row.net_cents,
                net_display=schemas.format_net_cents(row.net_cents, group.default_currency),
                paid_total_cents=row.paid_total_cents,
                owed_total_cents=row.owed_total_cents,
                settled_out_cents=row.settled_out_cents,
                settled_in_cents=row.settled_in_cents,
                status=status,
            )
        )

    return schemas.BalancesResponse(
        currency=group.default_currency,
        members=members,
        computed_at=datetime.now(timezone.utc),
    )


@router.get("/groups/{group_id}/balances/{member_id}")
async def get_member_balance(
    group_id: uuid.UUID,
    member_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.MemberBalanceDetail:
    """Detailed balance breakdown for a single member."""
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    group_repo = GroupRepository(session)
    group = await group_repo.get_by_id(group_id)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    rows = await compute_net_balances(session, group_id)
    row = next((r for r in rows if r.member_id == member_id), None)
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "MEMBER_NOT_FOUND", "message": "Member not found in this group.", "request_id": _req_id()}},
        )

    expense_count = await get_member_expense_count_paid(session, group_id, member_id)

    if row.net_cents > 0:
        status = "creditor"
    elif row.net_cents < 0:
        status = "debtor"
    else:
        status = "settled"

    currency = group.default_currency
    paid_display = schemas.format_cents(row.paid_total_cents, currency)
    owed_display = schemas.format_cents(row.owed_total_cents, currency)
    net_display = schemas.format_net_cents(row.net_cents, currency)

    summary = (
        f"{row.display_name} paid {paid_display} across {expense_count} expense"
        f"{'s' if expense_count != 1 else ''}. "
        f"Their share was {owed_display}. "
        f"Net: {net_display}."
    )

    return schemas.MemberBalanceDetail(
        member_id=row.member_id,
        display_name=row.display_name,
        net_cents=row.net_cents,
        net_display=net_display,
        paid_total_cents=row.paid_total_cents,
        owed_total_cents=row.owed_total_cents,
        settled_out_cents=row.settled_out_cents,
        settled_in_cents=row.settled_in_cents,
        status=status,
        expense_count_paid=expense_count,
        summary=summary,
    )


def _verify_group_access(current_member: MemberContext, group_id: uuid.UUID) -> None:
    if current_member.group_id != group_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "MEMBER_WRONG_GROUP",
                    "message": "Your session token is for a different group.",
                    "request_id": _req_id(),
                }
            },
        )


def _req_id() -> str:
    return str(uuid.uuid4())[:8]
