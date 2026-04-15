"""Anonymous member session model.

Session token lifecycle:
1. Member creates a group (POST /api/v1/groups) or joins via invite link
   (POST /api/v1/join/{invite_token}).
2. Server creates a Member record and issues a signed JWT (PyJWT, HS256).
3. JWT payload: {sub: member_id, group_id: group_id, is_admin: bool, iat, exp}
4. JWT is set as an httpOnly, SameSite=Lax cookie AND returned in the
   response body (so the frontend can store it in localStorage as a cache).
5. On subsequent requests the server reads the cookie (primary).
   If no cookie, falls back to Authorization: Bearer <token> header.
6. Cookie expiry: 30 days, rolling (reset on each valid request).

Safari ITP note: server-set httpOnly cookies are NOT subject to ITP's
7-day localStorage clearing rule. They are only cleared on explicit user action.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException, Request

from app.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"
COOKIE_NAME = "fairsplit_member_token"


@dataclass
class MemberContext:
    """Decoded session context injected into every authenticated request."""

    member_id: UUID
    group_id: UUID
    is_admin: bool


def create_member_token(member_id: UUID, group_id: UUID, is_admin: bool) -> str:
    """Issue a signed JWT for the given member.

    The token is valid for JWT_EXPIRY_DAYS days from now. It is stateless —
    no database lookup is required to validate it.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(member_id),
        "group_id": str(group_id),
        "is_admin": is_admin,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(days=settings.JWT_EXPIRY_DAYS)).timestamp()),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_member_token(token: str) -> MemberContext:
    """Verify and decode a member JWT.

    Raises HTTPException 401 on any failure — expired, invalid signature,
    malformed, or missing required claims.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="SESSION_EXPIRED")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="SESSION_INVALID")

    try:
        return MemberContext(
            member_id=UUID(payload["sub"]),
            group_id=UUID(payload["group_id"]),
            is_admin=bool(payload.get("is_admin", False)),
        )
    except (KeyError, ValueError):
        raise HTTPException(status_code=401, detail="SESSION_INVALID")


def get_current_member(request: Request) -> MemberContext:
    """Extract and validate the member token from the request.

    Resolution order:
    1. httpOnly cookie named 'fairsplit_member_token' (primary — set by server).
    2. Authorization: Bearer <token> header (fallback for API clients and
       cross-origin test scenarios).

    Raises HTTPException 401 if no token is present or the token is invalid.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

    if not token:
        raise HTTPException(status_code=401, detail="NO_SESSION")

    return decode_member_token(token)


def set_session_cookie(response, token: str) -> None:
    """Set the httpOnly session cookie on the response.

    The `secure` flag is set only in production. In development (Docker on
    HTTP) setting secure=True would silently block the cookie, making every
    authenticated request fail with 401.
    """
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.is_production,
        max_age=settings.JWT_EXPIRY_DAYS * 86400,
        path="/",
    )
