"""Developer-only endpoints — disabled in production.

GET  /api/v1/dev/seed-info           — return seeded groups + members for the dev panel
POST /api/v1/dev/login/{member_id}   — issue a session token for an existing member
GET  /api/v1/groups/preview/{token}  — public group preview before joining (join page)

All /api/v1/dev/* endpoints return 404 when ENVIRONMENT=production.
The preview endpoint is always public (no auth, used on the join page).
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.middleware.auth_middleware import create_member_token, set_session_cookie
from app.models.group import Group
from app.models.member import Member
from app.repositories.group_repo import GroupRepository
from app.repositories.member_repo import MemberRepository

router = APIRouter(prefix="/api/v1", tags=["dev"])
logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Response shapes
# ---------------------------------------------------------------------------


class MemberPreview(BaseModel):
    id: uuid.UUID
    display_name: str
    is_admin: bool


class GroupPreview(BaseModel):
    id: uuid.UUID
    name: str
    invite_token: uuid.UUID
    status: str
    default_currency: str
    member_count: int
    expense_count: int
    members: list[MemberPreview]


class DevSeedGroup(BaseModel):
    id: uuid.UUID
    name: str
    invite_token: uuid.UUID
    status: str
    members: list[MemberPreview]


class DevLoginResponse(BaseModel):
    group_id: uuid.UUID
    member: MemberPreview
    token: str


# ---------------------------------------------------------------------------
# Public: group preview (used by the join page, always available)
# ---------------------------------------------------------------------------


@router.get("/groups/preview/{invite_token}")
async def group_preview(
    invite_token: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> GroupPreview:
    """Return a lightweight group preview for an invite token.

    Public endpoint — no session required. Used by the join page to show the
    group name, member count, and a short member list before the user enters
    their display name.
    """
    group_repo = GroupRepository(session)
    member_repo = MemberRepository(session)

    group = await group_repo.get_by_invite_token(invite_token)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "INVALID_INVITE_TOKEN",
                    "message": "This invite link is invalid or has expired.",
                }
            },
        )

    members = await member_repo.list_by_group(group.id)
    member_count = await group_repo.get_member_count(group.id)
    expense_count = await group_repo.get_expense_count(group.id)

    return GroupPreview(
        id=group.id,
        name=group.name,
        invite_token=group.invite_token,
        status=group.status,
        default_currency=group.default_currency,
        member_count=member_count,
        expense_count=expense_count,
        # Show up to 5 members in the preview
        members=[
            MemberPreview(
                id=m.id,
                display_name=m.display_name,
                is_admin=m.is_admin,
            )
            for m in members[:5]
        ],
    )


# ---------------------------------------------------------------------------
# Dev-only: seed info + login-as-member
# ---------------------------------------------------------------------------


def _require_dev() -> None:
    """Raise 404 in production so dev endpoints are invisible."""
    if settings.is_production:
        raise HTTPException(status_code=404, detail="Not Found")


@router.get("/dev/seed-info")
async def dev_seed_info(
    session: AsyncSession = Depends(get_db),
) -> list[DevSeedGroup]:
    """Return all seeded groups with their members.

    Used by the dev panel on the home page to render clickable login links.
    Disabled in production.
    """
    _require_dev()

    result = await session.execute(
        select(Group).order_by(Group.created_at.asc())
    )
    groups = list(result.scalars().all())

    member_repo = MemberRepository(session)
    output: list[DevSeedGroup] = []

    for group in groups:
        members = await member_repo.list_by_group(group.id)
        output.append(
            DevSeedGroup(
                id=group.id,
                name=group.name,
                invite_token=group.invite_token,
                status=group.status,
                members=[
                    MemberPreview(
                        id=m.id,
                        display_name=m.display_name,
                        is_admin=m.is_admin,
                    )
                    for m in members
                ],
            )
        )

    return output


@router.post("/dev/login/{member_id}")
async def dev_login_as_member(
    member_id: uuid.UUID,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> DevLoginResponse:
    """Issue a session token for an existing member.

    Allows the dev panel to log in as any seeded member without going through
    the join flow. Sets the httpOnly session cookie and returns the JWT.
    Disabled in production.
    """
    _require_dev()

    member_repo = MemberRepository(session)
    member = await member_repo.get_by_id(member_id)

    if member is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "MEMBER_NOT_FOUND", "message": "Member not found."}},
        )

    token = create_member_token(
        member_id=member.id,
        group_id=member.group_id,
        is_admin=member.is_admin,
    )

    set_session_cookie(response, token)

    logger.info(
        "dev_login",
        extra={"member_id": str(member.id), "group_id": str(member.group_id)},
    )

    return DevLoginResponse(
        group_id=member.group_id,
        member=MemberPreview(
            id=member.id,
            display_name=member.display_name,
            is_admin=member.is_admin,
        ),
        token=token,
    )
