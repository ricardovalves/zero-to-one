"""Health check endpoint — not authenticated, not rate-limited."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def get_health() -> JSONResponse:
    """Return 200 if API and database are operational, 503 otherwise.

    Used by Fly.io health checks and the CD pipeline smoke test.
    Not authenticated. Not rate-limited.
    """
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return JSONResponse(
            status_code=200,
            content={"status": "healthy", "db": "connected", "timestamp": timestamp},
        )
    except Exception:
        logger.error("health_check_db_unreachable", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "db": "unreachable", "timestamp": timestamp},
        )
