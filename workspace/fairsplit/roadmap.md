# FairSplit — Project Roadmap

**Version:** 1.0  
**Date:** 2026-04-15  
**Author:** Project Manager Agent  
**Status:** Ready for Engineering

---

## Project Overview

FairSplit is a zero-friction shared expense tracker. Users create a group, share a link, members join with a display name only (no accounts), log expenses, and settle debts with a single tap using a minimum-transfer algorithm. The entire product runs with `docker compose up` — zero external services, zero API keys.

**Start date:** 2026-04-20 (Monday)  
**Target completion:** 2026-06-12 (end of Sprint 3)  
**Sprint length:** 2 weeks  
**Total sprints:** 3 (plus pre-sprint foundation week)  
**Team capacity assumption:** 70% of nominal — accounts for PR review, meetings, and unexpected issues.

---

## Timeline (Gantt-Style ASCII)

```
                          APR 20        MAY 4         MAY 18        JUN 1         JUN 15
                          |             |             |             |             |
Sprint 0 (Foundation)     |=============|             |             |             |
Sprint 1 (Core CRUD)                   |=============|             |             |
Sprint 2 (Hero Feature)                              |=============|             |
Sprint 3 (Polish + CI/CD)                                          |=============|

─────────────────────────────────────────────────────────────────────────────────────────
Epic 1: Foundation
  DB schema + migrations   |====|        |             |             |             |
  Backend skeleton         |=======|     |             |             |             |
  Frontend skeleton        |=======|     |             |             |             |
  Docker Compose stack     |=====|       |             |             |             |
─────────────────────────────────────────────────────────────────────────────────────────
Epic 2: Group + Auth
  Group creation API             |=====| |             |             |             |
  Join via invite link API       |=====| |             |             |             |
  Session middleware             |===|   |             |             |             |
  Group creation UI              |=======|             |             |             |
  Join flow UI                   |=======|             |             |             |
─────────────────────────────────────────────────────────────────────────────────────────
Epic 3: Expense Logging
  Expense CRUD API                       |=============|             |             |
  Balance computation API                |=============|             |             |
  Expense form UI (equal split)          |=========|   |             |             |
  Custom split modes UI                  |=============|             |             |
  Expense list + detail UI               |=======|     |             |             |
─────────────────────────────────────────────────────────────────────────────────────────
Epic 4: Settle-Up (Hero)
  Settle algorithm + unit tests                        |=====|       |             |
  Settle-up API endpoint                               |=====|       |             |
  Settle-up UI (plan + copy)                           |=========|   |             |
  Settlement recording API                             |===|         |             |
  Mark-as-paid UI                                      |=====|       |             |
─────────────────────────────────────────────────────────────────────────────────────────
Epic 5: Polish + Infra
  10s polling + SWR                                    |====|        |             |
  Draft persistence + idempotency                      |====|        |             |
  Dev login panel                                                    |===|         |
  GitHub Actions CI                                                  |=======|     |
  GitHub Actions CD                                                  |=======|     |
  Prometheus + Grafana                                               |=====|       |
  Smoke tests                                                        |=========|   |
  Seed data                                                          |=====|       |
─────────────────────────────────────────────────────────────────────────────────────────
```

---

## Epic Breakdown

### Epic 0: Foundation
**Owner:** db-engineer + infra-engineer + backend-engineer + frontend-engineer (parallel)  
**Sprint:** 0 (Week 1–2, Apr 20 – May 3)  
**Done when:** `docker compose up` starts all services cleanly; `GET /health` returns 200; the Next.js landing page renders; Alembic migrations run to completion; no engineer is blocked on environment setup.  
**Critical path:** Yes — nothing else can start until this is done.

---

### Epic 1: Group Creation and Anonymous Auth
**Owner:** backend-engineer + frontend-engineer (parallel after Epic 0)  
**Sprint:** 1 (Week 3–4, May 4 – May 17)  
**Done when:** A user can create a group via the UI, receive an invite link, and a second user can join via that link with only a display name. Session cookie and localStorage are both set. Both users see the group dashboard.  
**Critical path:** Yes — expense logging, balances, and settle-up all require a valid member session.

---

### Epic 2: Expense Logging and Balance View
**Owner:** backend-engineer + frontend-engineer (parallel after Epic 1 API is unblocked)  
**Sprint:** 1 (partially) + Sprint 2 (May 4 – May 17)  
**Done when:** Members can log an expense with equal split; custom-amount split; custom-percentage split. The expense list shows all expenses. The balance view shows each member's net balance. Balances recompute in real time after every expense mutation.  
**Critical path:** Yes — the settle-up epic depends on having expenses and net balances in the system.

---

### Epic 3: Settle-Up (Hero Feature)
**Owner:** backend-engineer (algorithm) + frontend-engineer (plan UI)  
**Sprint:** 2 (Week 5–6, May 18 – May 31)  
**Done when:** The minimum-transfer algorithm is implemented, all unit test cases from PRD Section 6 pass, `GET /groups/{id}/settle-up` returns the correct transfer plan, the UI renders the plan, the "Copy Payment Plan" button writes formatted plain text to the clipboard, and Mark-as-Paid flow records a settlement and updates balances.  
**Critical path:** Yes — this is the product's hero feature. Any delay here directly delays launch.

---

### Epic 4: Infrastructure, CI/CD, and Polish
**Owner:** infra-engineer + backend-engineer + frontend-engineer  
**Sprint:** 3 (Week 7–8, Jun 1 – Jun 12)  
**Done when:** GitHub Actions CI runs on every PR (lint, type check, unit tests, docker build). CD deploys on merge to main. Prometheus scrapes backend metrics. Grafana auto-provisions dashboard. Dev panel shows seeded groups with click-to-join. Smoke tests pass. Seed script populates at least two groups with realistic expenses and settlements.

---

## Sprint Plan

### Sprint 0 — Foundation (Apr 20 – May 3) — 28 story points

**Goal:** Every engineer can run the stack locally and be unblocked for feature work on Day 1 of Sprint 1.

**Rule:** No feature work in this sprint. Foundation only.

| # | Issue | Team | Est | Depends on |
|---|---|---|---|---|
| F-01 | [INFRA] Implement: Docker Compose stack (db, migrate, backend, frontend, prometheus, grafana) | infra | 5 | — |
| F-02 | [DB] Implement: Alembic async setup + all 6 entity migrations in dependency order | db | 5 | F-01 |
| F-03 | [BE] Implement: FastAPI app skeleton (config, db session, CORS, structured JSON logging, /health endpoint) | backend | 3 | F-01 |
| F-04 | [BE] Implement: Auth middleware (cookie-first, Bearer fallback, MemberContext injection) | backend | 3 | F-03 |
| F-05 | [FE] Implement: Next.js 16 app skeleton (App Router, Tailwind 4, shadcn/ui, api-client.ts, session.ts, format.ts) | frontend | 5 | F-01 |
| F-06 | [FE] Implement: Route structure and layout components (bottom nav, page shells, loading/error boundaries) | frontend | 3 | F-05 |
| F-07 | [BE] Implement: Idempotency service (check/store key in same transaction, 24-hour expiry cleanup) | backend | 3 | F-03, F-02 |
| F-08 | [INFRA] Implement: Prometheus config + Grafana auto-provisioning (datasource + FairSplit dashboard) | infra | 2 | F-01 |

**Sprint 0 total:** 29 pts. At 70% capacity across 4 engineers (4 × 8 pts nominal = 32 pts available at 70% = ~22 pts). Distribute: DB+Infra run in parallel on the Docker/migration work; Backend+Frontend start their skeletons once Docker is up (Day 2). This sprint is tight — F-01 must complete by Day 2 to unblock F-02 through F-06.

**Critical path in Sprint 0:** F-01 → F-02 (DB schema must exist before any service layer touches the database) and F-01 → F-05 (frontend needs the Docker network).

---

### Sprint 1 — Group + Auth + Expense CRUD (May 4 – May 17) — 42 story points

**Goal:** Users can create a group, share an invite link, join via that link, and log expenses (all three split modes). Balance view shows correct net amounts.

| # | Issue | Team | Est | Depends on |
|---|---|---|---|---|
| G-01 | [BE] Implement: POST /api/v1/groups (create group, auto-join creator as admin, issue JWT, set cookie) | backend | 3 | F-04, F-07 |
| G-02 | [BE] Implement: POST /api/v1/join/{invite_token} (validate token, create member, issue JWT, set cookie) | backend | 3 | F-04, F-07 |
| G-03 | [BE] Implement: GET /api/v1/groups/{id} and GET /api/v1/groups/{id}/members | backend | 2 | G-01 |
| G-04 | [BE] Implement: POST /api/v1/groups/{id}/invite (rotate invite token, return new link) | backend | 2 | G-01 |
| G-05 | [BE] Implement: GET /api/v1/groups/{id}/members/me (cookie-based session recovery endpoint) | backend | 1 | G-02 |
| G-06 | [FE] Implement: Home page (Create Group CTA) and create-group form (name, description, your name, POST /groups) | frontend | 3 | G-01, F-06 |
| G-07 | [FE] Implement: Join group page (/join/[inviteToken]) — display name form, POST /join/:token, session storage | frontend | 3 | G-02, F-06 |
| G-08 | [FE] Implement: Session recovery logic (localStorage miss → GET /members/me → restore token, never redirect directly to join) | frontend | 2 | G-05 |
| G-09 | [FE] Implement: Group dashboard shell — member list, balance card placeholders, invite link share (Web Share API + copy fallback) | frontend | 3 | G-03, G-04 |
| E-01 | [BE] Implement: POST /api/v1/groups/{id}/expenses (create expense, validate splits sum to total, idempotency key) | backend | 5 | G-01, F-07 |
| E-02 | [BE] Implement: GET /api/v1/groups/{id}/expenses (list, pagination) and GET /groups/{id}/expenses/{id} (detail) | backend | 3 | E-01 |
| E-03 | [BE] Implement: PATCH /api/v1/groups/{id}/expenses/{id} (edit, re-validate splits, recalculate) | backend | 3 | E-01 |
| E-04 | [BE] Implement: DELETE /api/v1/groups/{id}/expenses/{id} (soft delete via deleted_at) | backend | 2 | E-01 |
| E-05 | [BE] Implement: GET /api/v1/groups/{id}/balances (CTE query — net balance per member from expenses minus settlements) | backend | 5 | E-01 |
| E-06 | [FE] Implement: Add expense form — equal split mode (description, amount, payer dropdown, split-among multi-select, idempotency key) | frontend | 3 | E-01, G-09 |
| E-07 | [FE] Implement: Custom amount and custom percentage split modes in expense form (real-time validation: sums must match) | frontend | 3 | E-06 |
| E-08 | [FE] Implement: Expense list on dashboard (expense cards, empty state, tap to detail view) | frontend | 3 | E-02, G-09 |
| E-09 | [FE] Implement: Expense detail page — full breakdown per person, edit and delete actions (permission-gated) | frontend | 3 | E-03, E-04, E-08 |
| E-10 | [FE] Implement: Balance view — personal hero balance card (owed/owes/settled), all-members balance list, green/red/gray convention | frontend | 3 | E-05, G-09 |

**Sprint 1 total:** 52 pts. Backend and frontend work in parallel. Backend engineer handles G-01 through G-05 and E-01 through E-05 sequentially (the API surface must exist before the FE can integrate). Frontend starts G-06/G-07 on Day 1 against mock data, integrates live API by Day 4 when G-01/G-02 are done. Flag: E-05 (balance CTE) is the most complex backend task — assign it maximum focus, no context-switching.

---

### Sprint 2 — Settle-Up, Settlements, and 10s Polling (May 18 – May 31) — 38 story points

**Goal:** The hero feature is working end-to-end. Users can see the minimum-transfer plan, copy it to clipboard, and mark transfers as paid. Balances auto-refresh every 10 seconds.

| # | Issue | Team | Est | Depends on |
|---|---|---|---|---|
| S-01 | [BE] Implement: compute_settle_up() — greedy max-heap algorithm in settle_service.py with all PRD unit test cases passing | backend | 5 | E-05 |
| S-02 | [BE] Implement: GET /api/v1/groups/{id}/settle-up (compute at read time, return transfers + clipboard_text + all_settled flag) | backend | 3 | S-01 |
| S-03 | [BE] Implement: POST /api/v1/groups/{id}/settlements (record a payer→payee settlement, update net balances) | backend | 3 | G-01 |
| S-04 | [BE] Implement: DELETE /api/v1/groups/{id}/settlements/{id} (reverse a settlement, soft delete) | backend | 2 | S-03 |
| S-05 | [FE] Implement: Settle-up page — transfer list (from API), "Copy Payment Plan" button (navigator.clipboard + fallback), all-settled empty state + confetti | frontend | 5 | S-02 |
| S-06 | [FE] Implement: Mark-as-Paid flow — confirmation dialog, POST /settlements, balance refresh, settlement appears in expense feed | frontend | 3 | S-03, S-05 |
| S-07 | [FE] Implement: SWR hooks — useBalances (10s refreshInterval), useExpenses, useSettleUp — no loading indicator on background refresh, skeleton on initial load | frontend | 3 | E-05, S-02 |
| S-08 | [FE] Implement: Expense form draft persistence — write to localStorage on beforeunload, restore on mount, clear on successful save | frontend | 2 | E-06 |
| S-09 | [FE] Implement: Idempotency key generation in expense form — crypto.randomUUID() on mount, regenerate on successful submit, send as X-Idempotency-Key header | frontend | 1 | E-06 |
| S-10 | [BE] Write: Exhaustive unit tests for compute_settle_up() — all PRD test cases: 2-member, 3-member circular, 4+ member complex, all-settled, single-cent remainder | backend | 5 | S-01 |
| S-11 | [BE] Write: Integration tests for /groups, /join, /expenses, /balances, /settle-up, /settlements endpoints | backend | 5 | S-02, S-04 |
| S-12 | [FE] Implement: Mobile-first responsiveness audit — 320px minimum width, 44px touch targets, inputMode="decimal" on all amount fields, safe-area-inset-bottom on bottom nav | frontend | 3 | S-05, E-10 |

**Sprint 2 total:** 40 pts. S-01 is the highest-risk task and the critical path item — the algorithm must be implemented and fully tested before S-02 and S-05 can be finalized. S-10 (unit tests) should be written alongside S-01, not after. Do not declare S-01 done without all test cases passing.

---

### Sprint 3 — CI/CD, Observability, Dev Panel, Smoke Tests (Jun 1 – Jun 12) — 32 story points

**Goal:** The product is ready to ship. GitHub Actions CI gates every PR. CD deploys to staging on merge. Dev panel shows seeded group links. All smoke tests pass. No engineer opens a PR and waits more than 10 minutes for CI feedback.

| # | Issue | Team | Est | Depends on |
|---|---|---|---|---|
| I-01 | [INFRA] Implement: GitHub Actions CI workflow — ruff lint, pyright type check, pytest unit+integration, frontend type check, pnpm build, docker build test | infra | 5 | S-11 |
| I-02 | [INFRA] Implement: GitHub Actions CD workflow — merge to main → alembic upgrade head (migrate service) → fly deploy (backend) → vercel deploy (frontend) | infra | 5 | I-01 |
| I-03 | [DB] Implement: seed.py — two seeded groups (Trip to Nashville 6 members, Roommates 3 members), realistic expenses (equal + custom split), one settlement, correct balances | db | 5 | S-03 |
| I-04 | [FE] Implement: Dev login panel (gated on NEXT_PUBLIC_SHOW_DEV_PANEL=true) — lists seeded groups with group names, one admin and one regular member per group, click-to-join links | frontend | 3 | I-03 |
| I-05 | [BE] Implement: /metrics endpoint (Prometheus exposition format via prometheus-fastapi-instrumentator) | backend | 2 | F-03 |
| I-06 | [INFRA] Implement: Grafana dashboard — request rate, p95 latency per endpoint, error rate, DB connection pool saturation | infra | 3 | I-05, F-08 |
| I-07 | [QA] Write: Smoke test suite — docker compose up + seed.py → assert login succeeds, frontend loads, seeded users see populated dashboard, GET /health 200, GET /balances 200 with non-empty data | backend | 5 | I-03, I-04 |
| I-08 | [INFRA] Implement: Backend security headers (X-Content-Type-Options, X-Frame-Options, Content-Security-Policy, Referrer-Policy) as FastAPI middleware | backend | 2 | F-03 |
| I-09 | [DB] Implement: idempotency_keys cleanup — startup task to DELETE WHERE expires_at < NOW() (prevents table bloat) | backend | 1 | F-07 |
| I-10 | [BE] Implement: PATCH /api/v1/groups/{id} (update group name/description — admin only) | backend | 1 | G-01 |

**Sprint 3 total:** 32 pts. This sprint is intentionally lighter — buffer for any Sprint 2 carryover, stabilization time, and the smoke test gate. Do not ship without I-07 passing in full.

---

## Full Issue List (Linear-Ready Format)

> LINEAR_API_KEY is not set. The following issues are formatted for manual import into Linear. Create a project named "FairSplit", create epics matching the epic names below, and import issues into the matching epic.

---

### Epic: Foundation

---

**[F-01] [INFRA] Implement: Docker Compose stack with all services**

**Labels:** infra, chore, urgent  
**Estimate:** 5 points  
**Depends on:** nothing

**Context:** This is the foundation of the entire project. Every other engineer is blocked until this is done. The stack must start with a single `docker compose up` and have zero external dependencies — no cloud accounts, no API keys, no manual configuration.

**Requirements:**
- Services: `db` (postgres:16-alpine, port 5432), `migrate` (Alembic ephemeral, exits after upgrade head), `backend` (FastAPI, port 8000), `frontend` (Next.js, port 3000), `prometheus` (port 9090), `grafana` (port 3001)
- `migrate` service depends on `db` being healthy (health check: `pg_isready`)
- `backend` service depends on `migrate` exiting successfully
- Backend env vars: DATABASE_URL, SECRET_KEY, CORS_ORIGINS, ENVIRONMENT
- Frontend env vars: NEXT_PUBLIC_API_URL, NEXT_PUBLIC_SHOW_DEV_PANEL (Dockerfile ARG)
- Named volume `postgres_data` for DB persistence across restarts
- `.env.example` file documents every required variable with safe defaults for local dev

**Acceptance Criteria:**
- Given a developer clones the repo and runs `docker compose up`, then all 6 services start without error within 60 seconds
- Given the stack is running, then `curl http://localhost:8000/health` returns 200 and `curl http://localhost:3000` returns the Next.js landing page HTML
- Given the developer runs `docker compose down -v && docker compose up`, then migrations re-run and the DB is clean — no residual state
- Given the `backend` service environment is missing SECRET_KEY, then the backend container exits with a clear error (not a silent failure)

**Definition of Done:** All six services start; health endpoints return 200; Grafana UI loads at :3001; no other engineer needs to configure anything to run the stack.

---

**[F-02] [DB] Implement: Alembic async configuration and all entity migrations**

**Labels:** db, chore, urgent  
**Estimate:** 5 points  
**Depends on:** F-01

**Context:** The database schema is the contract that every service layer depends on. It must be created in the correct dependency order and match the DDL in `technical-spec.md §3` exactly. Alembic must use the async engine pattern — do not use the sync pattern, which will deadlock with asyncpg.

**Requirements:**
- Alembic configured with `async_engine_from_config`, `NullPool`, and `connection.run_sync(do_run_migrations)` in `env.py`
- DATABASE_URL read from environment variable (not hardcoded in alembic.ini)
- All models imported in `env.py` before `Base.metadata` is accessed
- Migration order: (1) groups, (2) members, (3) expenses, (4) expense_splits, (5) settlements, (6) idempotency_keys, (7) set_updated_at() trigger function, (8) trigger applied to all 5 entity tables
- All columns, constraints, and check constraints match the DDL exactly:
  - `expenses.amount_cents`: INTEGER, NOT NULL, CHECK > 0
  - `expense_splits.amount_cents`: INTEGER, NOT NULL, CHECK >= 0
  - `expense_splits.percentage`: NUMERIC(6,3), nullable
  - Soft delete columns: `expenses.deleted_at` and `settlements.deleted_at` are TIMESTAMPTZ nullable
- All 5 partial and unique indexes as specified in `technical-spec.md §3`

**Acceptance Criteria:**
- Given `alembic upgrade head` runs on an empty database, then all 6 tables exist with correct columns, constraints, and indexes
- Given `alembic upgrade head` is run twice, then the second run is a no-op (no error, no duplicate objects)
- Given `alembic downgrade base`, then all tables and indexes are removed cleanly
- Given a schema diff (`alembic check`), then there are zero pending changes

**Definition of Done:** Migrations run to completion in the Docker `migrate` service; `alembic check` reports no drift; all indexes verified with `\d tablename` in psql.

---

**[F-03] [BE] Implement: FastAPI application skeleton**

**Labels:** backend, chore, urgent  
**Estimate:** 3 points  
**Depends on:** F-01

**Context:** The FastAPI skeleton establishes the patterns every subsequent router must follow. Getting this right on Day 1 prevents pattern drift across the codebase. Every pattern here is mandatory for all routers that come later.

**Requirements:**
- `src/backend/core/config.py`: pydantic-settings `Settings` class; all env vars typed; raises at startup if required vars are missing
- `src/backend/core/db.py`: async SQLAlchemy engine + `AsyncSession` factory; `get_session` dependency
- `src/backend/core/security.py`: `create_member_token(member_id, group_id, is_admin)` and `decode_member_token(token)` using PyJWT 2.10.x HS256
- `src/backend/main.py`: mounts CORS middleware (allow origin from CORS_ORIGINS env), structured JSON logging middleware (request_id, method, path, status, duration_ms), includes all routers
- `GET /health` endpoint: returns `{"status": "ok", "db": "ok"}` after verifying DB connectivity; returns 503 if DB is unreachable
- Structured JSON logging: every request logged with timestamp, level, request_id (UUID, generated per request), method, path, status, duration_ms, group_id (if in request context), member_id (if authenticated)
- Every exception logged with `exc_info=True`

**Acceptance Criteria:**
- Given the backend starts, then `GET /health` returns `{"status": "ok", "db": "ok"}` with status 200
- Given a request is made to any endpoint, then a structured JSON log line appears in stdout with all required fields
- Given a 500 error occurs, then the exception traceback appears in the log with `exc_info=True`
- Given SECRET_KEY is not set, then the app refuses to start with a clear error message

**Definition of Done:** `/health` returns 200; log output is valid JSON; settings validation works.

---

**[F-04] [BE] Implement: Auth middleware (cookie-first, Bearer fallback)**

**Labels:** backend, chore, urgent  
**Estimate:** 3 points  
**Depends on:** F-03

**Context:** The session model for FairSplit is non-trivial. Members are anonymous — no email, no password. The JWT in an httpOnly cookie is the sole source of identity. The middleware must be implemented exactly as specified, because the Safari ITP fallback logic depends on the cookie being the primary store, not localStorage.

**Requirements:**
- `src/backend/middleware/auth_middleware.py`: reads `fairsplit_member_token` cookie first; falls back to `Authorization: Bearer` header
- Raises HTTP 401 `{"detail": "NO_SESSION"}` if neither is present
- Raises HTTP 401 `{"detail": "SESSION_EXPIRED"}` on expired JWT
- Raises HTTP 401 `{"detail": "SESSION_INVALID"}` on malformed JWT
- Injects `current_member: MemberContext` (member_id, group_id, is_admin) into request state
- Public routes that bypass auth: `GET /health`, `POST /api/v1/groups`, `POST /api/v1/join/{invite_token}`
- Rolling cookie refresh: on every authenticated request, reset the cookie expiry to 30 days from now (extend session on activity)

**Acceptance Criteria:**
- Given a request with a valid httpOnly cookie, then the request proceeds and `request.state.current_member` is populated
- Given a request with no cookie but a valid Bearer token, then the request proceeds identically
- Given a request to a protected endpoint with no token at all, then the response is 401 with `{"detail": "NO_SESSION"}`
- Given a request with an expired token, then the response is 401 with `{"detail": "SESSION_EXPIRED"}`
- Given a valid request, then the response includes a refreshed `Set-Cookie` header resetting the 30-day expiry

**Definition of Done:** Unit tests covering all four scenarios above pass.

---

**[F-05] [FE] Implement: Next.js 16 application skeleton**

**Labels:** frontend, chore, urgent  
**Estimate:** 5 points  
**Depends on:** F-01

**Context:** The frontend skeleton establishes every shared utility that downstream components depend on. The API client, session management, and currency formatting must be correct before any feature UI is built on top of them.

**Requirements:**
- `src/frontend/lib/api-client.ts`: typed fetch wrapper — base URL from `NEXT_PUBLIC_API_URL`, `credentials: "include"` on every request, throws on non-2xx with the response body parsed, handles the two response envelope shapes (singleton vs. paginated list per CTO handoff)
- `src/frontend/lib/session.ts`: `getToken(groupId)` reads from localStorage first; if missing, calls `GET /api/v1/groups/{id}/members/me` using cookie; never redirects to join page without attempting the recovery call first
- `src/frontend/lib/format.ts`: `formatCents(cents: number, currency?: string): string` (e.g., 4200 → "$42.00"); `tabular-nums` font feature enabled via CSS class
- Tailwind 4 config with design tokens: `brand-700` = #047857, `brand-500` = #10b981, all tokens from `design-spec.md §2`
- shadcn/ui installed and configured; Button (with brand variant), Input, Dialog, Toast (Sonner), Badge primitives available
- `NEXT_PUBLIC_SHOW_DEV_PANEL` Dockerfile ARG wired through docker-compose to the Next.js container

**Acceptance Criteria:**
- Given the frontend container starts, then the landing page renders at `http://localhost:3000` with correct brand color on primary button
- Given `formatCents(4200)` is called, then it returns `"$42.00"`
- Given `formatCents(4201)` is called, then it returns `"$42.01"`
- Given `getToken(groupId)` is called and localStorage is empty, then it makes a GET /members/me request before returning null

**Definition of Done:** Landing page renders; all lib functions are unit-testable and typed with no TypeScript errors.

---

**[F-06] [FE] Implement: Route structure and shared layout components**

**Labels:** frontend, chore, urgent  
**Estimate:** 3 points  
**Depends on:** F-05

**Context:** All page routes must exist as shells before the team can work on feature components in parallel. The bottom navigation is a shared component that every group page uses — it must be built once and reused.

**Requirements:**
- App Router pages as shells (no content yet, just the route + layout mounting):
  - `app/page.tsx` — home
  - `app/groups/[groupId]/page.tsx` — dashboard
  - `app/groups/[groupId]/expenses/[expenseId]/page.tsx` — expense detail
  - `app/groups/[groupId]/settle-up/page.tsx` — settle-up plan
  - `app/join/[inviteToken]/page.tsx` — join group
- `components/ui/bottom-nav.tsx`: fixed bottom navigation, `position: fixed; bottom: 0`, `padding-bottom: env(safe-area-inset-bottom)`, 64px height, 44px touch targets
- Loading skeletons for balance card and expense list (used on initial SWR load)
- Error boundary component (catches render errors, shows a non-error-like fallback)
- Empty state component (receives title + body + optional CTA — no error language)

**Acceptance Criteria:**
- Given any page route is navigated to, then the shell renders without a JavaScript error
- Given the bottom navigation is rendered on an iPhone viewport (375px), then all tap targets are at least 44×44px and the nav does not overlap page content (safe area is respected)
- Given a loading state is triggered, then a skeleton appears — not a spinner or blank screen

**Definition of Done:** All routes return non-error shells; bottom nav renders correctly at 320px and 375px.

---

**[F-07] [BE] Implement: Idempotency service**

**Labels:** backend, chore, high  
**Estimate:** 3 points  
**Depends on:** F-03, F-02

**Context:** The group creation and expense creation flows are especially vulnerable to double-submission (network retry, double-tap on mobile). The idempotency service prevents duplicate writes transparently. It must be implemented before any mutation endpoints are built.

**Requirements:**
- `src/backend/services/idempotency_service.py`
- `check_and_store(db, key, response_body, status_code, expires_in=86400)`: checks `idempotency_keys` table; if key exists and not expired, returns the stored response; if key does not exist, caller processes the mutation, then this function inserts the key + response in the same transaction
- Key is the value of the `X-Idempotency-Key` request header (client-generated UUID)
- If the header is absent on a mutation endpoint, the request is processed normally (idempotency is optional for clients that don't send the header)
- Stored `response_body` is JSONB; `status_code` is INTEGER

**Acceptance Criteria:**
- Given a POST /groups request with idempotency key "abc-123", then the group is created and the key is stored
- Given the same POST /groups request with key "abc-123" is sent again within 24 hours, then the original response is returned and no second group is created
- Given an idempotency key is older than 24 hours, then it is treated as absent (new request processed)
- Given a request is made without the X-Idempotency-Key header, then the request is processed normally (no error)

**Definition of Done:** Unit tests for duplicate-submission prevention pass.

---

**[F-08] [INFRA] Implement: Prometheus + Grafana auto-provisioning**

**Labels:** infra, chore, medium  
**Estimate:** 2 points  
**Depends on:** F-01

**Context:** Observability must be available from Day 1 of development, not bolted on at the end. Grafana must auto-provision its datasource and dashboard from config files — no manual Grafana setup after `docker compose up`.

**Requirements:**
- `src/infra/prometheus/prometheus.yml`: scrapes `http://backend:8000/metrics` every 15s
- `src/infra/grafana/provisioning/datasources/prometheus.yml`: Prometheus datasource auto-provisioned
- `src/infra/grafana/provisioning/dashboards/fairsplit.json`: dashboard with panels for request rate, p95 latency (per endpoint), error rate (4xx/5xx), and DB connection pool saturation
- Grafana default credentials: admin/admin (documented in README)
- Grafana volume mounts the provisioning directory; no Grafana state is committed to the repo

**Acceptance Criteria:**
- Given `docker compose up`, then Grafana UI loads at `:3001` with no manual configuration required
- Given the backend has received at least one request, then the Grafana dashboard shows non-zero request rate
- Given the developer restarts the stack, then Grafana still shows the dashboard (provisioning is persistent across restarts)

**Definition of Done:** Grafana dashboard loads automatically after `docker compose up`; metrics are visible.

---

### Epic: Group Creation and Anonymous Auth

---

**[G-01] [BE] Implement: POST /api/v1/groups — group creation with auto-join and JWT issuance**

**Labels:** backend, feature, urgent  
**Estimate:** 3 points  
**Depends on:** F-04, F-07

**Context:** Group creation is the entry point for every FairSplit user. The creator is immediately and automatically a group member (admin role). The endpoint must issue a JWT, set the httpOnly cookie, and return the group, member, and token in a single response. This is one of two endpoints that create a session — the patterns set here must be replicated in POST /join.

**Requirements:**
- Request body: `{group_name: string (1–80 chars), description: string (0–200 chars, optional), your_name: string (1–40 chars), currency: string (default "USD")}`
- Creates: one `groups` row, one `members` row (is_admin=true), sets `groups.invite_token` (cryptographically random URL-safe token, 32 chars)
- Issues JWT: `{sub: member_id, group_id: group_id, is_admin: true, iat: now, exp: now+30d}`
- Response body: `{group: GroupSchema, member: MemberSchema, token: str}` with status 201
- Sets `Set-Cookie: fairsplit_member_token=<token>; HttpOnly; SameSite=Lax; Path=/; Max-Age=2592000`
- Idempotency: checks `X-Idempotency-Key` header before creating; returns stored response if key was seen within 24h
- Validation errors return 422 with field-level detail

**Acceptance Criteria:**
- Given a valid POST /groups request, then the response is 201 with group, member, and token fields
- Given the response is received, then the `Set-Cookie` header is present with `HttpOnly` and `SameSite=Lax` flags
- Given the same request is sent twice with the same idempotency key, then only one group is created
- Given group_name is empty, then the response is 422 with a field-level error on group_name

**Definition of Done:** Integration test covering creation, cookie presence, and idempotency passes.

---

**[G-02] [BE] Implement: POST /api/v1/join/{invite_token} — group join with session issuance**

**Labels:** backend, feature, urgent  
**Estimate:** 3 points  
**Depends on:** F-04, F-07

**Context:** The join flow is the primary mechanism for viral growth. Every new group member arrives via an invite link. The endpoint validates the invite token, creates the member, issues a JWT, and sets the cookie — same session model as group creation. Display name deduplication (append "(2)" suffix) must be handled server-side.

**Requirements:**
- Route param: `invite_token` — looked up in `groups` table via `idx_groups_invite_token`
- Request body: `{display_name: string (1–40 chars)}`
- Returns 404 if invite_token is not found (message: "This link is no longer valid. Ask the group admin for a new one.")
- Creates one `members` row (is_admin=false); if display_name already exists in the group, appends " (2)", " (3)", etc.
- Issues JWT: `{sub: member_id, group_id: group_id, is_admin: false, iat: now, exp: now+30d}`
- Response body: `{group: GroupSchema, member: MemberSchema, token: str}` with status 201
- Sets `Set-Cookie: fairsplit_member_token=<token>; HttpOnly; SameSite=Lax; Path=/; Max-Age=2592000`
- Idempotency: same pattern as G-01

**Acceptance Criteria:**
- Given a valid invite_token and display name "Daniel", then the response is 201 with the member record and session cookie
- Given the display name "Daniel" already exists in the group, then the new member is created as "Daniel (2)"
- Given an invalid or missing invite_token, then the response is 404 with the standard error message
- Given the same request is sent twice with the same idempotency key, then only one member is created

**Definition of Done:** Integration test covering join, deduplication, invalid token, and idempotency passes.

---

**[G-03] [BE] Implement: GET /api/v1/groups/{id} and GET /api/v1/groups/{id}/members**

**Labels:** backend, feature, high  
**Estimate:** 2 points  
**Depends on:** G-01

**Context:** These are the two reads that populate the group dashboard. They are called on every page load and must be fast. The member list is sorted by net balance descending (largest creditor first) once expenses exist; alphabetically when all balances are zero.

**Requirements:**
- `GET /groups/{id}`: requires valid session token with matching group_id; returns full GroupSchema
- `GET /groups/{id}/members`: returns paginated member list with current net balance per member; sorting as described; empty list returns `{data: [], total: 0, page: 1, per_page: 50}`
- Group ID in JWT must match the requested group ID — members cannot access other groups

**Acceptance Criteria:**
- Given a valid session for group A, then GET /groups/A returns the group data
- Given a valid session for group A, then GET /groups/B returns 403
- Given the group has no expenses, then the member list is sorted alphabetically and each balance is 0

**Definition of Done:** Returns correct data; cross-group access is blocked.

---

**[G-04] [BE] Implement: POST /api/v1/groups/{id}/invite — rotate invite token**

**Labels:** backend, feature, medium  
**Estimate:** 2 points  
**Depends on:** G-01

**Context:** The invite link must be rotatable so the group admin can revoke access for new members (e.g., after an unwanted join). This endpoint generates a new cryptographically random invite token, invalidating the previous link.

**Requirements:**
- Requires admin session (is_admin=true in JWT); returns 403 if not admin
- Generates new 32-char URL-safe token; updates `groups.invite_token`
- Returns `{invite_url: string}` with the new full invite URL (using base URL from config)

**Acceptance Criteria:**
- Given an admin member requests a new invite link, then the response contains a new URL with a different token
- Given a non-admin member requests a new invite link, then the response is 403
- Given the old invite link is used after rotation, then it returns 404

**Definition of Done:** Token rotation works; old token is rejected; 403 for non-admin.

---

**[G-05] [BE] Implement: GET /api/v1/groups/{id}/members/me — session recovery**

**Labels:** backend, feature, high  
**Estimate:** 1 point  
**Depends on:** G-02

**Context:** This endpoint exists specifically to support the Safari ITP session recovery flow. When a user returns to the app after localStorage has been cleared, the frontend calls this endpoint (which uses the httpOnly cookie) to recover the JWT and restore it to localStorage. Without this endpoint, returning iOS Safari users lose their session.

**Requirements:**
- Requires valid httpOnly cookie (or Bearer token); returns the current member's data and a fresh JWT
- Returns `{member: MemberSchema, token: str}` — the frontend stores the token back into localStorage
- Also refreshes the cookie expiry (30 days rolling)

**Acceptance Criteria:**
- Given a valid cookie session, then GET /members/me returns the member data and a fresh token
- Given no cookie or token, then the response is 401

**Definition of Done:** Session recovery works without localStorage.

---

**[G-06] [FE] Implement: Home page and create-group form**

**Labels:** frontend, feature, urgent  
**Estimate:** 3 points  
**Depends on:** G-01, F-06

**Context:** The home page is the first thing a new user sees. It must immediately communicate the product's value and make group creation the obvious next step. The form must be simple — group name, optional description, and the creator's display name. Zero friction.

**Requirements:**
- `app/page.tsx`: "Create a Group" CTA as the primary action; secondary link "Got an invite link? Join here"
- Create group form (can be a modal or inline): group name (required, max 80 chars), description (optional, max 200 chars), your display name (required, max 40 chars)
- On submit: POST /api/v1/groups with X-Idempotency-Key; store token in localStorage as `fairsplit_token_{groupId}`; redirect to `/groups/{groupId}`
- Inline validation: "Group name is required" on empty submit; character counter at 80-char limit for group name
- Input `type="text"` for all fields; no `type="number"` anywhere
- Primary button uses brand-700 (#047857) background with white text

**Acceptance Criteria:**
- Given a user fills in the form and submits, then they are redirected to the group dashboard with the group name in the page title
- Given the group name is left empty and submit is clicked, then an inline validation error appears without a page navigation
- Given the network is slow (simulate 500ms delay), then the submit button shows a loading state and cannot be double-clicked

**Definition of Done:** Form submits, session is stored, redirect to dashboard occurs.

---

**[G-07] [FE] Implement: Join group page**

**Labels:** frontend, feature, urgent  
**Estimate:** 3 points  
**Depends on:** G-02, F-06

**Context:** The join flow is the most critical flow in the product. Every new member arrives here. It must be fast, frictionless, and complete in under 60 seconds from clicking the invite link. The first screen must never ask for email, password, or any account information.

**Requirements:**
- `app/join/[inviteToken]/page.tsx`: shows group name (from invite token lookup — the join API returns the group), display name input (required, max 40 chars), "Join Group" button
- On submit: POST /api/v1/join/{inviteToken}; store token in localStorage as `fairsplit_token_{groupId}`; redirect to `/groups/{groupId}`
- If invite token returns 404: shows the error message "This link is no longer valid. Ask the group admin for a new one." — not an error page, an inline message
- Input is auto-focused on mount (immediately ready for typing on desktop; soft keyboard opens on mobile)
- Idempotency key generated with `crypto.randomUUID()` on mount

**Acceptance Criteria:**
- Given a user opens a valid invite link and types their name, then tapping "Join Group" redirects them to the dashboard in under 2 seconds (network permitting)
- Given the invite token is invalid, then the inline error message appears — no full-page error
- Given the user is already a member (returning visitor with valid cookie), then they are redirected to the dashboard without seeing the join form

**Definition of Done:** Join flow completes end-to-end; session is stored; invalid link shows inline error.

---

**[G-08] [FE] Implement: Session recovery logic**

**Labels:** frontend, feature, urgent  
**Estimate:** 2 points  
**Depends on:** G-05

**Context:** This is the fix for the Safari ITP risk identified as the product's top risk in the PM handoff. If localStorage is cleared (iOS Safari ITP, 7-day inactivity), the app must not redirect the user to the join page. It must first attempt to recover the session via the httpOnly cookie by calling GET /members/me. Only if that fails is the user considered truly unauthenticated.

**Requirements:**
- `lib/session.ts`: `getSession(groupId)` attempts localStorage read first; if missing, calls GET /api/v1/groups/{groupId}/members/me (which sends the cookie via `credentials: "include"`); if that returns a token, stores it in localStorage and returns the session; only returns null if both fail
- All group pages call `getSession()` on mount before deciding whether to show content or redirect
- Never call `router.push("/join/...")` without first attempting the /members/me recovery call

**Acceptance Criteria:**
- Given localStorage is cleared but the httpOnly cookie is present, then the user sees the group dashboard (not the join page)
- Given both localStorage and the cookie are missing, then the user is redirected to the join page
- Given the /members/me call fails with a network error, then the user is redirected to the join page (graceful degradation)

**Definition of Done:** Session recovery works without localStorage; manual test in Safari with localStorage cleared.

---

**[G-09] [FE] Implement: Group dashboard shell — member list, balance placeholders, invite link**

**Labels:** frontend, feature, high  
**Estimate:** 3 points  
**Depends on:** G-03, G-04

**Context:** The group dashboard is the product's main screen. Members spend most of their time here. This issue builds the shell — member list, balance card area (with skeleton, populated in E-10), expense list area (with skeleton, populated in E-08), and the invite link share flow.

**Requirements:**
- `app/groups/[groupId]/page.tsx`: group name in header, member list (names + balance badges using green/red/gray convention), invite link section with "Invite Members" button
- "Invite Members": calls POST /api/v1/groups/{id}/invite to get the current link (or reads from group response); displays link with "Copy Link" button; if Web Share API is available (`navigator.share`), shows "Share" button as secondary option
- Toast on copy: "Link copied to clipboard"
- Balance card area: skeleton placeholder (replaced by E-10)
- Expense list area: skeleton placeholder (replaced by E-08)
- Bottom navigation with tabs: Expenses, Balances, Settle Up

**Acceptance Criteria:**
- Given a group with 3 members, then all 3 member names appear in the list
- Given "Copy Link" is tapped, then a toast "Link copied to clipboard" appears
- Given `navigator.share` is available, then a "Share" button appears alongside "Copy Link"

**Definition of Done:** Dashboard shell renders with live member data; invite link copy works.

---

### Epic: Expense Logging and Balance View

---

**[E-01] [BE] Implement: POST /api/v1/groups/{id}/expenses — expense creation**

**Labels:** backend, feature, urgent  
**Estimate:** 5 points  
**Depends on:** G-01, F-07

**Context:** Expense creation is the highest-frequency action in the product. It must handle three split modes (equal, custom amounts, custom percentages), validate that splits sum to the total, convert decimal string input to integer cents, and store everything correctly. The rounding rule (1-cent remainder to first creditor alphabetically) must be implemented here.

**Requirements:**
- Request body: `{description: string, amount_cents: int, currency: string, payer_member_id: uuid, split_type: "equal"|"custom_amount"|"custom_percentage", splits: [{member_id: uuid, amount_cents?: int, percentage?: float}], idempotency_key?: string}`
- Validates: amount_cents > 0; payer_member_id is a member of the group; all split member_ids are members of the group; splits sum to amount_cents (with 1-cent tolerance for rounding); percentage splits sum to 100.0 (±0.01%)
- For `equal` split: divides amount_cents evenly; any 1-cent remainder added to first member alphabetically by display_name
- For `custom_percentage`: computes amount_cents per member from percentage; any 1-cent remainder added to first member alphabetically
- Creates one `expenses` row and N `expense_splits` rows in a single transaction
- Idempotency: checks X-Idempotency-Key before creating
- Returns 201 with ExpenseSchema (including splits)

**Acceptance Criteria:**
- Given a 3-member equal split of $10.00 (1000 cents), then the splits are [334, 333, 333] cents with the remainder cent assigned to the first alphabetical member
- Given custom percentages that sum to 100%, then splits are computed correctly and sum to amount_cents
- Given splits do not sum to amount_cents, then the response is 422 with a clear error
- Given payer_member_id is not in the group, then the response is 422

**Definition of Done:** All three split modes work correctly; rounding is correct; idempotency prevents duplicates.

---

**[E-02] [BE] Implement: GET /api/v1/groups/{id}/expenses (list) and GET /api/v1/groups/{id}/expenses/{id} (detail)**

**Labels:** backend, feature, high  
**Estimate:** 3 points  
**Depends on:** E-01

**Context:** The expense list is paginated — groups with 200 expenses must not return all rows in one response. The detail endpoint returns the full split breakdown per member, which is the data needed for the expense detail page.

**Requirements:**
- List: excludes soft-deleted expenses (`deleted_at IS NULL`); ordered by `created_at DESC`; paginated (default per_page=20, max=100); returns `{data: ExpenseSchema[], total: int, page: int, per_page: int}`
- Detail: returns ExpenseSchema with nested `splits: [{member_id, display_name, amount_cents}]`
- Both endpoints require a valid session for the correct group

**Acceptance Criteria:**
- Given 25 expenses exist and page=1 is requested, then 20 expenses are returned with total=25
- Given an expense detail is requested, then the response includes the per-person split breakdown
- Given a soft-deleted expense ID is requested in the detail endpoint, then the response is 404

**Definition of Done:** Pagination works; soft-deleted expenses are excluded; splits appear in detail.

---

**[E-03] [BE] Implement: PATCH /api/v1/groups/{id}/expenses/{id} — expense edit**

**Labels:** backend, feature, high  
**Estimate:** 3 points  
**Depends on:** E-01

**Context:** Edit is allowed for the original expense logger or the group admin. The edit replaces the existing splits — the old expense_splits rows are deleted and new ones are created in the same transaction. Balances recalculate automatically on the next balance query since they are computed at read time.

**Requirements:**
- Authorization: requester must be original logger (logged_by_member_id) or is_admin=true
- Returns 403 if neither condition is met
- Request body: same schema as POST (any field can be omitted to keep existing value)
- Replaces all existing expense_splits for this expense in the same transaction
- Returns 200 with updated ExpenseSchema

**Acceptance Criteria:**
- Given the expense logger edits an expense amount, then the response reflects the new amount and splits
- Given a non-admin, non-logger member sends a PATCH, then the response is 403
- Given the edit is made, then immediately calling GET /balances returns updated balances

**Definition of Done:** Edit with authorization enforcement and balance recalculation works.

---

**[E-04] [BE] Implement: DELETE /api/v1/groups/{id}/expenses/{id} — soft delete**

**Labels:** backend, feature, high  
**Estimate:** 2 points  
**Depends on:** E-01

**Context:** Deletion sets `deleted_at` to the current timestamp. The expense is excluded from all subsequent queries by the partial index on `deleted_at IS NULL`. This is reversible if needed (no data is destroyed), but the UI treats it as permanent (no undo button in MVP).

**Requirements:**
- Authorization: same as PATCH (original logger or admin)
- Sets `expenses.deleted_at = NOW()` — does not DELETE the row
- Returns 204 No Content on success
- Returns 403 if unauthorized; 404 if expense not found or already deleted

**Acceptance Criteria:**
- Given a valid DELETE request, then the expense no longer appears in GET /expenses list
- Given the same expense ID is requested after deletion, then GET /expenses/{id} returns 404
- Given a non-authorized member sends DELETE, then the response is 403

**Definition of Done:** Soft delete works; partial index correctly excludes deleted rows.

---

**[E-05] [BE] Implement: GET /api/v1/groups/{id}/balances — net balance computation**

**Labels:** backend, feature, urgent  
**Estimate:** 5 points  
**Depends on:** E-01

**Context:** This is the most performance-critical endpoint in the system. It is polled every 10 seconds by all active clients on the dashboard. The CTE query from `technical-spec.md §3 Query 1` computes net balances by summing credits (expenses paid) minus debits (splits owed) minus settlements (recorded payments). Correctness here flows directly into the settle-up algorithm.

**Requirements:**
- Uses the CTE query from technical-spec.md §3: sums `(amount_cents WHERE payer_member_id = m.id) - (split amount_cents for m.id) - (settlements received) + (settlements paid)` per member
- Only includes non-deleted expenses (via partial index)
- Excludes soft-deleted settlements
- Returns `{data: [{member_id, display_name, balance_cents: int}], computed_at: datetime}` where positive balance_cents = creditor (owed money), negative = debtor (owes money)
- Must complete in < 200ms p95 (verified by integration test with 200 expenses in the group)
- Returns an empty list (not 404) if the group has no members yet

**Acceptance Criteria:**
- Given member A paid $100 and member B paid $0 in an equal 2-member split, then balance for A = +5000 cents and balance for B = -5000 cents
- Given a settlement of $50 from B to A is recorded, then balance for A = 0 and balance for B = 0
- Given the group has no expenses, then the response is `{data: [], computed_at: ...}` with status 200 (not 404)
- Given the query runs against 200 expenses with 5 members, then it completes in under 200ms

**Definition of Done:** All three scenarios above produce correct results; performance test passes.

---

**[E-06] [FE] Implement: Add expense form — equal split mode**

**Labels:** frontend, feature, urgent  
**Estimate:** 3 points  
**Depends on:** E-01, G-09

**Context:** The expense form is the highest-frequency UI in the product. It must be fast to fill out and impossible to accidentally double-submit. The equal split mode is the default and must work before the custom split modes (E-07) are added.

**Requirements:**
- `components/expense-form/ExpenseForm.tsx`: description (text input), amount (text input with `inputMode="decimal"`, no `type="number"`), payer dropdown (defaults to current member), split-among multi-select (defaults to all members), split type selector (equal selected by default)
- Per-person share preview: shown in real time below the amount field as the user types (e.g., "4 people — $12.50 each")
- Submit: POST /api/v1/groups/{id}/expenses with X-Idempotency-Key header; on success, invalidate SWR expense and balance caches; redirect/dismiss form
- Loading state on submit button (disable re-click during inflight request)
- All form fields have visible labels (not placeholder-only labels)

**Acceptance Criteria:**
- Given a user enters $50.00 and selects 4 members for equal split, then the preview shows "$12.50 each"
- Given the user taps Save, then the expense appears at the top of the expense list without a page reload
- Given the network is slow, then the submit button is disabled and shows a loading indicator
- Given the user taps Save twice rapidly, then only one expense is created (idempotency key prevents duplicate)

**Definition of Done:** Equal split expense saves correctly; double-submission is prevented.

---

**[E-07] [FE] Implement: Custom amount and custom percentage split modes**

**Labels:** frontend, feature, high  
**Estimate:** 3 points  
**Depends on:** E-06

**Context:** These are the two non-default split modes. Custom amounts are used when the group wants to specify exactly what each person owes. Custom percentages are used when splitting by share (e.g., 40%/30%/30%). Both require real-time validation — the values must sum to the total before the form can be submitted.

**Requirements:**
- "Custom amounts" mode: shows an amount input per selected member; running total shown; validation error if parts do not sum to total (shown as "Total is $X but splits add up to $Y — please adjust")
- "Custom percentages" mode: shows a percentage input per selected member; running total shown; validation error if percentages do not sum to 100%
- Switching between split types resets the per-member fields to the equal-split defaults
- Rounding preview: in equal split, show how the 1-cent remainder is assigned ("$33.34 + $33.33 + $33.33")
- Both modes use `inputMode="decimal"` on their inputs

**Acceptance Criteria:**
- Given "Custom amounts" is selected and splits do not sum to the total, then the Save button is disabled and a validation message is visible
- Given "Custom percentages" is selected and percentages sum to 100%, then Save is enabled
- Given the split type is changed, then per-member inputs reset to equal-split defaults

**Definition of Done:** Both custom split modes validate and submit correctly.

---

**[E-08] [FE] Implement: Expense list on dashboard and empty state**

**Labels:** frontend, feature, high  
**Estimate:** 3 points  
**Depends on:** E-02, G-09

**Context:** The expense list is the primary information display on the dashboard. It must handle the empty state gracefully (new group with no expenses) and show enough information on each card to make the detail tap feel optional, not required.

**Requirements:**
- Expense card: description, amount (formatted from cents), payer display name, date (relative: "2 days ago"), number of people in split
- Empty state: "No expenses yet. Tap 'Add Expense' to log your first one." — positive, instructional, not error-like
- Infinite scroll or "Load more" button at 20 items; uses the pagination API
- `useExpenses` SWR hook with `refreshInterval: 10000`
- Tap expense card → navigate to `/groups/{groupId}/expenses/{expenseId}`

**Acceptance Criteria:**
- Given the group has no expenses, then the empty state message is shown (not an error)
- Given the group has 25 expenses, then 20 are shown initially with a "Load more" button that reveals the remaining 5
- Given a new expense is saved, then it appears at the top of the list within 10 seconds (next poll cycle)

**Definition of Done:** Empty state shown; pagination works; new expenses appear.

---

**[E-09] [FE] Implement: Expense detail page — breakdown, edit, delete**

**Labels:** frontend, feature, high  
**Estimate:** 3 points  
**Depends on:** E-03, E-04, E-08

**Context:** The expense detail page shows the full split breakdown and allows editing or deletion. Edit and delete are permission-gated — only the original logger or an admin sees those actions. Deletion requires a confirmation dialog.

**Requirements:**
- `app/groups/[groupId]/expenses/[expenseId]/page.tsx`: shows description, total amount, payer, date, split breakdown table (member name + amount)
- "Edit" button: visible only to original logger or admin; opens the expense form pre-filled with existing values (PATCH on submit)
- "Delete" button: visible only to original logger or admin; opens a `role="dialog"` confirmation: "Delete this expense? This cannot be undone." — Cancel + Confirm actions
- On successful delete: navigate back to dashboard; expense no longer in list
- On successful edit: expense detail reflects updated values; balance card on dashboard updates within 10s

**Acceptance Criteria:**
- Given the logged-in member is not the original logger and not an admin, then neither Edit nor Delete buttons appear
- Given the Delete button is tapped, then a confirmation dialog appears before any deletion occurs
- Given the delete is confirmed, then the user is navigated back to the dashboard and the expense is gone

**Definition of Done:** Permission enforcement works; delete confirmation works; edit pre-fills correctly.

---

**[E-10] [FE] Implement: Balance view — personal hero card and all-members list**

**Labels:** frontend, feature, urgent  
**Estimate:** 3 points  
**Depends on:** E-05, G-09

**Context:** The balance view is the second most important screen after the settle-up plan. The personal hero card (large, prominent balance display) is seen every time a member opens the dashboard. The color convention (green = owed, red = owes, gray = settled) must be absolutely consistent.

**Requirements:**
- Personal hero card (top of dashboard): large amount display in green (positive balance) or red (negative balance) or gray ($0); label text: "You are owed $X", "You owe $X", or "You're all settled up"
- "See all balances" section: member list with name + balance badge; sorted by balance descending (largest creditor first); green badge for positive, red for negative, gray for zero
- Uses `useBalances` SWR hook with `refreshInterval: 10000`
- Non-member visiting the group URL: shows group name and "Join to see balances" prompt — not a 403 error page
- All monetary amounts use `font-variant-numeric: tabular-nums` via `formatCents()`

**Acceptance Criteria:**
- Given the logged-in member is owed $42.00, then the hero card shows "You are owed $42.00" in green
- Given the logged-in member owes $18.50, then the hero card shows "You owe $18.50" in red
- Given all balances are zero, then the hero card shows "You're all settled up" in gray
- Given 10 seconds pass, then the balance card updates silently (no loading indicator for background refresh)

**Definition of Done:** Hero card displays correctly for all three balance states; polling updates silently.

---

### Epic: Settle-Up (Hero Feature)

---

**[S-01] [BE] Implement: compute_settle_up() — greedy max-heap algorithm**

**Labels:** backend, feature, urgent  
**Estimate:** 5 points  
**Depends on:** E-05

**Context:** This is the most algorithmically complex component in the system and the product's primary differentiator. The implementation is specified in `technical-spec.md §1 C4 Level 4`. It must be implemented exactly as specified and tested exhaustively before the endpoint that calls it (S-02) is considered done. A bug in this algorithm destroys user trust — correctness is zero-tolerance.

**Requirements:**
- `src/backend/services/settle_service.py` implementing `compute_settle_up(net_balances, member_names, currency)` exactly as in the technical-spec code listing
- Input: `dict[UUID, int]` (net balances in cents — positive = creditor, negative = debtor); must sum to zero
- If sum does not equal zero: absorbs the discrepancy into the first creditor alphabetically (same convention as rounding policy)
- Output: `list[Transfer]` ordered by largest transfer amount first
- All arithmetic is integer — no floats
- Returns empty list if all balances are zero

**Acceptance Criteria (all must pass as unit tests):**
- 2-member group: A owes B $100 → 1 transfer: A pays B $100
- 3-member circular: A owes B $10, B owes C $10, C owes A $10 → 0 transfers (all net to 0)
- 3-member net: A=-3000, B=-2000, C=+5000 → 2 transfers (A pays C $30, B pays C $20)
- 4-member: A=-6000, B=-4000, C=+3000, D=+7000 → 3 transfers
- All-settled: all balances = 0 → empty list
- Single-cent remainder: 3-member equal split of $1.00 → balances include a 1-cent correction; total still sums to 0 after correction; algorithm produces valid transfers

**Definition of Done:** All six unit test cases above pass; no test case takes longer than 10ms to run.

---

**[S-10] [BE] Write: Exhaustive unit tests for compute_settle_up()**

**Labels:** backend, chore, urgent  
**Estimate:** 5 points  
**Depends on:** S-01

**Context:** Test coverage for the settle-up algorithm is not optional — it is the primary quality gate for the product's hero feature. These tests must live in `src/backend/tests/test_settle_service.py` and cover every edge case documented in the PRD. They are the permanent regression suite for this algorithm.

**Requirements:**
- All test cases from the PRD Section 6 Feature 5 algorithm spec
- Additional edge cases: single member (1 transfer = none needed), two members (1 transfer), N members all already settled, large group (20 members, 50 random expenses) — verify transfer count <= N-1
- Tests must be deterministic (no random seed required; use fixed UUIDs)
- All tests use integer cents; no float arithmetic
- Tests run in < 1 second total (pure Python, no DB)

**Acceptance Criteria:**
- Running `pytest src/backend/tests/test_settle_service.py` produces zero failures
- Test coverage for `settle_service.py` is >= 95%
- The 20-member stress test completes in < 100ms

**Definition of Done:** `pytest` passes with zero failures; coverage report shows >= 95% for settle_service.py.

---

**[S-02] [BE] Implement: GET /api/v1/groups/{id}/settle-up — settle-up endpoint**

**Labels:** backend, feature, urgent  
**Estimate:** 3 points  
**Depends on:** S-01

**Context:** This endpoint is called when a user taps "Settle Up". It runs the balance CTE query, passes the results to `compute_settle_up()`, and returns the formatted transfer plan including pre-computed clipboard text. Computed at read time — not cached or stored.

**Requirements:**
- Calls `balance_service.compute_nets()` then passes to `settle_service.compute_settle_up()`
- Returns: `{group_name: str, currency: str, all_settled: bool, transfer_count: int, transfers: [{debtor_id, debtor_name, creditor_id, creditor_name, amount_cents}], clipboard_text: str, computed_at: datetime}`
- `clipboard_text` format: `"FairSplit Settle-Up Plan:\n• Daniel pays Maya $42.00\n• Jake pays Tom $18.50"` (uses `format_cents()` for display)
- If all balances are zero: returns `{all_settled: true, transfer_count: 0, transfers: [], ...}`
- Must complete in < 100ms p95

**Acceptance Criteria:**
- Given 3 members with known net balances, then the transfer list matches the expected minimum-transfer output
- Given all balances are zero, then `all_settled=true` and `transfers=[]`
- Given the response, then `clipboard_text` is a correctly formatted human-readable string

**Definition of Done:** Endpoint returns correct data; clipboard_text is formatted correctly.

---

**[S-03] [BE] Implement: POST /api/v1/groups/{id}/settlements — record a settlement**

**Labels:** backend, feature, high  
**Estimate:** 3 points  
**Depends on:** G-01

**Context:** A settlement records that a debt has been paid outside the app (Venmo, Cash App, etc.). It creates a `settlements` row with payer and payee. The balance computation CTE subtracts settled amounts, so the balance view and settle-up plan immediately reflect the payment.

**Requirements:**
- Request body: `{payer_member_id: uuid, payee_member_id: uuid, amount_cents: int, note: string (optional)}`
- Validates: both members are in the group; amount_cents > 0; payer != payee
- Creates one `settlements` row
- Returns 201 with SettlementSchema
- Idempotency: checks X-Idempotency-Key

**Acceptance Criteria:**
- Given a valid settlement is recorded, then GET /balances immediately reflects the reduced amounts
- Given payer == payee, then the response is 422
- Given either member is not in the group, then the response is 422

**Definition of Done:** Settlement creates correctly; balance CTE accounts for it immediately.

---

**[S-04] [BE] Implement: DELETE /api/v1/groups/{id}/settlements/{id} — reverse settlement**

**Labels:** backend, feature, medium  
**Estimate:** 2 points  
**Depends on:** S-03

**Context:** Settlements recorded in error must be reversible. Any group member may delete a settlement (not admin-only — the group trusts all members). Soft delete pattern: sets `deleted_at`.

**Requirements:**
- Any authenticated group member may delete any settlement (no admin restriction)
- Sets `settlements.deleted_at = NOW()` — does not DELETE the row
- Returns 204 No Content
- Returns 404 if settlement not found or already deleted

**Acceptance Criteria:**
- Given a valid DELETE, then the settlement no longer affects GET /balances
- Given the same settlement is deleted twice, then the second request returns 404

**Definition of Done:** Settlement reversal restores original balances.

---

**[S-05] [FE] Implement: Settle-up page — transfer list, copy button, confetti**

**Labels:** frontend, feature, urgent  
**Estimate:** 5 points  
**Depends on:** S-02

**Context:** This is the emotional peak of the product. The design spec describes this as the moment that must feel like magic. The transfer list must be clean and minimal. The "Copy Payment Plan" button is a primary CTA. The all-settled state shows a confetti celebration. Reference `settle-up.html` in the prototype for the visual target.

**Requirements:**
- `app/groups/[groupId]/settle-up/page.tsx`: renders transfer list from GET /settle-up response
- Each transfer row: "[Debtor name] pays [Creditor name] [amount]" — current member's name bolded/highlighted if they appear in a transfer
- "Copy Payment Plan" button: writes `clipboard_text` from API response to clipboard via `navigator.clipboard.writeText()`; fallback: `document.execCommand("copy")` for older browsers; toast "Payment plan copied to clipboard!"
- All-settled state: "Everyone is settled up." message + CSS confetti animation (CSS particles, not a library) — per prototype design
- Tap a transfer row: shows note "This is a suggested transfer only. Use Venmo, Cash App, or bank transfer to complete it." as a bottom sheet or tooltip
- `useSettleUp` SWR hook — does not use `refreshInterval` (the user tapped to see this; they will manually refresh)

**Acceptance Criteria:**
- Given the API returns 2 transfers, then 2 transfer rows are displayed
- Given "Copy Payment Plan" is tapped, then the clipboard contains the formatted text and a toast appears
- Given all balances are zero, then the all-settled state with confetti is shown
- Given the current member is "Maya" and she appears in a transfer, then "Maya" is bolded in that row

**Definition of Done:** Settle-up page renders correctly; copy button works; all-settled state shows confetti.

---

**[S-06] [FE] Implement: Mark-as-Paid flow — settlement confirmation and balance update**

**Labels:** frontend, feature, high  
**Estimate:** 3 points  
**Depends on:** S-03, S-05

**Context:** After the settle-up plan is displayed, members must be able to mark transfers as completed. This creates a settlement record in the backend, which flows back into the balance computation and removes the transfer from the plan.

**Requirements:**
- Each transfer row on the settle-up page has a "Mark as Paid" button (visible to all members, not just the payer)
- Tapping "Mark as Paid" opens a confirmation dialog: "Confirm that [debtor] paid $[amount] to [creditor]?"
- On confirm: POST /api/v1/groups/{id}/settlements; on success, invalidate `useSettleUp` and `useBalances` caches; the transfer disappears from the list
- A settlement entry appears in the expense feed: "[Debtor] settled $[amount] with [Creditor]"
- If a settlement was recorded in error, any member can delete it via the settlement entry in the feed (DELETE /settlements/{id})

**Acceptance Criteria:**
- Given "Mark as Paid" is tapped, then the confirmation dialog appears before any API call is made
- Given the confirmation is submitted, then the transfer is removed from the settle-up list immediately
- Given a settlement appears in the expense feed, then it is visually distinct from a regular expense

**Definition of Done:** Confirmation dialog works; settlement is recorded; transfer disappears from plan.

---

**[S-07] [FE] Implement: SWR hooks — useBalances, useExpenses, useSettleUp**

**Labels:** frontend, feature, high  
**Estimate:** 3 points  
**Depends on:** E-05, S-02

**Context:** These hooks are the data layer for the entire client application. They must be implemented once, shared across all pages, and configured correctly for polling behavior. Background refreshes must not show loading indicators.

**Requirements:**
- `hooks/useBalances.ts`: `useSWR("/api/v1/groups/{id}/balances", {refreshInterval: 10000})` — returns `{balances, isLoading, error}`; `isLoading` is true only on initial load (no data yet), not on background revalidation
- `hooks/useExpenses.ts`: `useSWR("/api/v1/groups/{id}/expenses", {refreshInterval: 10000})` — paginated; supports `page` parameter
- `hooks/useSettleUp.ts`: `useSWR("/api/v1/groups/{id}/settle-up")` — no `refreshInterval` (manual refresh only); invalidated by S-06 on settlement creation
- All hooks pass `credentials: "include"` via the shared api-client.ts fetcher
- All hooks handle 401 (session expired) by calling session recovery before redirecting

**Acceptance Criteria:**
- Given the balance hook is mounted, then it fetches immediately and then every 10 seconds
- Given a background refresh fires, then no loading spinner appears (only the initial skeleton does)
- Given a 401 is returned, then the hook attempts session recovery before redirecting to the join page

**Definition of Done:** All three hooks work; background polling is silent; 401 triggers recovery.

---

**[S-08] [FE] Implement: Expense form draft persistence**

**Labels:** frontend, feature, high  
**Estimate:** 2 points  
**Depends on:** E-06

**Context:** This is a must-have per PM requirements. If a user is halfway through filling out an expense form and accidentally navigates away (or the browser loses focus on mobile), they should not lose their work.

**Requirements:**
- On form field change: write form state to `localStorage["fairsplit_draft_{groupId}"]` using `beforeunload` event and/or `onChange` debounced at 500ms
- On form mount: check for draft in localStorage; if found, pre-fill all form fields silently (no prompt)
- On successful save: clear `localStorage["fairsplit_draft_{groupId}"]`
- On explicit form dismiss (cancel button): clear the draft

**Acceptance Criteria:**
- Given a user fills in description and amount, then navigates to another tab, then returns — the form fields are pre-filled
- Given the expense is saved successfully, then `localStorage["fairsplit_draft_{groupId}"]` is cleared
- Given the form is cancelled, then the draft is cleared

**Definition of Done:** Draft persist and restore works; draft is cleared on save and cancel.

---

**[S-09] [FE] Implement: Idempotency key generation in expense form**

**Labels:** frontend, feature, high  
**Estimate:** 1 point  
**Depends on:** E-06

**Context:** The expense form generates an idempotency key on mount to prevent double-submission on slow connections. This is especially important on mobile where users may tap Submit and then tap again when the response is slow.

**Requirements:**
- Generate `crypto.randomUUID()` when the expense form mounts; store as a ref (not state — must not trigger re-render)
- Include the UUID in the `X-Idempotency-Key` header of the POST /expenses request
- On successful submission, regenerate the UUID (so the form is ready for the next expense)
- On submission failure (non-idempotency-related), do NOT regenerate — the user may retry with the same key

**Acceptance Criteria:**
- Given the form mounts, then a UUID is generated
- Given Submit is tapped twice in rapid succession, then only one POST request succeeds (the second returns the cached idempotency response)
- Given the form is successfully submitted and dismissed, then mounting it again generates a new UUID

**Definition of Done:** Double-tap creates only one expense; UUID regenerates after success.

---

**[S-11] [BE] Write: Integration tests for all API endpoints**

**Labels:** backend, chore, urgent  
**Estimate:** 5 points  
**Depends on:** S-02, S-04

**Context:** Integration tests run against a real (test) database and verify the full request lifecycle including auth middleware, service layer, and database writes. These tests are the primary gate in GitHub Actions CI — no PR merges without them passing.

**Requirements:**
- Test client: `httpx.AsyncClient` with `transport=ASGITransport(app=app)`
- Test database: PostgreSQL in Docker (same image as production); Alembic upgrades applied before test suite; transaction rollback per test for isolation
- Coverage targets: every endpoint in the API spec must have at least one test; every 4xx error case must have a test
- Key scenarios to cover:
  - Full group creation → join → expense → balance → settle-up flow (happy path)
  - Cross-group access blocked (403)
  - Idempotency: duplicate POST creates exactly one resource
  - Soft delete: deleted expense not in list; deleted settlement not in balance
  - Session expiry: expired JWT returns 401
  - Equal split rounding: 1-cent remainder assigned correctly

**Acceptance Criteria:**
- Running `pytest src/backend/tests/` produces zero failures
- Test coverage for all routers is >= 80%
- Tests run in < 60 seconds total

**Definition of Done:** `pytest` passes with zero failures; CI step uses these tests.

---

**[S-12] [FE] Implement: Mobile-first responsiveness audit**

**Labels:** frontend, chore, high  
**Estimate:** 3 points  
**Depends on:** S-05, E-10

**Context:** The product must work on mobile as a first-class experience (Maya logs expenses on her phone during a trip). This issue is a dedicated audit pass across all screens to verify mobile requirements.

**Requirements:**
- Verify minimum width 320px renders without horizontal scroll on all pages
- Verify all interactive elements (buttons, inputs, tap targets) are >= 44×44px
- Verify all amount inputs use `inputMode="decimal"` and `type="text"` (not `type="number"`)
- Verify bottom navigation does not overlap content on iPhone (safe-area-inset-bottom)
- Verify `prefers-reduced-motion` media query suppresses all CSS transitions
- Verify confetti animation on settle-up does not trigger jank on a mid-range mobile device (throttle CPU in DevTools)

**Acceptance Criteria:**
- At 320px viewport, all pages render without horizontal scrollbar
- In DevTools mobile emulation (iPhone SE), all tap targets pass the 44px check
- With CPU throttled 4x, the settle-up confetti animation maintains >= 30fps

**Definition of Done:** Manual audit checklist complete with no failures; developer signs off.

---

### Epic: Infrastructure, CI/CD, and Polish

---

**[I-01] [INFRA] Implement: GitHub Actions CI workflow**

**Labels:** infra, chore, urgent  
**Estimate:** 5 points  
**Depends on:** S-11

**Context:** CI is non-negotiable. Every PR must be gated by lint, type checks, unit tests, integration tests, and a Docker build test before it can be merged. Engineers must never wait more than 10 minutes for CI feedback.

**Requirements:**
- Trigger: `on: [pull_request]` to any branch
- Jobs (run in parallel where possible):
  - `lint-backend`: ruff check + ruff format --check
  - `typecheck-backend`: pyright `src/backend/`
  - `test-backend`: pytest with PostgreSQL service container; runs unit + integration tests; uploads coverage report
  - `typecheck-frontend`: `pnpm exec tsc --noEmit`
  - `build-frontend`: `pnpm build`
  - `docker-build`: `docker compose build` (verifies all Dockerfiles build successfully)
- Cache: pip/uv cache for Python deps; pnpm store cache for Node deps
- CI must complete in <= 10 minutes on GitHub-hosted runners

**Acceptance Criteria:**
- Given a PR is opened, then all CI jobs run automatically
- Given any job fails, then the PR is blocked from merging
- Given all jobs pass, then the PR shows a green check mark
- Given no code changes (only docs), then the full CI suite still runs (no skip logic — correctness over speed)

**Definition of Done:** CI runs on an actual PR; all jobs pass on the main branch.

---

**[I-02] [INFRA] Implement: GitHub Actions CD workflow**

**Labels:** infra, chore, high  
**Estimate:** 5 points  
**Depends on:** I-01

**Context:** CD automates deployment to staging (Fly.io backend + Vercel frontend) on every merge to main. The migration step must run before the backend is deployed — never deploy a new backend version before the DB schema is updated.

**Requirements:**
- Trigger: `on: push: branches: [main]`
- Steps in order:
  1. Run migrations: `fly ssh console -a fairsplit-backend -C "alembic upgrade head"`
  2. Deploy backend: `fly deploy --app fairsplit-backend`
  3. Deploy frontend: `vercel deploy --prod --token $VERCEL_TOKEN`
  4. Smoke test: `curl https://api.fairsplit.fly.dev/health` → must return 200
- Secrets required: `FLY_API_TOKEN`, `VERCEL_TOKEN` — documented in repo README
- Rollback: if smoke test fails, CD step exits with non-zero code and alerts via GitHub notification

**Acceptance Criteria:**
- Given a merge to main, then the backend and frontend are deployed to staging automatically
- Given the health check returns non-200, then the CD workflow fails and the team is notified
- Given migrations fail, then the backend deploy step is skipped

**Definition of Done:** CD runs on a merge to main; staging is updated; smoke test validates the deploy.

---

**[I-03] [DB] Implement: seed.py — realistic seeded groups**

**Labels:** db, chore, urgent  
**Estimate:** 5 points  
**Depends on:** S-03

**Context:** Seeded data is mandatory — every developer and QA engineer must be able to run `python seed.py` and see a populated, functional application. Seeded users must land on a non-empty dashboard. A blank dashboard after seeding is a seed failure.

**Requirements:**
- Two seeded groups:
  1. "Nashville Trip 2026" — 6 members: Maya (admin), Daniel, Priya, Tom, Jake, Sarah. 15 expenses (mix of equal and custom splits covering food, transport, accommodation). 1 settlement (Tom paid Jake $25). Net balances are non-zero for at least 4 members.
  2. "Roommates — April" — 3 members: Alex (admin), Jordan, Casey. 8 expenses (utilities, groceries, internet). All balances non-zero. No settlements yet.
- All amounts stored as integer cents (no float arithmetic in seed script)
- Each seeded member gets a valid JWT token printed to stdout (so the dev can paste it into the dev panel or make API calls)
- Idempotent: running `python seed.py` twice does not create duplicate groups (checks by group name before creating)
- The seeded data exercises all features: equal split, custom amount split, custom percentage split, at least one settlement

**Acceptance Criteria:**
- Given `python seed.py` is run against a fresh database, then both groups exist with correct member counts and expenses
- Given a developer opens the dev panel and clicks the join link for "Maya" in Nashville Trip, then they see a populated dashboard with expenses and a non-zero balance
- Given `python seed.py` is run twice, then only two groups exist (idempotent)

**Definition of Done:** Seeded groups have realistic data; dev panel links work; smoke test uses seed data.

---

**[I-04] [FE] Implement: Dev login panel**

**Labels:** frontend, chore, urgent  
**Estimate:** 3 points  
**Depends on:** I-03

**Context:** The dev panel is a mandatory quality requirement. It allows any developer or reviewer to immediately jump into a pre-populated group without going through the create/join flow manually. It is gated on `NEXT_PUBLIC_SHOW_DEV_PANEL=true` — never shown in production.

**Requirements:**
- Rendered only when `process.env.NEXT_PUBLIC_SHOW_DEV_PANEL === "true"`
- Shown on the home page (`app/page.tsx`) as a collapsible panel below the main CTA
- Lists both seeded groups with: group name, member count, and for each member: display name, role (admin/member), and a clickable "Join as [name]" link
- "Join as [name]" link: navigates to `/join/{inviteToken}?prefill={displayName}` — the join page auto-submits if the prefill param is present (or uses a direct join endpoint that accepts the member's existing JWT from seed output)
- Alternatively: the seed script can output a direct session link per member that bypasses the join form entirely

**Acceptance Criteria:**
- Given `NEXT_PUBLIC_SHOW_DEV_PANEL=true`, then the dev panel is visible on the home page
- Given the developer clicks "Join as Maya", then they are redirected to the Nashville Trip dashboard with Maya's session
- Given `NEXT_PUBLIC_SHOW_DEV_PANEL` is not set or is false, then no dev panel element is rendered in the DOM

**Definition of Done:** Dev panel visible in local dev; clicking any member link leads to a populated dashboard.

---

**[I-05] [BE] Implement: /metrics endpoint for Prometheus**

**Labels:** backend, chore, medium  
**Estimate:** 2 points  
**Depends on:** F-03

**Context:** The Prometheus metrics endpoint is what Grafana scrapes to populate the monitoring dashboard. It must be available from the first day the backend runs so that Grafana has historical data during development.

**Requirements:**
- Install `prometheus-fastapi-instrumentator` (or equivalent)
- Expose `GET /metrics` in Prometheus exposition format
- Metrics included: HTTP request count (by method + path + status), request duration histogram (by method + path), in-flight request gauge
- `/metrics` endpoint is public (no auth required) — it exposes no user data

**Acceptance Criteria:**
- Given the backend is running, then `curl http://localhost:8000/metrics` returns a valid Prometheus text format response
- Given 10 requests have been made, then the request count metric reflects 10 requests
- Given Prometheus is scraping the endpoint, then the Grafana dashboard shows non-zero values

**Definition of Done:** Metrics endpoint returns valid Prometheus format; Grafana dashboard shows data.

---

**[I-06] [INFRA] Implement: Grafana dashboard panels**

**Labels:** infra, chore, medium  
**Estimate:** 3 points  
**Depends on:** I-05, F-08

**Context:** The Grafana dashboard is the primary operational view during development and after launch. It must be provisioned automatically and contain actionable panels — not just vanity metrics.

**Requirements:**
- Panels:
  1. Request rate (requests/second, all endpoints combined)
  2. p95 latency by endpoint (time-series, one line per route)
  3. Error rate (4xx + 5xx percentage over total)
  4. DB connection pool saturation (active / max connections)
  5. Balance endpoint latency (dedicated panel — this is the SLA-gated endpoint)
  6. Settle-up endpoint latency (dedicated panel — the hero endpoint)
- Dashboard auto-provisions from JSON file in `src/infra/grafana/provisioning/dashboards/`
- Refresh interval: 30 seconds

**Acceptance Criteria:**
- Given `docker compose up`, then all 6 dashboard panels are visible without manual Grafana configuration
- Given 100 requests are made to the balance endpoint, then the p95 latency panel shows a non-zero value
- Given the error rate exceeds 10%, then the error rate panel turns red (threshold configured in JSON)

**Definition of Done:** All 6 panels render with data after `docker compose up` + seeded requests.

---

**[I-07] [QA] Write: Smoke test suite**

**Labels:** backend, chore, urgent  
**Estimate:** 5 points  
**Depends on:** I-03, I-04

**Context:** The smoke test suite is the final gate before any build is declared complete. It verifies the entire system end-to-end: `docker compose up` + seed → login → see data. A build that fails smoke tests is not done.

**Requirements:**
- `src/backend/tests/test_smoke.py` (or a separate `tests/smoke/` directory)
- Steps (in order):
  1. Assert `GET /health` returns 200 with `{"status": "ok", "db": "ok"}`
  2. Assert `GET http://localhost:3000` returns 200 (frontend loads)
  3. Use a seeded member's JWT to call `GET /api/v1/groups/{nashvilleGroupId}/balances` — assert response is 200 and `data` array is non-empty (not blank dashboard)
  4. Call `GET /api/v1/groups/{nashvilleGroupId}/expenses` — assert at least one expense is present
  5. Call `GET /api/v1/groups/{nashvilleGroupId}/settle-up` — assert `transfer_count >= 1` (balances are not all zero in Nashville Trip)
  6. Call `POST /api/v1/groups/{nashvilleGroupId}/expenses` with a new expense — assert 201 response
  7. Assert the new expense appears in the expense list
- Smoke tests run as a CI step after `docker compose up` and `python seed.py`

**Acceptance Criteria:**
- Given `docker compose up && python seed.py` is run, then all 7 smoke test steps pass without error
- Given any smoke test step fails, then the CI pipeline fails and the build is not declared done
- Given the frontend container is not running, then smoke test step 2 fails with a clear error message (not a timeout)

**Definition of Done:** All 7 steps pass on a clean `docker compose up && python seed.py` run.

---

**[I-08] [BE] Implement: Security headers middleware**

**Labels:** backend, chore, high  
**Estimate:** 2 points  
**Depends on:** F-03

**Context:** Security headers are a baseline requirement. They protect against common browser-based attacks (clickjacking, MIME sniffing, XSS via inline scripts). They must be set on every response.

**Requirements:**
- FastAPI middleware that sets on every response:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:`
  - `Permissions-Policy: geolocation=(), camera=(), microphone=()`
- Does not override `Set-Cookie` or CORS headers

**Acceptance Criteria:**
- Given any HTTP response from the backend, then all 5 security headers are present
- Given a browser DevTools network panel, then the response headers show the correct values
- Given the Content-Security-Policy is set, then inline `<script>` tags on the frontend are blocked (frontend must not use inline scripts)

**Definition of Done:** All 5 headers present on every response; verified with curl.

---

**[I-09] [DB] Implement: Idempotency key cleanup task**

**Labels:** db, chore, medium  
**Estimate:** 1 point  
**Depends on:** F-07

**Context:** The idempotency_keys table will accumulate rows indefinitely without cleanup. A startup task deletes expired keys before serving traffic — simple, no cron scheduler required.

**Requirements:**
- In `src/backend/main.py` startup event (FastAPI lifespan): execute `DELETE FROM idempotency_keys WHERE expires_at < NOW()`
- Log how many rows were deleted (structured JSON log)
- If the DELETE fails (DB unreachable), log the error but do not prevent the server from starting

**Acceptance Criteria:**
- Given 100 expired idempotency keys are in the table, then after server restart, those rows are deleted
- Given the DB is unavailable at startup, then the server still starts (cleanup failure is non-fatal)

**Definition of Done:** Expired keys are deleted on startup; failure is non-fatal.

---

**[I-10] [BE] Implement: PATCH /api/v1/groups/{id} — update group name/description**

**Labels:** backend, feature, low  
**Estimate:** 1 point  
**Depends on:** G-01

**Context:** The group admin must be able to rename the group or update its description after creation. This is a simple PATCH with admin authorization.

**Requirements:**
- Admin-only (is_admin=true in JWT); returns 403 if not admin
- Request body: `{group_name?: string (1–80 chars), description?: string (0–200 chars)}` — both optional (PATCH semantics)
- Returns 200 with updated GroupSchema

**Acceptance Criteria:**
- Given an admin patches the group name, then GET /groups/{id} returns the new name
- Given a non-admin sends the PATCH, then the response is 403

**Definition of Done:** Admin can rename the group; non-admin is blocked.

---

## Dependency Map

```
F-01 (Docker Compose)
  └── F-02 (DB migrations)
  └── F-03 (FastAPI skeleton)
        └── F-04 (Auth middleware)
              └── G-01 (POST /groups)
                    └── G-03 (GET /groups + members)
                    └── G-04 (POST /invite)
                    └── E-01 (POST /expenses)
                          └── E-02 (GET /expenses)
                          └── E-03 (PATCH /expenses)
                          └── E-04 (DELETE /expenses)
                          └── E-05 (GET /balances)  ← CRITICAL PATH
                                └── S-01 (settle algorithm) ← CRITICAL PATH
                                      └── S-10 (algorithm unit tests)
                                      └── S-02 (GET /settle-up) ← CRITICAL PATH
                                            └── S-05 (settle-up UI) ← CRITICAL PATH
              └── G-02 (POST /join)
                    └── G-05 (GET /members/me)
  └── F-07 (Idempotency service)
  └── F-08 (Prometheus + Grafana)
        └── I-05 (/metrics endpoint)
        └── I-06 (Grafana panels)
  └── F-05 (Next.js skeleton)
        └── F-06 (routes + layout)
              └── G-06 (create group UI)
              └── G-07 (join UI)
              └── G-08 (session recovery)
              └── G-09 (dashboard shell)
                    └── E-06 (expense form - equal)
                          └── E-07 (custom split modes)
                          └── S-08 (draft persistence)
                          └── S-09 (idempotency key in form)
                    └── E-08 (expense list UI)
                    └── E-10 (balance view UI)

S-03 (POST /settlements)
  └── S-04 (DELETE /settlements)
  └── I-03 (seed.py)
        └── I-04 (dev panel)
        └── I-07 (smoke tests)

S-11 (integration tests)
  └── I-01 (GitHub Actions CI)
        └── I-02 (GitHub Actions CD)
```

**Critical path (longest dependency chain to hero feature):**

`F-01 → F-02 → F-03 → F-04 → G-01 → E-01 → E-05 → S-01 → S-02 → S-05`

Any delay on this chain delays the entire product. These 10 issues are the protected critical path. Assign the most senior engineer to E-05, S-01, and S-02.

---

## Risk Register

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R-01 | Settle-up algorithm correctness failure | Low | Critical | S-10 exhaustive unit tests must pass before S-02 is merged; algorithm logic is peer-reviewed against the pseudocode in technical-spec.md before implementation starts |
| R-02 | Safari ITP clears localStorage → returning iOS users see join screen | High | High | G-08 (session recovery via httpOnly cookie) is Sprint 1 work, not a post-launch fix; G-05 must be implemented before G-08 |
| R-03 | Balance CTE query too slow for 10s polling interval | Medium | High | E-05 must include a performance test at 200 expenses; if p95 exceeds 200ms, add `EXPLAIN ANALYZE` and add the partial index specified in the technical-spec before Sprint 2 starts |
| R-04 | Docker Compose startup order fails (backend starts before migrations complete) | Medium | High | F-01 must use `depends_on: migrate: condition: service_completed_successfully`; enforced in F-01 acceptance criteria |
| R-05 | Float arithmetic in expense amount handling produces wrong splits | High | High | E-01 must validate all amount handling in integer cents end-to-end; frontend sends string decimal, backend converts to cents — never pass a float to any arithmetic function; verified in integration tests |
| R-06 | Sprint 1 scope is too large (52 pts for 2 engineers at 70% = ~22 pts/eng) | High | High | Backend engineer prioritizes G-01, G-02, E-01, E-05 (the API surface that unblocks frontend); frontend starts against mock data on Day 1 and integrates live API on Day 4. If sprint is at risk, defer E-09 (expense detail edit/delete) to Sprint 2 |
| R-07 | Idempotency key not sent by frontend → double expense creation | Medium | Medium | S-09 (frontend idempotency key generation) is part of Sprint 2 scope; E-01 accepts requests without the header (idempotency is optional for clients) — but S-09 must ship before the app is considered production-ready |
| R-08 | CI takes > 10 minutes → engineers disable it | Medium | Medium | I-01 specifies parallelism between lint, typecheck, and test jobs; Docker layer caching for build step; target is < 8 minutes on GitHub-hosted runners |

---

## Definition of "Done" for the Project

The project is done when:
1. `docker compose up && python seed.py` starts all services cleanly
2. All smoke tests (I-07) pass on a clean environment
3. A developer can create a group, invite a second member, log 3 expenses (one of each split type), view correct balances, and see the correct settle-up plan — all in under 5 minutes
4. The settle-up algorithm passes all unit tests (S-10)
5. GitHub Actions CI (I-01) runs on every PR and no PR can merge with failing tests
6. The dev panel (I-04) shows seeded groups with click-to-join links
7. The app renders correctly at 320px viewport width on mobile

---

## What Is Explicitly Out of Scope (Not in Any Sprint)

Per PM handoff — these are not deferred, they are excluded from MVP:
- Receipt scanning / OCR (requires external API)
- In-app payments (FairSplit is a ledger, not a payment rail)
- Push notifications / email (no accounts = no notification address)
- Multi-currency auto-conversion (requires FX API)
- Native iOS/Android app (PWA first)
- Group archiving / closing
- Group admin role management (beyond the single admin model)
- Dark mode

---

*This roadmap covers 3 sprints (6 weeks) starting 2026-04-20. The settle-up algorithm (S-01 + S-10) is the highest-risk item and must be treated as the critical path through Sprint 2.*
