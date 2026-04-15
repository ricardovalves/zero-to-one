# CTO/Architect Handoff — FairSplit

**Date:** 2026-04-15  
**Authored by:** CTO/Architect Agent

---

## Key Facts for Downstream Agents

1. **Backend language + framework:** Python 3.12 + FastAPI 0.135.x — ASGI via uvicorn 0.34.x
2. **Frontend:** Next.js 16.2.x (App Router, React 19) — local Docker port 3000; staging on Vercel free tier
3. **Database:** PostgreSQL 16.13 (`postgres:16-alpine`) — local Docker; staging on Fly Postgres free tier — ORM: SQLAlchemy 2.0 async + asyncpg driver + Alembic 1.14.x migrations
4. **Auth strategy:** Custom JWT (PyJWT 2.10.x, HS256) — httpOnly SameSite=Lax cookie (primary, Safari ITP safe) + Bearer token header (fallback) — 30-day rolling expiry — NO email, NO password, NO bcrypt (display name only)
5. **API base URL pattern:** `http://localhost:8000/api/v1/` (local) — versioned as `/api/v1/...` — full spec in `api-spec.yaml`
6. **Key external services:** NONE — this is the defining architectural constraint. Zero external accounts, APIs, or cloud services required.
7. **Monorepo structure:** `src/backend/` + `src/frontend/` + `src/infra/`
8. **CI/CD:** GitHub Actions — CI (lint + type check + unit + integration + security audit + docker build) on every PR; CD (migrate + deploy + smoke test) on merge to main
9. **Critical performance constraints:** Balance endpoint < 200ms p95 (polled every 10 seconds by all active clients); settle-up algorithm < 100ms p95 for 50 members; expense save < 300ms p95
10. **Prototype vs production split:** Local = `docker compose up` (zero config); staging = Fly.io free tier + Vercel free; production = Fly.io hobby ($5–10/month) or $6/month VPS with Coolify

---

## Session Model (READ THIS CAREFULLY — it is non-obvious)

The session model for anonymous members uses **two layers**:

- **Layer 1 (authoritative):** Server-set `httpOnly`, `Secure`, `SameSite=Lax` cookie named `fairsplit_member_token`. This is the source of truth. Safari ITP does NOT clear `httpOnly` cookies set by the server. Cookie expiry: 30 days rolling.
- **Layer 2 (read cache):** The JWT token is also returned in the response body on join/create. The frontend stores it in `localStorage` as a convenience cache for client-side reads. If `localStorage` is cleared by ITP, the cookie persists and the API continues to work. The frontend should read from `localStorage` first; if absent, make a `/members/me` request (which uses the cookie) to recover the token.

JWT payload: `{sub: member_id, group_id: group_id, is_admin: bool, iat: unix_timestamp, exp: unix_timestamp}`.

The server extracts the member's context from the token on every authenticated request. There is no session table in the database — the JWT is stateless.

---

## For Backend Engineer

### Router structure (`src/backend/routers/`)
- `groups.py` — `POST /groups`, `GET /groups/{id}`, `PATCH /groups/{id}`, `POST /groups/{id}/invite`
- `members.py` — `POST /join/{invite_token}`, `GET /groups/{id}/members`, `GET /groups/{id}/members/me`
- `expenses.py` — `GET/POST /groups/{id}/expenses`, `GET/PATCH/DELETE /groups/{id}/expenses/{expense_id}`
- `balances.py` — `GET /groups/{id}/balances`, `GET /groups/{id}/balances/{member_id}`
- `settle_up.py` — `GET /groups/{id}/settle-up`
- `settlements.py` — `GET/POST /groups/{id}/settlements`, `DELETE /groups/{id}/settlements/{settlement_id}`
- `health.py` — `GET /health`

### Database tables (all 5 must be created in migration order)
`groups` → `members` → `expenses` → `expense_splits` → `settlements` + `idempotency_keys`

### Auth middleware
`src/backend/middleware/auth_middleware.py` — reads `fairsplit_member_token` cookie first, falls back to `Authorization: Bearer` header. Raises 401 on missing/invalid/expired token. Injects `current_member: MemberContext` into the request state. Apply to all routes except `GET /health` and `POST /join/{invite_token}` and `POST /groups`.

Wait — correction: `POST /groups` ALSO issues a token (group creator is auto-joined as admin), so it does not require an existing session but DOES create one. `POST /join/{invite_token}` similarly. The health endpoint is fully public.

### Service layer pattern
- `services/settle_service.py` — contains `compute_settle_up(net_balances, member_names, currency)` — see C4 Level 4 code in `technical-spec.md §1`
- `services/balance_service.py` — runs the CTE query from `technical-spec.md §3 Query 1`
- `services/idempotency_service.py` — check/store idempotency keys before/after mutation
- All services receive an `AsyncSession` as the first argument (dependency injection via FastAPI `Depends`)

### Critical: All monetary amounts are integer cents
- `amount_cents: int` in all Pydantic schemas and database columns
- The frontend sends integer cents (not decimal strings) for all API requests
- Display formatting (`"$42.00"`) is computed from cents at the API response layer using a `format_cents(cents, currency)` helper
- Rounding for custom_percentage splits: any 1-cent remainder is added to the first member's split sorted alphabetically by `display_name`

### Idempotency key handling
Check `idempotency_keys` table before processing any POST mutation. If key exists and not expired: return stored `response_body` with stored `status_code`. If key does not exist: process the mutation, then INSERT the idempotency key with the response inside the same transaction.

### Structured JSON logging (mandatory)
Every request logged with: `timestamp`, `level`, `request_id`, `method`, `path`, `status`, `duration_ms`, `group_id` (if applicable), `member_id` (if applicable). Use `structlog` or Python's `logging` with a JSON formatter. Every exception logged with `exc_info=True`.

---

## For Frontend Engineer

### API client base URL
`NEXT_PUBLIC_API_URL` environment variable. Default for local: `http://localhost:8000`. Use `credentials: "include"` on every fetch call to send the httpOnly cookie cross-origin.

### Auth token storage
- **Cookie (primary):** Set by server. Read by server. Never access it from JavaScript.
- **localStorage (cache):** Store the `token` from join/create response as `fairsplit_token_{group_id}`. Read this for client-side operations that need the decoded member_id. If missing, call `GET /api/v1/groups/{id}/members/me` (uses cookie) to recover.
- **Never** redirect to the join page just because localStorage is empty — always attempt the `/members/me` call first.

### Response envelope (NON-NEGOTIABLE — verify in api-spec.yaml)
- **Singleton endpoints** (auth, GET /groups/{id}, GET /groups/{id}/expenses/{id}, GET /groups/{id}/members/me, etc.): return the resource object directly. `response.data` (axios) or `await res.json()` (fetch) IS the resource. No `.data` wrapper.
- **List endpoints** (GET /groups/{id}/expenses, GET /groups/{id}/members, GET /groups/{id}/settlements): return `{data: T[], total: int, page: int, per_page: int}`. The array is at `response.data.data` (axios) or `(await res.json()).data` (fetch).
- **Join/Create group:** Returns `{group, member, token}` — THREE fields at the top level.
- **Settle-up:** Returns `{group_name, currency, all_settled, transfer_count, transfers, clipboard_text, computed_at}`.

### Key feature endpoints
1. `POST /api/v1/groups` — group creation + first session
2. `POST /api/v1/join/{invite_token}` — group join + session
3. `GET /api/v1/groups/{id}/balances` — polled every 10s via SWR `refreshInterval`
4. `GET /api/v1/groups/{id}/settle-up` — the hero feature

### Polling
Use SWR with `refreshInterval: 10000` on the balances and expenses hooks. Do NOT use WebSockets. The backend is not set up for WebSocket connections.

### Dev login panel
Gate on `NEXT_PUBLIC_SHOW_DEV_PANEL === "true"` (Dockerfile ARG, set in docker-compose). Show seeded group links and member session tokens so developers can jump into a pre-populated group without creating a new one. The panel must list at least one admin member and one regular member per seeded group, with click-to-join links.

### Mobile-first requirements
- Amount inputs: `inputMode="decimal"` for numeric keypad on iOS/Android
- Minimum touch target: 44px
- Group join flow must complete in < 60 seconds (time from opening link to seeing expense list)
- Draft persistence: store form state in `localStorage` under `fairsplit_draft_{group_id}`. Clear on successful save.

---

## For DB Engineer

### Schema DDL
Complete runnable SQL is in `technical-spec.md §3`. Copy it directly — all constraints, indexes, and triggers are specified. Do not paraphrase.

### Critical indexes (must implement exactly as written)
- `idx_expenses_group_id_active` — partial index WHERE `deleted_at IS NULL` — critical for expense list and balance query performance
- `idx_expenses_group_id_not_deleted` — partial index for balance CTE
- `idx_settlements_group_id_active` — partial index WHERE `deleted_at IS NULL`
- `idx_groups_invite_token` — unique index on `invite_token` — used on every join flow
- `idx_members_group_id` — non-unique, used on every group dashboard load

### Migration order (dependency order)
1. Create `groups` table
2. Create `members` table (FK → groups)
3. Create `expenses` table (FK → groups, FK → members × 2)
4. Create `expense_splits` table (FK → expenses, FK → members)
5. Create `settlements` table (FK → groups, FK → members × 2)
6. Create `idempotency_keys` table (standalone)
7. Create `set_updated_at()` trigger function
8. Apply trigger to all 5 entity tables

### Key schema notes
- `expenses.amount_cents`: INTEGER, CHECK > 0. No FLOAT or NUMERIC for money.
- `expense_splits.amount_cents`: INTEGER, CHECK >= 0 (can be 0 for record-keeping edge case).
- `expense_splits.percentage`: NUMERIC(6,3), nullable — stored for display only; `amount_cents` is authoritative.
- `expenses.deleted_at`: TIMESTAMPTZ, nullable — soft delete pattern.
- `settlements.deleted_at`: TIMESTAMPTZ, nullable — soft delete (reversible settlements).
- `idempotency_keys.expires_at`: TIMESTAMPTZ — run `DELETE FROM idempotency_keys WHERE expires_at < NOW()` as a periodic cleanup (cron or startup task).

### Alembic async pattern (required)
Use `async_engine_from_config` and `connection.run_sync(do_run_migrations)` in `env.py`. Use `NullPool` for migrations. Import ALL models in `env.py` before accessing `Base.metadata`. Load DATABASE_URL from environment variable (not hardcoded in `alembic.ini`).

---

## For Infra Engineer

### Docker (one Dockerfile per service)
- `src/backend/Dockerfile` — `FROM python:3.12-slim`, install with `uv`, copy source, run `uvicorn`
- `src/frontend/Dockerfile` — multi-stage build: `node:20-alpine` builder → `node:20-alpine` runner

### Local stack (zero external dependencies)
```bash
docker compose up  # starts: db, migrate, backend, frontend, prometheus, grafana
```
All ports: DB=5432, Backend=8000, Frontend=3000, Prometheus=9090, Grafana=3001.
Grafana default login: admin/admin.

### Environment variables (all required for backend)
```
DATABASE_URL=postgresql+asyncpg://fairsplit:fairsplit_dev@db:5432/fairsplit
SECRET_KEY=<minimum 32 random characters — generate with: python -c "import secrets; print(secrets.token_hex(32))">
CORS_ORIGINS=http://localhost:3000
ENVIRONMENT=development  # or: production
```

### Environment variables (frontend)
```
NEXT_PUBLIC_API_URL=http://localhost:8000  # backend URL
NEXT_PUBLIC_SHOW_DEV_PANEL=true           # Dockerfile ARG — dev panel visibility
```

### Staging (Fly.io + Vercel)
- Backend: `fly launch` + `fly secrets set SECRET_KEY=...` + `fly deploy`
- Frontend: `vercel deploy --prod` (auto-detects Next.js)
- Database: `fly postgres create` (free shared instance, 1GB storage)
- Run migrations before deploy: add to CD pipeline as `fly ssh console -C "alembic upgrade head"` or use the ephemeral `migrate` service in docker-compose pattern adapted for Fly.io

### Monitoring (provisioned automatically)
- `src/infra/prometheus/prometheus.yml` — scrapes backend `/metrics` endpoint
- `src/infra/grafana/provisioning/` — auto-provisions Prometheus datasource and FairSplit dashboard
- No manual Grafana setup after `docker compose up`

### Security headers
The backend should set all security headers documented in `technical-spec.md §5`. For staging/production, configure HTTPS at the Fly.io / Vercel layer (automatic). `SameSite=Lax` on the session cookie requires HTTPS in production (Fly.io provides this automatically).

---

## Assumptions Added (for assumptions.md)

See appended entries in `workspace/fairsplit/assumptions.md`.

---

## Files Written

- `workspace/fairsplit/technical-spec.md` — complete, no stubs
- `workspace/fairsplit/api-spec.yaml` — complete OpenAPI 3.1 spec (25+ endpoints)
- `workspace/fairsplit/handoffs/cto-architect.md` — this file
- `workspace/fairsplit/assumptions.md` — appended (architectural assumptions)
