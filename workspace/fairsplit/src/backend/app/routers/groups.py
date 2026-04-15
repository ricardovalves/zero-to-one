"""Group management endpoints.

POST /api/v1/groups       — create group + auto-join creator as admin
GET  /api/v1/groups/{id}  — get group details (authenticated)
PATCH /api/v1/groups/{id} — update group (admin only)
POST /api/v1/groups/{id}/invite — regenerate invite token (admin only)

Note on public vs authenticated:
- POST /groups is public (no existing session required — this creates the session)
- All other endpoints require a valid member session token for the group
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

import app.schemas as schemas
from app.database import get_db
from app.middleware.auth_middleware import (
    MemberContext,
    create_member_token,
    get_current_member,
    set_session_cookie,
)
from app.repositories.group_repo import GroupRepository
from app.repositories.member_repo import MemberRepository
from app.services.idempotency_service import check_idempotency, store_idempotency

router = APIRouter(prefix="/api/v1", tags=["groups"])
logger = logging.getLogger(__name__)


@router.post("/groups", status_code=201)
async def create_group(
    request: Request,
    body: schemas.CreateGroupRequest,
    response: Response,
    x_idempotency_key: Optional[str] = Header(default=None, alias="X-Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
) -> schemas.CreateGroupResponse:
    """Create a new expense group.

    The creator is automatically added as the admin member. A signed JWT is
    returned in the response body AND set as an httpOnly cookie.

    Idempotent: provide X-Idempotency-Key to prevent double-submission.
    """
    request_id = str(uuid.uuid4())[:8]

    # Parse idempotency key
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
        # Check idempotency before doing any work
        cached = await check_idempotency(session, idem_key)
        if cached is not None:
            # Re-issue the cookie with the original token
            token = cached.get("token", "")
            set_session_cookie(response, token)
            return schemas.CreateGroupResponse(**cached)

        group_repo = GroupRepository(session)
        member_repo = MemberRepository(session)

        group = await group_repo.create(
            name=body.name,
            description=body.description,
            default_currency=body.default_currency,
        )
        member = await member_repo.create(
            group_id=group.id,
            display_name=body.admin_display_name,
            is_admin=True,
        )

        token = create_member_token(
            member_id=member.id,
            group_id=group.id,
            is_admin=True,
        )

        member_count = await group_repo.get_member_count(group.id)
        expense_count = 0

        result = schemas.CreateGroupResponse(
            group=schemas.Group(
                id=group.id,
                name=group.name,
                description=group.description,
                invite_token=group.invite_token,
                status=group.status,
                default_currency=group.default_currency,
                member_count=member_count,
                expense_count=expense_count,
                created_at=group.created_at,
                updated_at=group.updated_at,
            ),
            member=schemas.Member(
                id=member.id,
                display_name=member.display_name,
                is_admin=member.is_admin,
                joined_at=member.joined_at,
            ),
            token=token,
        )

        response_dict = result.model_dump(mode="json")

        await store_idempotency(
            session=session,
            idempotency_key=idem_key,
            endpoint="POST /api/v1/groups",
            response_body=response_dict,
            status_code=201,
        )

    set_session_cookie(response, token)

    logger.info(
        "group_created",
        extra={
            "group_id": str(group.id),
            "member_id": str(member.id),
            "request_id": request_id,
        },
    )

    return result


@router.get("/groups/{group_id}")
async def get_group(
    group_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.Group:
    """Get group details. Requires a valid member session for this group."""
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    group_repo = GroupRepository(session)
    group = await group_repo.get_by_id(group_id)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    member_count = await group_repo.get_member_count(group_id)
    expense_count = await group_repo.get_expense_count(group_id)

    return schemas.Group(
        id=group.id,
        name=group.name,
        description=group.description,
        invite_token=group.invite_token,
        status=group.status,
        default_currency=group.default_currency,
        member_count=member_count,
        expense_count=expense_count,
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


@router.patch("/groups/{group_id}")
async def update_group(
    group_id: uuid.UUID,
    body: schemas.UpdateGroupRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.Group:
    """Update group name, description, or status. Admin only."""
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    if not current_member.is_admin:
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "PERMISSION_DENIED", "message": "Only group admins can edit group settings.", "request_id": _req_id()}},
        )

    group_repo = GroupRepository(session)
    group = await group_repo.get_by_id(group_id)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    updates: dict = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.description is not None:
        updates["description"] = body.description

    if body.status == "archived" and not body.force:
        # Check for outstanding balances before archiving
        from app.services.balance_service import compute_net_balances
        balance_rows = await compute_net_balances(session, group_id)
        has_outstanding = any(row.net_cents != 0 for row in balance_rows)
        if has_outstanding:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": {
                        "code": "GROUP_HAS_OUTSTANDING_BALANCES",
                        "message": "Some members still have outstanding balances. Pass force=true to archive anyway.",
                        "request_id": _req_id(),
                    }
                },
            )

    if body.status is not None:
        updates["status"] = body.status

    if not updates:
        # Nothing to update — return current state
        member_count = await group_repo.get_member_count(group_id)
        expense_count = await group_repo.get_expense_count(group_id)
        return schemas.Group(
            id=group.id,
            name=group.name,
            description=group.description,
            invite_token=group.invite_token,
            status=group.status,
            default_currency=group.default_currency,
            member_count=member_count,
            expense_count=expense_count,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )

    async with session.begin():
        updated = await group_repo.update(group_id, **updates)

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    member_count = await group_repo.get_member_count(group_id)
    expense_count = await group_repo.get_expense_count(group_id)

    logger.info(
        "group_updated",
        extra={"group_id": str(group_id), "member_id": str(current_member.member_id)},
    )

    return schemas.Group(
        id=updated.id,
        name=updated.name,
        description=updated.description,
        invite_token=updated.invite_token,
        status=updated.status,
        default_currency=updated.default_currency,
        member_count=member_count,
        expense_count=expense_count,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.post("/groups/{group_id}/invite")
async def regenerate_invite_token(
    group_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.InviteTokenResponse:
    """Regenerate the group invite token. Admin only."""
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    if not current_member.is_admin:
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "PERMISSION_DENIED", "message": "Only group admins can regenerate the invite link.", "request_id": _req_id()}},
        )

    group_repo = GroupRepository(session)
    group = await group_repo.get_by_id(group_id)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    async with session.begin():
        new_token = await group_repo.regenerate_invite_token(group_id)

    logger.info(
        "invite_token_regenerated",
        extra={"group_id": str(group_id), "member_id": str(current_member.member_id)},
    )

    return schemas.InviteTokenResponse(invite_token=new_token)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _verify_group_access(current_member: MemberContext, group_id: uuid.UUID) -> None:
    """Raise 403 if the session token is for a different group."""
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
