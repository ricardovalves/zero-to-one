# ── Stage 1: builder ────────────────────────────────────────────────────────
# Install all Python dependencies using uv for fast, reproducible installs.
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files first for layer caching
COPY requirements.txt ./

# Create venv at /app/.venv — must match the runner stage path exactly.
# If the venv is created at /build/.venv and copied to /app/.venv, the
# shebang lines in scripts like `alembic` still point to /build/.venv/bin/python,
# which does not exist in the runner, causing "no such file or directory" on exec.
RUN uv venv /app/.venv && \
    uv pip install --no-cache --python /app/.venv/bin/python -r requirements.txt

# ── Stage 2: production runner ───────────────────────────────────────────────
# Minimal runtime image — no build tools, no pip, no uv.
FROM python:3.12-slim AS runner

# Install curl for the health check only (added to slim image)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user for the application process
RUN groupadd --gid 1001 app && \
    useradd --uid 1001 --gid 1001 --no-create-home app

WORKDIR /app

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY alembic.ini ./
COPY migrations/ ./migrations/
COPY app/ ./app/

# Ensure venv binaries take precedence on PATH
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Drop privileges
USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start uvicorn with a single worker in development; use gunicorn in production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
