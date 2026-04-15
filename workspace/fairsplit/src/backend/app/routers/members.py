"""Member management endpoints.

POST /api/v1/join/{invite_token}        — join a group by invite link (public)
GET  /api/v1/groups/{id}/members        — list all members (authenticated)
GET  /api/v1/groups/{id}/members/me     — get current member profile (authenticated)
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

router = APIRouter(prefix="/api/v1", tags=["members"])
logger = logging.getLogger(__name__)


@router.post("/join/{invite_token}", status_code=201)
async def join_group(
    invite_token: uuid.UUID,
    body: schemas.JoinGroupRequest,
    request: Request,
    response: Response,
    x_idempotency_key: Optional[str] = Header(default=None, alias="X-Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
) -> schemas.JoinGroupResponse:
    """Join a group via invite link.

    No existing session required. Returns {group, member, token} and sets
    an httpOnly session cookie.

    Duplicate display names are resolved by appending (2), (3), etc.
    """
    request_id = str(uuid.uuid4())[:8]

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
            token = cached.get("token", "")
            set_session_cookie(response, token)
            return schemas.JoinGroupResponse(**cached)

        group_repo = GroupRepository(session)
        member_repo = MemberRepository(session)

        group = await group_repo.get_by_invite_token(invite_token)
        if group is None:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "INVALID_INVITE_TOKEN",
                        "message": "This link is no longer valid. Ask the group admin for a new one.",
                        "request_id": request_id,
                    }
                },
            )

        if group.status == "archived":
            raise HTTPException(
                status_code=409,
                detail={
                    "error": {
                        "code": "GROUP_ARCHIVED",
                        "message": "This group has been closed. You can view it in read-only mode.",
                        "request_id": request_id,
                    }
                },
            )

        # Resolve unique display name (append suffix if duplicate)
        display_name = await member_repo.resolve_unique_display_name(
            group.id, body.display_name
        )

        member = await member_repo.create(
            group_id=group.id,
            display_name=display_name,
            is_admin=False,
        )

        token = create_member_token(
            member_id=member.id,
            group_id=group.id,
            is_admin=False,
        )

        member_count = await group_repo.get_member_count(group.id)

        result = schemas.JoinGroupResponse(
            group=schemas.JoinGroupGroupSummary(
                id=group.id,
                name=group.name,
                status=group.status,
                default_currency=group.default_currency,
                member_count=member_count,
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
            endpoint=f"POST /api/v1/join/{invite_token}",
            response_body=response_dict,
            status_code=201,
        )

    set_session_cookie(response, token)

    logger.info(
        "member_joined",
        extra={
            "group_id": str(group.id),
            "member_id": str(member.id),
            "request_id": request_id,
        },
    )

    return result


@router.get("/groups/{group_id}/members")
async def list_members(
    group_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """List all members in a group, sorted alphabetically by display name."""
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    group_repo = GroupRepository(session)
    group = await group_repo.get_by_id(group_id)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    member_repo = MemberRepository(session)
    members = await member_repo.list_by_group(group_id)

    member_list = [
        schemas.Member(
            id=m.id,
            display_name=m.display_name,
            is_admin=m.is_admin,
            joined_at=m.joined_at,
        )
        for m in members
    ]

    return {
        "data": [m.model_dump(mode="json") for m in member_list],
        "total": len(member_list),
        "page": 1,
        "per_page": 100,
    }


@router.get("/groups/{group_id}/members/me")
async def get_current_member_profile(
    group_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.Member:
    """Return the authenticated member's profile.

    Used on page load to confirm session validity and recover member context
    if localStorage was cleared. Never redirects to join — always attempts
    cookie-based auth first.
    """
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    member_repo = MemberRepository(session)
    member = await member_repo.get_by_id(current_member.member_id)
    if member is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "MEMBER_NOT_FOUND", "message": "Member not found.", "request_id": _req_id()}},
        )

    return schemas.Member(
        id=member.id,
        display_name=member.display_name,
        is_admin=member.is_admin,
        joined_at=member.joined_at,
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
