"""Structured JSON logging configuration.

All log output is JSON to stdout. Every request is logged with method, path,
status, and duration. Every error is logged with exc_info=True.

Call configure_logging() once at startup in main.py before the app is created.
"""

import json
import logging
import sys
from datetime import datetime, timezone


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON object."""

    # Fields that are standard LogRecord attributes, not extra payload
    _SKIP_ATTRS = frozenset({
        "name", "msg", "args", "levelname", "levelno", "pathname",
        "filename", "module", "exc_info", "exc_text", "stack_info",
        "lineno", "funcName", "created", "msecs", "relativeCreated",
        "thread", "threadName", "processName", "process", "message",
        "taskName",
    })

    def format(self, record: logging.LogRecord) -> str:
        log: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log["exception"] = self.formatException(record.exc_info)

        # Include any extra fields passed via logger.info("msg", extra={...})
        for key, val in record.__dict__.items():
            if key not in self._SKIP_ATTRS and not key.startswith("_"):
                log[key] = val

        return json.dumps(log, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with structured JSON output.

    Must be called before the FastAPI app is created so that all loggers
    (including uvicorn's internal ones) inherit the handler.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Suppress noisy third-party loggers that produce high-cardinality noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
