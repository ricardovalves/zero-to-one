"""Settlement management endpoints.

GET    /api/v1/groups/{id}/settlements              — list settlements
POST   /api/v1/groups/{id}/settlements              — record a settlement
DELETE /api/v1/groups/{id}/settlements/{settlement_id} — soft-delete (reverse)
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

import app.schemas as schemas
from app.database import get_db
from app.middleware.auth_middleware import MemberContext, get_current_member
from app.repositories.group_repo import GroupRepository
from app.repositories.member_repo import MemberRepository
from app.repositories.settlement_repo import SettlementRepository
from app.services.idempotency_service import check_idempotency, store_idempotency

router = APIRouter(prefix="/api/v1", tags=["settlements"])
logger = logging.getLogger(__name__)


@router.get("/groups/{group_id}/settlements")
async def list_settlements(
    group_id: uuid.UUID,
    request: Request,
    page: int = 1,
    per_page: int = 20,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """List active settlement records, newest first, paginated."""
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    if page < 1 or per_page < 1 or per_page > 100:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "VALIDATION_ERROR", "message": "Invalid pagination parameters.", "request_id": _req_id()}},
        )

    group_repo = GroupRepository(session)
    group = await group_repo.get_by_id(group_id)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    repo = SettlementRepository(session)
    settlements, total = await repo.list_by_group(group_id, page, per_page)

    data = [_settlement_to_schema(s, group.default_currency).model_dump(mode="json") for s in settlements]

    return {"data": data, "total": total, "page": page, "per_page": per_page}


@router.post("/groups/{group_id}/settlements", status_code=201)
async def create_settlement(
    group_id: uuid.UUID,
    body: schemas.CreateSettlementRequest,
    request: Request,
    x_idempotency_key: Optional[str] = Header(default=None, alias="X-Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
) -> schemas.Settlement:
    """Record a completed transfer (mark as paid).

    The caller must be the payer (body.payer_member_id) or a group admin.
    Idempotent: provide X-Idempotency-Key to prevent double-recording.
    """
    request_id = str(uuid.uuid4())[:8]
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    idem_key: uuid.UUID | None = None
    if x_idempotency_key:
        try:
            idem_key = uuid.UUID(x_idempotency_key)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail={"error": {"code": "VALIDATION_ERROR", "message": "X-Idempotency-Key must be a valid UUID.", "request_id": request_id}},
            )

    async with session.begin():
        cached = await check_idempotency(session, idem_key)
        if cached is not None:
            return schemas.Settlement(**cached)

        group_repo = GroupRepository(session)
        group = await group_repo.get_by_id(group_id)
        if group is None:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": request_id}},
            )
        if group.status == "archived":
            raise HTTPException(
                status_code=409,
                detail={"error": {"code": "GROUP_ARCHIVED", "message": "Cannot add settlements to an archived group.", "request_id": request_id}},
            )

        # Validate payer and payee are in this group
        member_repo = MemberRepository(session)
        payer = await member_repo.get_by_id(body.payer_member_id)
        if payer is None or payer.group_id != group_id:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "MEMBER_NOT_FOUND", "message": "Payer member not found in this group.", "request_id": request_id}},
            )
        payee = await member_repo.get_by_id(body.payee_member_id)
        if payee is None or payee.group_id != group_id:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "MEMBER_NOT_FOUND", "message": "Payee member not found in this group.", "request_id": request_id}},
            )

        # Permission: must be payer or admin
        if (
            body.payer_member_id != current_member.member_id
            and not current_member.is_admin
        ):
            raise HTTPException(
                status_code=403,
                detail={"error": {"code": "PERMISSION_DENIED", "message": "You can only record settlements where you are the payer, or you must be the group admin.", "request_id": request_id}},
            )

        repo = SettlementRepository(session)
        settlement = await repo.create(
            group_id=group_id,
            payer_member_id=body.payer_member_id,
            payee_member_id=body.payee_member_id,
            amount_cents=body.amount_cents,
            currency=body.currency,
        )

        result = _settlement_to_schema(settlement, group.default_currency)
        response_dict = result.model_dump(mode="json")

        await store_idempotency(
            session=session,
            idempotency_key=idem_key,
            endpoint=f"POST /api/v1/groups/{group_id}/settlements",
            response_body=response_dict,
            status_code=201,
        )

    logger.info(
        "settlement_created",
        extra={
            "group_id": str(group_id),
            "settlement_id": str(settlement.id),
            "member_id": str(current_member.member_id),
            "amount_cents": settlement.amount_cents,
        },
    )

    return result


@router.delete("/groups/{group_id}/settlements/{settlement_id}")
async def delete_settlement(
    group_id: uuid.UUID,
    settlement_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.DeletedResponse:
    """Soft-delete (reverse) a settlement. Caller must be the payer or admin."""
    request_id = _req_id()
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    async with session.begin():
        group_repo = GroupRepository(session)
        group = await group_repo.get_by_id(group_id)
        if group is None:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": request_id}},
            )

        repo = SettlementRepository(session)
        settlement = await repo.get_by_id_including_deleted(settlement_id)
        if settlement is None or settlement.group_id != group_id:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "SETTLEMENT_NOT_FOUND", "message": "Settlement not found.", "request_id": request_id}},
            )

        # If already deleted, return success (idempotent)
        if settlement.deleted_at is not None:
            return schemas.DeletedResponse(message="Settlement reversed. Balances have been restored.")

        # Permission: payer or admin
        if (
            settlement.payer_member_id != current_member.member_id
            and not current_member.is_admin
        ):
            raise HTTPException(
                status_code=403,
                detail={"error": {"code": "PERMISSION_DENIED", "message": "You can only reverse settlements where you are the payer, or you must be the group admin.", "request_id": request_id}},
            )

        await repo.soft_delete(settlement_id)

    logger.info(
        "settlement_deleted",
        extra={
            "group_id": str(group_id),
            "settlement_id": str(settlement_id),
            "member_id": str(current_member.member_id),
        },
    )

    return schemas.DeletedResponse(message="Settlement reversed. Balances have been restored.")


def _settlement_to_schema(settlement, default_currency: str) -> schemas.Settlement:
    """Convert a Settlement ORM object to a schema."""
    return schemas.Settlement(
        id=settlement.id,
        group_id=settlement.group_id,
        payer_id=settlement.payer_member_id,
        payer_name=settlement.payer.display_name,
        payee_id=settlement.payee_member_id,
        payee_name=settlement.payee.display_name,
        amount_cents=settlement.amount_cents,
        amount_display=schemas.format_cents(settlement.amount_cents, settlement.currency),
        currency=settlement.currency,
        created_at=settlement.created_at,
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
