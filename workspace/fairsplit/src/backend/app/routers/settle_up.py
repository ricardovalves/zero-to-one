"""Settle-up computation endpoint — the hero feature.

GET /api/v1/groups/{id}/settle-up

Runs the greedy max-heap minimum-transfer algorithm on the current net
balances. Returns an ordered list of transfers that, if completed, bring
all members' balances to zero. Always computed at read time from live data.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

import app.schemas as schemas
from app.config import get_settings
from app.database import get_db
from app.middleware.auth_middleware import MemberContext, get_current_member
from app.repositories.group_repo import GroupRepository
from app.services.balance_service import compute_net_balances
from app.services.settle_service import compute_settle_up

router = APIRouter(prefix="/api/v1", tags=["settle-up"])
logger = logging.getLogger(__name__)
settings = get_settings()


@router.get("/groups/{group_id}/settle-up")
async def get_settle_up(
    group_id: uuid.UUID,
    request: Request,
    currency: str | None = None,
    session: AsyncSession = Depends(get_db),
) -> schemas.SettleUpResponse:
    """Compute the minimum-transfer settle-up plan.

    The greedy max-heap algorithm runs in O(n log n) and is computed fresh on
    every request. For groups up to 20 members it produces the exact minimum
    number of transfers. For larger groups it produces a near-optimal result.

    If all balances are zero, returns an empty transfers list with all_settled=True.

    The response includes a pre-formatted clipboard_text ready to paste into
    a group chat.
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

    effective_currency = currency or group.default_currency

    # Compute net balances (the CTE query)
    balance_rows = await compute_net_balances(session, group_id)

    # Build the inputs for the settle-up algorithm
    net_balances: dict[uuid.UUID, int] = {
        row.member_id: row.net_cents for row in balance_rows
    }
    member_names: dict[uuid.UUID, str] = {
        row.member_id: row.display_name for row in balance_rows
    }

    # Run the algorithm
    transfers = compute_settle_up(net_balances, member_names, effective_currency)

    all_settled = len(transfers) == 0

    # Build schema objects
    transfer_schemas = [
        schemas.Transfer(
            debtor_id=t.debtor_id,
            debtor_name=t.debtor_name,
            creditor_id=t.creditor_id,
            creditor_name=t.creditor_name,
            amount_cents=t.amount_cents,
            amount_display=schemas.format_cents(t.amount_cents, t.currency),
            currency=t.currency,
        )
        for t in transfers
    ]

    # Build clipboard text
    group_url = f"{settings.APP_BASE_URL}/groups/{group_id}"
    if all_settled:
        clipboard_text = (
            f"FairSplit — {group.name}\n"
            "Everyone is settled up. Nothing to pay."
        )
    else:
        lines = [f"FairSplit — {group.name} Settle-Up"]
        for t in transfer_schemas:
            lines.append(f"• {t.debtor_name} pays {t.creditor_name} {t.amount_display}")
        lines.append(f"Powered by FairSplit: {group_url}")
        clipboard_text = "\n".join(lines)

    computed_at = datetime.now(timezone.utc)

    logger.info(
        "settle_up_computed",
        extra={
            "group_id": str(group_id),
            "member_id": str(current_member.member_id),
            "transfer_count": len(transfers),
            "all_settled": all_settled,
        },
    )

    return schemas.SettleUpResponse(
        group_name=group.name,
        currency=effective_currency,
        all_settled=all_settled,
        transfer_count=len(transfers),
        transfers=transfer_schemas,
        clipboard_text=clipboard_text,
        computed_at=computed_at,
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
