"""FairSplit FastAPI application.

Entry point for the ASGI server. Initialises middleware, routers, and
exception handlers. All configuration is sourced from environment variables
via app.config.Settings.

Run locally:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import get_settings
from app.logging_config import configure_logging
from app.routers import balances, dev, expenses, groups, health, members, settle_up, settlements

settings = get_settings()

# Configure structured JSON logging before anything else — this ensures that
# even early startup log messages from uvicorn are captured in JSON format.
configure_logging(level=settings.LOG_LEVEL)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="FairSplit API",
    version="1.0.0",
    description=(
        "Zero-dependency shared expense tracker API. "
        "Members join via invite link with a display name only — no account, "
        "no email, no password."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,  # required for httpOnly cookie auth
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds OWASP-recommended security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains"
            )
        return response


app.add_middleware(SecurityHeadersMiddleware)


# ---------------------------------------------------------------------------
# Request/response logging (structured JSON)
# ---------------------------------------------------------------------------


_access_logger = logging.getLogger("app.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every request with method, path, status, and duration.

    Also injects a unique X-Request-ID response header for log correlation.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        # Attach request_id to request state for use in exception handlers
        request.state.request_id = request_id

        response = await call_next(request)
        duration_ms = round((time.monotonic() - start) * 1000, 1)

        response.headers["X-Request-ID"] = request_id

        _access_logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": duration_ms,
            },
        )

        return response


app.add_middleware(RequestLoggingMiddleware)


# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled server errors.

    Logs the full stack trace (never leaks it to the client) and returns the
    standard error envelope with INTERNAL_ERROR code.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "unhandled_exception",
        exc_info=True,
        extra={"path": request.url.path, "request_id": request_id},
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Something went wrong. Please try again.",
                "request_id": request_id,
            }
        },
    )


# ---------------------------------------------------------------------------
# Startup / shutdown lifecycle
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup() -> None:
    """Perform startup tasks.

    - Logs the application startup with environment details.
    - Schedules the idempotency key cleanup as a background task.
    """
    logger.info(
        "app_starting",
        extra={
            "environment": settings.ENVIRONMENT,
            "log_level": settings.LOG_LEVEL,
        },
    )

    # Clean up expired idempotency keys from previous runs
    from app.database import AsyncSessionLocal
    from app.repositories.idempotency_repo import IdempotencyRepository

    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                repo = IdempotencyRepository(session)
                deleted = await repo.cleanup_expired()
                if deleted > 0:
                    logger.info(
                        "idempotency_cleanup",
                        extra={"deleted_count": deleted},
                    )
    except Exception:
        # Do not block startup if cleanup fails (DB may not be ready yet)
        logger.warning("idempotency_cleanup_failed", exc_info=True)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

# Health check — mounted at / level so /health resolves without the /api/v1 prefix
app.include_router(health.router)

# All API routers — mounted with /api/v1 prefix (defined in each router)
app.include_router(groups.router)
app.include_router(members.router)
app.include_router(expenses.router)
app.include_router(balances.router)
app.include_router(settle_up.router)
app.include_router(settlements.router)
app.include_router(dev.router)
