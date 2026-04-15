# FairSplit — Developer Guide

Zero-friction shared expense tracker. No accounts. No email. No password.
Members join via a shareable link with just a display name.

---

## Running Locally

The entire stack starts with a single command. No external services, no accounts, no credentials required.

```bash
cd workspace/fairsplit/src
docker compose up
```

Wait approximately 30 seconds for all services to become healthy. Then:

| Service      | URL                          | Credentials   |
|---|---|---|
| Frontend     | http://localhost:3000        | —             |
| Backend API  | http://localhost:8000        | —             |
| API docs     | http://localhost:8000/docs   | —             |
| Health check | http://localhost:8000/health | —             |
| Prometheus   | http://localhost:9090        | —             |
| Grafana      | http://localhost:3001        | admin / admin |
| Mailpit      | http://localhost:8025        | —             |

### Startup sequence

Docker Compose starts services in dependency order:

1. `db` — PostgreSQL 16 starts and becomes healthy (pg_isready passes)
2. `migrate` — runs `alembic upgrade head` then exits (restart: no)
3. `backend` — FastAPI starts after migrate completes successfully
4. `frontend` — Next.js starts after backend is healthy
5. `prometheus`, `grafana`, `mailpit` — start in parallel, no dependency on application services

### Stopping

```bash
docker compose down        # stop and remove containers, keep volumes
docker compose down -v     # stop and remove containers AND volumes (wipes DB)
```

---

## Seeding Test Data

The seed script creates pre-populated groups so developers can test the full UI without manually creating groups and expenses.

```bash
# Run once after docker compose up
docker compose exec backend python -m scripts.seed
```

The seed creates:
- **Group: "Weekend in Barcelona"** — 4 members (Maya as admin, Daniel, Priya, Alex)
- 6 expenses with a mix of split types (equal, custom_amount, custom_percentage)
- 2 recorded settlements
- Realistic balances (not all settled — so settle-up returns transfers)

### Seeded accounts

The seed script prints the invite links and member tokens to stdout after running. You can also use the dev panel (see below) to jump directly into a seeded group.

---

## Dev Panel

The login page shows a dev panel when `NEXT_PUBLIC_SHOW_DEV_PANEL=true` (set automatically by docker-compose via Dockerfile ARG — never via `NODE_ENV`).

The panel lists seeded group members with click-to-fill tokens. Click any entry to jump directly into that member's session without entering a display name or invite token.

At minimum the panel shows:
- One admin member in the "Weekend in Barcelona" group (Maya)
- One regular member (Daniel)

The dev panel is gated on the build arg — it does not appear in staging or production builds (those set `NEXT_PUBLIC_SHOW_DEV_PANEL=false`).

---

## Environment Variables

All environment variables are set automatically by `docker-compose.yml` for local development.

To run services outside Docker (for example, pytest against a local Postgres), copy `.env.local.example`:

```bash
cp .env.local.example .env.local
```

### Backend variables

| Variable        | Required | Default (local)                                              | Description |
|---|---|---|---|
| `DATABASE_URL`  | Yes      | `postgresql+asyncpg://fairsplit:fairsplit_dev@db:5432/fairsplit` | asyncpg connection string |
| `SECRET_KEY`    | Yes      | `dev-secret-key-change-in-production-minimum-32-chars` | JWT signing secret (min 32 chars) |
| `CORS_ORIGINS`  | Yes      | `http://localhost:3000` | Comma-separated allowed origins |
| `ENVIRONMENT`   | No       | `development` | `development` or `production` |
| `LOG_LEVEL`     | No       | `INFO` | Structured log level |
| `APP_BASE_URL`  | No       | `http://localhost:3000` | Base URL for invite links in settle-up clipboard text |

### Frontend variables (build-time ARGs + runtime ENVs)

| Variable                      | Required | Default (local) | Description |
|---|---|---|---|
| `NEXT_PUBLIC_API_URL`         | Yes      | `http://localhost:8000` | Backend URL consumed by browser |
| `NEXT_PUBLIC_SHOW_DEV_PANEL`  | No       | `true` | Show dev panel (Dockerfile ARG — not NODE_ENV) |

### Staging / production secrets (GitHub Secrets)

| Secret                    | Used by | Description |
|---|---|---|
| `FLY_API_TOKEN`           | CD      | Fly.io personal access token |
| `VERCEL_TOKEN`            | CD      | Vercel deployment token |
| `VERCEL_ORG_ID`           | CD      | Vercel organization ID |
| `VERCEL_PROJECT_ID`       | CD      | Vercel project ID |
| `PRODUCTION_API_URL`      | CD, smoke test | `https://fairsplit-backend.fly.dev` |
| `PRODUCTION_FRONTEND_URL` | CD, smoke test | `https://fairsplit.vercel.app` |
| `VPS_SSH_KEY`             | CD (VPS path) | Private SSH key for VPS deployment |
| `VPS_HOST`                | CD (VPS path) | VPS hostname or IP |
| `VPS_USER`                | CD (VPS path) | SSH username |

### GitHub repository variables (not secrets)

| Variable        | Values             | Description |
|---|---|---|
| `DEPLOY_TARGET` | `fly` (default), `vercel`, `vps` | Controls which deploy step runs |

---

## Running Tests

Tests run against a PostgreSQL test database (separate from the dev database).

```bash
# Inside the backend container
docker compose exec backend pytest tests/ -v

# Or locally with a .env.local pointing at a test DB
DATABASE_URL=postgresql+asyncpg://fairsplit:fairsplit_test@localhost:5432/fairsplit_test \
  pytest backend/tests/ -v --cov=app
```

The critical test file is `tests/test_settle_service.py` — it contains the six required unit test cases for the settle-up algorithm. This file must pass before any PR is merged.

---

## Monorepo Structure

```
src/
├── backend/
│   ├── app/
│   │   ├── config.py              — Pydantic settings (all env-var driven)
│   │   ├── database.py            — Async SQLAlchemy engine + session factory
│   │   ├── logging_config.py      — Structured JSON logging
│   │   ├── main.py                — FastAPI app, middleware, router registration
│   │   ├── middleware/
│   │   │   └── auth_middleware.py — JWT cookie/header extraction, MemberContext injection
│   │   ├── models/                — SQLAlchemy ORM models (Group, Member, Expense, etc.)
│   │   ├── repositories/          — DB query functions (async, typed)
│   │   ├── routers/               — FastAPI routers (groups, members, expenses, balances, settle_up, settlements, health)
│   │   └── services/
│   │       ├── settle_service.py  — Greedy min-transfer algorithm (hero feature)
│   │       ├── balance_service.py — CTE balance aggregation query
│   │       └── idempotency_service.py — Idempotency key check/store
│   ├── migrations/
│   │   ├── env.py                 — Alembic async env (NullPool, DATABASE_URL from env)
│   │   └── versions/              — Migration scripts
│   ├── tests/
│   │   └── test_settle_service.py — Settle-up unit tests (6 required cases)
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/app/                   — Next.js 16 App Router pages
│   │   ├── page.tsx               — Landing / create group
│   │   ├── join/[token]/          — Join group flow
│   │   └── groups/[id]/           — Group dashboard (expenses, balances, settle-up)
│   ├── Dockerfile
│   └── package.json
├── infra/
│   ├── prometheus/
│   │   └── prometheus.yml         — Scrape config (backend:8000/metrics, 15s interval)
│   └── grafana/
│       └── provisioning/
│           ├── datasources/
│           │   └── prometheus.yml — Auto-provision Prometheus datasource
│           └── dashboards/
│               ├── dashboard.yml  — Dashboard provider config
│               └── fairsplit.json — FairSplit metrics dashboard (4 panels + 8 charts)
├── .github/
│   └── workflows/
│       ├── ci.yml                 — PR checks: lint, test, docker build, security scan
│       └── cd.yml                 — Deploy on merge to main: build, migrate, deploy, smoke test
├── docker-compose.yml
├── smoke_test.py
└── .env.local.example
```

---

## CI/CD Pipeline

### CI (every pull request)

Four jobs run in parallel:

| Job | What it does | Target time |
|---|---|---|
| `lint-backend` | ruff check + ruff format --check | < 30s |
| `lint-frontend` | ESLint + tsc --noEmit | < 60s |
| `test-backend` | pytest with postgres service container, coverage report | < 2 min |
| `build-docker` | docker build backend + frontend (validates Dockerfiles) | < 3 min |
| `security-scan` | pip-audit + npm audit + Trivy container scan | < 2 min |

Target: all jobs complete in under 5 minutes on a standard PR.

### CD (merge to main)

Sequential stages with rollback on failure:

1. CI checks (re-run inline to ensure no race with force-push)
2. Build and push images to GHCR (tagged with `sha-{commit}` and `latest`)
3. Run Alembic migrations (`fly ssh console` or direct DB connection)
4. Deploy backend (Fly.io rolling deploy or VPS Docker swap)
5. Deploy frontend (Vercel or Fly.io)
6. Smoke test (`smoke_test.py` against production URLs)
7. Rollback if smoke test fails (`flyctl releases rollback`)

Target: production deployment completes in under 10 minutes from merge.

### Deploy target selection

Set the GitHub repository variable `DEPLOY_TARGET`:
- `fly` (default) — backend to Fly.io, frontend to Fly.io
- `vercel` — frontend to Vercel, backend to Fly.io
- `vps` — both services to self-hosted VPS via SSH + Docker

---

## Observability

### Logs

All backend logs are structured JSON to stdout. Every request includes:
```json
{
  "timestamp": "2026-04-15T12:00:00.000Z",
  "level": "INFO",
  "logger": "app.middleware.logging",
  "message": "request completed",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "method": "GET",
  "path": "/api/v1/groups/abc/balances",
  "status": 200,
  "duration_ms": 42,
  "group_id": "abc",
  "member_id": "xyz"
}
```

Errors include `"exception"` with full traceback.

### Metrics

The backend exposes Prometheus metrics at `GET /metrics` via `prometheus-fastapi-instrumentator`. Prometheus scrapes this endpoint every 15 seconds.

### Grafana dashboard

The FairSplit dashboard (auto-provisioned, no manual setup) contains:

- **Overview row:** Request rate, error rate (5xx), p95 latency, active groups — all as stat panels
- **Request Throughput row:** Request rate by endpoint, error rate by HTTP status code
- **Latency Percentiles row:** p50/p95/p99 over time, p95 by endpoint
- **Business Metrics row:** Active groups + members over time, write operation rate (expenses/settlements/groups created)

Access at http://localhost:3001 (admin/admin).

### Health endpoint

```
GET /health

Response 200:
{
  "status": "ok",
  "version": "1.0.0",
  "db": "ok"
}
```

The health endpoint is public (no auth required) and responds within 200ms p95. It is used by Docker Compose healthchecks, the CD smoke test, and UptimeRobot/Uptime Kuma for uptime monitoring.

---

## Key Design Decisions

- **All money is integer cents.** `amount_cents: int`. Never float, never Decimal in API responses. `$42.00 = 4200`.
- **No accounts, no email.** Session = JWT in httpOnly cookie (primary) + localStorage cache. Join via invite link with display name only.
- **Idempotency on all mutations.** POST requests to `/expenses` and `/groups` require `X-Idempotency-Key` header (client UUID). Prevents duplicate expense submission on slow connections.
- **Balance polling, not WebSockets.** SWR with `refreshInterval: 10000` on balances and expenses. Simpler, more reliable, adequate for this use case.
- **Settle-up at read time.** The minimum-transfer algorithm runs on every `GET /settle-up` call — not stored. O(n log n) greedy max-heap, < 50ms for 20 members.
- **Soft deletes.** Expenses and settlements have `deleted_at` — reversible. Hard deletes are not supported.
