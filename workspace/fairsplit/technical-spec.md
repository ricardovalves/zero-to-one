# FairSplit — Technical Specification

**Version:** 1.0  
**Date:** 2026-04-15  
**Author:** CTO/Architect Agent  
**Status:** Ready for Engineering

---

## Table of Contents

1. Architecture Overview
2. Technology Stack
3. Data Architecture
4. API Design
5. Non-Functional Requirements
6. Testing Strategy
7. Deployment Architecture
8. Cost Analysis
9. Migration & Evolution Path
10. Architecture Decision Records (ADRs)
11. Open Technical Questions

---

## 1. Architecture Overview

### System Summary

FairSplit is a zero-dependency shared expense tracker. Users create a group by visiting the root URL, share an invite link, and members join with a display name only — no email, no password, no account. Expenses are logged, split according to three modes (equal, custom amounts, custom percentages), and the settle-up view computes the minimum number of transfers needed to clear all debts using a greedy max-heap algorithm. The entire product runs with `docker compose up` and requires zero external accounts or API keys.

**At scale:** 100–500 concurrent users, 5–20 members per group, 50–200 expenses per group. Architecture must support 10,000 users without a rewrite.

### Core Architectural Decisions

1. **Compute settle-up at read time, not write time.** The greedy max-heap algorithm is O(n log n) and completes in under 10ms for typical group sizes (under 50ms for 100 members). Pre-computation would require cache invalidation on every expense mutation — more complexity for no measurable benefit.

2. **Session model: httpOnly cookie as the primary session store, not localStorage.** Safari ITP clears localStorage after 7 days of inactivity. A server-set `httpOnly`, `SameSite=Lax` cookie carrying the signed member token is the correct approach for persistent anonymous sessions. localStorage is used only as an in-memory read cache for the current tab's session token (to avoid a round-trip cookie read on every API call that needs the token client-side). The cookie is the source of truth.

3. **All monetary amounts stored and computed as integer cents.** Floating-point arithmetic on monetary values produces rounding errors that compound over expense history. Integer cents eliminate this entire class of bug. Amounts are converted to cents on receipt (frontend sends string decimal; backend converts and stores integer). All arithmetic in the settle-up algorithm operates on integers. A 1-cent remainder from rounding is assigned to the first creditor alphabetically.

4. **Stateless API behind a single PostgreSQL instance.** No in-process caching, no shared memory, no Redis. The API is horizontally scalable by adding instances behind a load balancer. The database is the single source of truth. This is the correct trade-off for the expected scale (sub-1,000 concurrent users) and eliminates an entire category of cache invalidation bugs.

5. **Idempotency keys on all mutation endpoints.** The client generates a UUID when a form opens and sends it in `X-Idempotency-Key`. The server stores the key and response for 24 hours. Double-submits (network retries, double-taps) return the original response without a duplicate write. This is especially important for the group creation and expense creation flows.

---

### C4 Level 1 — System Context

```
                        ┌──────────────────────────────────────────┐
                        │              INTERNET                     │
                        └──────────────────────────────────────────┘
                                          │
                    ┌─────────────────────┼────────────────────────┐
                    │                     │                        │
             ┌──────▼──────┐    ┌─────────▼──────┐   ┌────────────▼────────┐
             │    Maya      │    │    Daniel       │   │    Ravi (Dev)       │
             │ Trip Organiz.│    │ Reluctant Partic│   │ Self-Hoster         │
             │ (Creator)    │    │ (Joiner via link│   │ (docker compose up) │
             └──────┬──────┘    └─────────┬──────┘   └────────────┬────────┘
                    │                     │                        │
                    └─────────────────────┴────────────────────────┘
                                          │
                                          │  HTTPS (browser / PWA)
                                          │
                        ┌─────────────────▼─────────────────────────┐
                        │                                            │
                        │         FairSplit System                   │
                        │                                            │
                        │  ┌──────────────┐   ┌──────────────────┐  │
                        │  │  Next.js 16  │   │   FastAPI 0.135  │  │
                        │  │  Frontend    │◄──►   Backend API    │  │
                        │  │  (App Router)│   │   (Python 3.12)  │  │
                        │  └──────────────┘   └────────┬─────────┘  │
                        │                              │             │
                        │                   ┌──────────▼──────────┐  │
                        │                   │  PostgreSQL 16.13   │  │
                        │                   │  (postgres:16-alpine│  │
                        │                   └─────────────────────┘  │
                        │                                            │
                        └────────────────────────────────────────────┘

  External systems: NONE (zero external dependencies — no email,
  no storage, no analytics service, no payment processor in MVP)
```

---

### C4 Level 2 — Containers

```
 ┌─────────────────────────────────────────────────────────────────────────┐
 │                         FairSplit System                                │
 │                                                                         │
 │  ┌─────────────────────────────────┐    ┌──────────────────────────┐   │
 │  │  FRONTEND CONTAINER              │    │  BACKEND CONTAINER        │   │
 │  │  Next.js 16.2.x                  │    │  FastAPI 0.135.x          │   │
 │  │  App Router + React 19           │    │  Python 3.12              │   │
 │  │  Deployed: Docker (local),       │◄──►│  uvicorn ASGI server      │   │
 │  │            Vercel (staging)      │    │  Deployed: Docker (local),│   │
 │  │  Port: 3000                      │    │            Fly.io (staging│   │
 │  │                                  │    │  Port: 8000               │   │
 │  │  Serves: HTML/JS/CSS SPA pages   │    │  Serves: REST API /api/v1 │   │
 │  └────────────────┬─────────────────┘    └────────────┬─────────────┘   │
 │                   │                                   │                 │
 │                   │  HTTP/JSON API calls               │                 │
 │                   │  (NEXT_PUBLIC_API_URL)             │  asyncpg        │
 │                   │                                   │  SQLAlchemy 2.0 │
 │                   │                      ┌────────────▼─────────────┐   │
 │                   │                      │  DATABASE CONTAINER       │   │
 │                   │                      │  PostgreSQL 16.13         │   │
 │                   │                      │  postgres:16-alpine       │   │
 │                   │                      │  Port: 5432               │   │
 │                   │                      │  Volume: postgres_data     │   │
 │                   │                      └──────────────────────────┘   │
 │                                                                         │
 │  ┌─────────────────────────────────┐                                    │
 │  │  MIGRATIONS CONTAINER (ephemeral)│                                   │
 │  │  Alembic 1.14.x                  │                                   │
 │  │  Runs: alembic upgrade head      │                                   │
 │  │  Exits after completion          │                                   │
 │  └─────────────────────────────────┘                                    │
 └─────────────────────────────────────────────────────────────────────────┘
```

---

### C4 Level 3 — Components (Backend)

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  BACKEND CONTAINER (FastAPI 0.135.x)                                     │
 │                                                                          │
 │  ┌─────────────────────────────────────────────────────────────────┐    │
 │  │  ROUTERS LAYER (src/backend/routers/)                            │    │
 │  │                                                                  │    │
 │  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────┐  │    │
 │  │  │ groups.py   │  │ expenses.py  │  │ settlements.py        │  │    │
 │  │  │ POST /groups│  │ POST /expenses  │ POST /settlements      │  │    │
 │  │  │ GET  /groups│  │ GET  /expenses  │ DELETE /settlements/{} │  │    │
 │  │  │ PATCH/groups│  │ PATCH /expenses │                        │  │    │
 │  │  └──────┬──────┘  │ DELETE /expen│  └──────────┬────────────┘  │    │
 │  │         │         └──────┬───────┘             │               │    │
 │  │  ┌──────▼──────┐  ┌──────▼───────┐  ┌──────────▼────────────┐  │    │
 │  │  │ members.py  │  │ balances.py  │  │ settle_up.py           │  │    │
 │  │  │ POST /join  │  │ GET /balances│  │ GET /settle-up         │  │    │
 │  │  └─────────────┘  └─────────────┘  └───────────────────────┘  │    │
 │  └────────────────────────────────┬────────────────────────────────┘    │
 │                                   │                                      │
 │  ┌────────────────────────────────▼────────────────────────────────┐    │
 │  │  SERVICES LAYER (src/backend/services/)                          │    │
 │  │                                                                  │    │
 │  │  ┌──────────────────┐   ┌─────────────────┐   ┌──────────────┐ │    │
 │  │  │ group_service.py │   │expense_service.py│   │settle_service│ │    │
 │  │  │ - create_group   │   │ - create_expense │   │ - compute()  │ │    │
 │  │  │ - update_group   │   │ - update_expense │   │ (greedy heap)│ │    │
 │  │  │ - get_group      │   │ - delete_expense │   └──────────────┘ │    │
 │  │  └──────────────────┘   │ - list_expenses  │                    │    │
 │  │                          └─────────────────┘                    │    │
 │  │  ┌──────────────────┐   ┌─────────────────┐   ┌──────────────┐ │    │
 │  │  │ member_service.py│   │balance_service.py│   │settlement_svc│ │    │
 │  │  │ - join_group     │   │ - compute_nets   │   │ - record()   │ │    │
 │  │  │ - get_member     │   │ - get_breakdown  │   │ - delete()   │ │    │
 │  │  └──────────────────┘   └─────────────────┘   └──────────────┘ │    │
 │  └────────────────────────────────┬────────────────────────────────┘    │
 │                                   │                                      │
 │  ┌────────────────────────────────▼────────────────────────────────┐    │
 │  │  REPOSITORIES LAYER (src/backend/repositories/)                  │    │
 │  │                                                                  │    │
 │  │  group_repo.py   member_repo.py   expense_repo.py               │    │
 │  │  settlement_repo.py   idempotency_repo.py                        │    │
 │  │  (All use SQLAlchemy 2.0 async ORM + asyncpg driver)             │    │
 │  └────────────────────────────────┬────────────────────────────────┘    │
 │                                   │                                      │
 │  ┌────────────────────────────────▼────────────────────────────────┐    │
 │  │  MIDDLEWARE LAYER (src/backend/middleware/)                       │    │
 │  │                                                                  │    │
 │  │  auth_middleware.py    — validates member_token cookie/header    │    │
 │  │  idempotency_middleware.py — checks X-Idempotency-Key header     │    │
 │  │  logging_middleware.py  — structured JSON request/response logs  │    │
 │  │  cors_middleware.py     — CORS for frontend origin               │    │
 │  └────────────────────────────────────────────────────────────────┘    │
 │                                                                          │
 │  ┌──────────────────────────────────────────────────────────────────┐   │
 │  │  CORE (src/backend/core/)                                         │   │
 │  │  config.py (pydantic-settings)   db.py (async engine + session)  │   │
 │  │  security.py (JWT sign/verify via PyJWT)                         │   │
 │  └──────────────────────────────────────────────────────────────────┘   │
 └──────────────────────────────────────────────────────────────────────────┘
```

### C4 Level 3 — Components (Frontend)

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  FRONTEND CONTAINER (Next.js 16.2.x, App Router)                         │
 │                                                                          │
 │  app/ (Next.js App Router)                                               │
 │  ├── page.tsx                — Home: "Create a Group" CTA                │
 │  ├── groups/                                                             │
 │  │   └── [groupId]/                                                      │
 │  │       ├── page.tsx        — Group dashboard (expenses + balance)      │
 │  │       ├── expenses/                                                   │
 │  │       │   └── [expenseId]/page.tsx — Expense detail                  │
 │  │       └── settle-up/page.tsx — Settle-up plan view                   │
 │  └── join/                                                               │
 │      └── [groupId]/page.tsx  — Join group (display name form)           │
 │                                                                          │
 │  components/ (shared React 19 components)                                │
 │  ├── expense-form/           — Add/Edit expense form with draft persist  │
 │  ├── balance-list/           — Member balance cards                      │
 │  ├── settle-up-plan/         — Transfer list + copy-to-clipboard         │
 │  ├── member-list/            — Group member roster                       │
 │  └── ui/                    — Design system primitives (Button, Toast,  │
 │                               Input, Modal, Badge)                       │
 │                                                                          │
 │  lib/                                                                    │
 │  ├── api-client.ts           — Typed fetch wrapper (NEXT_PUBLIC_API_URL) │
 │  ├── session.ts              — Cookie read + localStorage cache          │
 │  ├── settle-algorithm.ts     — Client-side algorithm preview (optional)  │
 │  └── format.ts               — Currency formatting (cents → display)     │
 │                                                                          │
 │  hooks/                                                                  │
 │  ├── useGroup.ts             — SWR hook: group data + polling            │
 │  ├── useBalances.ts          — SWR hook: member balances (10s refresh)  │
 │  ├── useExpenses.ts          — SWR hook: expense list                    │
 │  └── useSettleUp.ts          — SWR hook: settle-up plan                 │
 └──────────────────────────────────────────────────────────────────────────┘
```

### C4 Level 4 — Code: Settle-Up Service (most complex component)

```python
# src/backend/services/settle_service.py
#
# The minimum-transfer settle-up algorithm.
# IMPORTANT: The problem is NP-Complete (reducible from Sum of Subsets).
# This greedy heuristic produces the exact minimum for most practical group
# sizes (n <= 20) and a near-optimal result for larger groups. It is NOT
# provably optimal for all inputs. The PRD documents this trade-off (P11).
#
# Algorithm: O(n log n) greedy max-heap.
# Input:  dict[member_id, int]  — net balance in cents (+ = creditor, - = debtor)
# Output: list[Transfer]        — ordered list of (debtor_id, creditor_id, amount_cents)

import heapq
from dataclasses import dataclass
from uuid import UUID

@dataclass
class Transfer:
    debtor_id: UUID
    debtor_name: str
    creditor_id: UUID
    creditor_name: str
    amount_cents: int   # always positive
    currency: str       # ISO 4217

def compute_settle_up(
    net_balances: dict[UUID, int],
    member_names: dict[UUID, str],
    currency: str = "USD",
) -> list[Transfer]:
    """
    Greedy max-heap minimum-transfer algorithm.

    Args:
        net_balances:  Map of member_id -> net balance in cents.
                       Positive = creditor (owed money).
                       Negative = debtor (owes money).
                       Must sum to zero (enforced by expense model).
        member_names:  Map of member_id -> display name.
        currency:      ISO 4217 currency code for this settlement.

    Returns:
        List of Transfer objects. Empty list if all balances are zero.

    Raises:
        ValueError: If net_balances does not sum to zero (data inconsistency).
    """
    total = sum(net_balances.values())
    if total != 0:
        # Log the discrepancy; adjust by assigning remainder to first creditor
        # alphabetically (same convention as rounding policy).
        sorted_creditors = sorted(
            [(uid, bal) for uid, bal in net_balances.items() if bal > 0],
            key=lambda x: member_names[x[0]]
        )
        if sorted_creditors:
            first_creditor_id, _ = sorted_creditors[0]
            net_balances[first_creditor_id] -= total  # absorb discrepancy

    # Build max-heaps (Python heapq is min-heap; negate values for max-heap)
    creditors: list[tuple[int, UUID]] = []   # (-balance, member_id)
    debtors:   list[tuple[int, UUID]] = []   # (-abs_balance, member_id)

    for member_id, balance in net_balances.items():
        if balance > 0:
            heapq.heappush(creditors, (-balance, member_id))
        elif balance < 0:
            heapq.heappush(debtors, (balance, member_id))   # negative = already "max"

    transfers: list[Transfer] = []

    while creditors and debtors:
        neg_cred_bal, creditor_id = heapq.heappop(creditors)
        debtor_bal, debtor_id     = heapq.heappop(debtors)

        cred_bal = -neg_cred_bal          # restore to positive
        debt_abs = -debtor_bal            # restore to positive

        transfer_amount = min(cred_bal, debt_abs)

        transfers.append(Transfer(
            debtor_id=debtor_id,
            debtor_name=member_names[debtor_id],
            creditor_id=creditor_id,
            creditor_name=member_names[creditor_id],
            amount_cents=transfer_amount,
            currency=currency,
        ))

        remaining_cred = cred_bal - transfer_amount
        remaining_debt = debt_abs - transfer_amount

        if remaining_cred > 0:
            heapq.heappush(creditors, (-remaining_cred, creditor_id))
        if remaining_debt > 0:
            heapq.heappush(debtors, (-remaining_debt, debtor_id))

    return transfers
```

### C4 Level 4 — Code: Auth Middleware (session model)

```python
# src/backend/middleware/auth_middleware.py
#
# Anonymous member session model.
#
# Session token lifecycle:
# 1. Member joins a group (POST /api/v1/groups/{id}/members).
# 2. Server creates a Member record and issues a signed JWT.
# 3. JWT payload: {sub: member_id, group_id: group_id, iat: unix, exp: unix}
# 4. JWT is set as an httpOnly, SameSite=Lax cookie AND returned in the
#    response body (so the frontend can store it in localStorage as a cache).
# 5. On subsequent requests, the server reads the cookie (primary).
#    If no cookie, falls back to Authorization: Bearer <token> header
#    (for API clients and cross-origin test scenarios).
# 6. Cookie expiry: 30 days from issue, rolling (reset on each valid request).
#
# Safari ITP note: server-set httpOnly cookies are NOT subject to ITP's
# 7-day localStorage clearing rule. They are only cleared if the user
# explicitly clears cookies. This is the correct solution for persistent
# anonymous sessions.

import jwt                              # PyJWT (not python-jose)
from fastapi import Request, HTTPException
from uuid import UUID

ALGORITHM = "HS256"

def decode_member_token(token: str, secret: str) -> dict:
    try:
        payload = jwt.decode(token, secret, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="SESSION_EXPIRED")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="SESSION_INVALID")

def get_current_member(request: Request, secret: str) -> dict:
    """
    Extract and validate the member token from:
    1. httpOnly cookie named 'fairsplit_member_token' (primary)
    2. Authorization: Bearer header (fallback for API clients)
    """
    token = request.cookies.get("fairsplit_member_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="NO_SESSION")
    return decode_member_token(token, secret)
```

---

## 2. Technology Stack

| Layer | Technology | Version | Local/Prototype | Staging/Production | Rationale | Alternatives Considered |
|---|---|---|---|---|---|---|
| Frontend framework | Next.js | 16.2.x | Docker (port 3000) | Vercel free tier | App Router, React 19, Turbopack (stable in 16), zero-config PWA support | Vite+React SPA: no SSR/metadata control; Remix: less ecosystem momentum |
| Frontend runtime | React | 19.x | same | same | Required by Next.js 16; concurrent features improve form responsiveness | N/A |
| Frontend styling | Tailwind CSS | 4.x | same | same | Utility-first, no external CSS dependency, works with Next.js 16 turbopack | CSS Modules: more boilerplate; shadcn/ui components built on Tailwind |
| UI components | shadcn/ui | latest | same | same | Unstyled accessible primitives; copy-into-project model — no npm dependency lock-in | Radix UI direct: more setup; Mantine: heavier bundle |
| Data fetching | SWR | 2.x | same | same | Automatic polling (refreshInterval), stale-while-revalidate, deduplicated requests | React Query: functionally equivalent; chose SWR for smaller bundle |
| Backend framework | FastAPI | 0.135.x | Docker (port 8000) | Fly.io free tier | Async-first, OpenAPI auto-generation, Pydantic v2 validation | Django REST: sync-first complexity; Flask: no async native support |
| Backend language | Python | 3.12 | Docker python:3.12-slim | same | Supported by FastAPI 0.135+, performance improvements, no 3.8/3.9 deprecation risk | 3.11: supported but older; 3.13: too new for ecosystem |
| ASGI server | uvicorn | 0.34.x | Docker | Fly.io | Standard ASGI server for FastAPI; gunicorn+uvicorn workers for prod | hypercorn: less community adoption |
| Database | PostgreSQL | 16.13 | postgres:16-alpine Docker | Fly Postgres (free) | Integer-cent storage, JSON support, excellent async support via asyncpg | MySQL: less expression power; SQLite: no concurrent writes |
| ORM | SQLAlchemy | 2.0.x | same | same | Async-native in 2.0, Mapped[] typed models, best-in-class Python ORM | Tortoise ORM: smaller ecosystem; raw asyncpg: too much boilerplate |
| Async DB driver | asyncpg | 0.30.x | same | same | Fastest PostgreSQL async driver for Python; native protocol | psycopg3: also valid; asyncpg has more production references |
| Migrations | Alembic | 1.14.x | Docker (ephemeral container) | Run before server start | Pairs with SQLAlchemy, autogenerate support, transaction-per-migration | Flyway: Java dependency; raw SQL: no version tracking |
| JWT signing | PyJWT | 2.10.x | same | same | Official FastAPI recommendation (python-jose deprecated); actively maintained | python-jose: abandoned since 2021; authlib: overkill |
| Validation (API) | Pydantic | 2.x | same | same | Bundled with FastAPI; v2 is 5–50x faster than v1 | marshmallow: separate library, slower |
| Auth | Custom JWT (httpOnly cookie) | — | same | same | No external service; group-scoped anonymous sessions; Safari ITP safe | Clerk: paid; Auth0: external; NextAuth.js: not needed without OAuth |
| CI/CD | GitHub Actions | — | — | GitHub-hosted runners | Free for public repos; 2,000 min/month for private | CircleCI: paid; Jenkins: self-hosted overhead |
| Monitoring | Grafana + Prometheus | Grafana 11.x / Prom 2.x | Docker | Self-hosted or Grafana Cloud free | Fully open-source; Docker-native; no account required | Datadog: paid; New Relic: paid |
| Error tracking | Sentry | free tier (optional) | stderr logs | Sentry free (5K events/mo) | Free tier adequate for launch; SDK is one-line install | Honeybadger: paid; Rollbar: paid |
| Package manager (BE) | uv | 0.6.x | same | same | 10–100x faster than pip; PEP 517 compliant; lockfile support | pip+requirements.txt: no lockfile; Poetry: slower |
| Package manager (FE) | pnpm | 9.x | same | same | Disk-efficient, strict dependency resolution, monorepo support | npm: slow; yarn: less efficient |

---

## 3. Data Architecture

### Entity-Relationship Diagram

```
groups ──────────────────< members
   │                          │
   │                          │ (logged_by_member_id)
   └──────────────────< expenses ──────────────────< expense_splits
                          │
                          └──── (payer_member_id FK → members)

members ──────────────────< settlements
   (payer_member_id)

groups ──────────────────< idempotency_keys

groups ──────────────────< settlements
   (via members — group is implicit through member)
```

### Complete SQL DDL

```sql
-- Enable pgcrypto extension for gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- groups
-- ============================================================
CREATE TABLE groups (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name             VARCHAR(80)  NOT NULL CHECK (length(trim(name)) > 0),
    description      VARCHAR(200),
    invite_token     UUID         NOT NULL DEFAULT gen_random_uuid() UNIQUE,
    status           VARCHAR(20)  NOT NULL DEFAULT 'active'
                     CHECK (status IN ('active', 'archived')),
    default_currency CHAR(3)      NOT NULL DEFAULT 'USD',
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Index for invite link lookup (the most common read path for new joins)
CREATE UNIQUE INDEX idx_groups_invite_token ON groups (invite_token);

-- ============================================================
-- members
-- ============================================================
CREATE TABLE members (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id     UUID        NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    display_name VARCHAR(40) NOT NULL CHECK (length(trim(display_name)) > 0),
    is_admin     BOOLEAN     NOT NULL DEFAULT FALSE,
    joined_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Lookup members by group (used on every group dashboard load)
CREATE INDEX idx_members_group_id ON members (group_id);

-- Soft-uniqueness: display name within a group (enforced at application layer,
-- not DB constraint, because duplicates are allowed with suffix appended)

-- ============================================================
-- expenses
-- ============================================================
CREATE TABLE expenses (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id            UUID        NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    payer_member_id     UUID        NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    logged_by_member_id UUID        NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    description         VARCHAR(200) NOT NULL CHECK (length(trim(description)) > 0),
    amount_cents        INTEGER     NOT NULL CHECK (amount_cents > 0),
    currency            CHAR(3)     NOT NULL DEFAULT 'USD',
    split_type          VARCHAR(20) NOT NULL
                        CHECK (split_type IN ('equal', 'custom_amount', 'custom_percentage')),
    expense_date        DATE        NOT NULL DEFAULT CURRENT_DATE,
    deleted_at          TIMESTAMPTZ,   -- soft delete
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Primary query path: list expenses for a group, newest first, excluding deleted
CREATE INDEX idx_expenses_group_id_active
    ON expenses (group_id, created_at DESC)
    WHERE deleted_at IS NULL;

-- For balance computation: all active expenses by group (no order needed)
CREATE INDEX idx_expenses_group_id_not_deleted
    ON expenses (group_id)
    WHERE deleted_at IS NULL;

-- For permission check: "did this member log this expense?"
CREATE INDEX idx_expenses_logged_by ON expenses (logged_by_member_id);

-- ============================================================
-- expense_splits
-- ============================================================
CREATE TABLE expense_splits (
    id           UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    expense_id   UUID    NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
    member_id    UUID    NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    -- For custom_percentage split type: stored for display purposes only.
    -- amount_cents is always the authoritative value.
    percentage   NUMERIC(6,3),
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (expense_id, member_id)
);

-- Balance computation query joins expense_splits with expenses:
-- SELECT member_id, SUM(amount_cents) FROM expense_splits
-- JOIN expenses ON expenses.id = expense_splits.expense_id
-- WHERE expenses.group_id = $1 AND expenses.deleted_at IS NULL
CREATE INDEX idx_expense_splits_expense_id ON expense_splits (expense_id);
CREATE INDEX idx_expense_splits_member_id  ON expense_splits (member_id);

-- ============================================================
-- settlements
-- ============================================================
CREATE TABLE settlements (
    id               UUID    PRIMARY KEY DEFAULT gen_random_uuid(),
    group_id         UUID    NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    payer_member_id  UUID    NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    payee_member_id  UUID    NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
    amount_cents     INTEGER NOT NULL CHECK (amount_cents > 0),
    currency         CHAR(3) NOT NULL DEFAULT 'USD',
    deleted_at       TIMESTAMPTZ,   -- soft delete (settlement can be reversed)
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK (payer_member_id != payee_member_id)
);

-- Balance computation: active settlements by group
CREATE INDEX idx_settlements_group_id_active
    ON settlements (group_id)
    WHERE deleted_at IS NULL;

-- ============================================================
-- idempotency_keys
-- ============================================================
-- Stores client-generated idempotency keys for 24 hours.
-- Prevents double-submission on group creation, expense creation,
-- and settlement creation.
CREATE TABLE idempotency_keys (
    key            UUID        PRIMARY KEY,
    endpoint       VARCHAR(100) NOT NULL,   -- e.g., 'POST /api/v1/groups'
    response_body  JSONB       NOT NULL,
    status_code    SMALLINT    NOT NULL,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at     TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
);

-- Automatic cleanup: query for expired keys (a background task purges these).
-- Alternatively, a partial index for active keys:
CREATE INDEX idx_idempotency_keys_expires ON idempotency_keys (expires_at)
    WHERE expires_at > NOW();
```

### Updated_at Trigger (applied to all tables)

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_groups_updated_at
    BEFORE UPDATE ON groups
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_members_updated_at
    BEFORE UPDATE ON members
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_expenses_updated_at
    BEFORE UPDATE ON expenses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_expense_splits_updated_at
    BEFORE UPDATE ON expense_splits
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER set_settlements_updated_at
    BEFORE UPDATE ON settlements
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

### Common Query Patterns and Execution Plans

**Query 1: Compute net balances for all members in a group**

This is the most performance-critical query. Called on every balance view and every settle-up computation.

```sql
-- Net balance computation
-- paid_total: sum of all expenses where this member was the payer
-- owed_total: sum of all expense_splits where this member is included
-- net_cents: paid_total - owed_total (positive = creditor)

WITH paid AS (
    SELECT payer_member_id AS member_id,
           SUM(amount_cents) AS paid_total
    FROM expenses
    WHERE group_id = $1
      AND deleted_at IS NULL
    GROUP BY payer_member_id
),
owed AS (
    SELECT es.member_id,
           SUM(es.amount_cents) AS owed_total
    FROM expense_splits es
    JOIN expenses e ON e.id = es.expense_id
    WHERE e.group_id = $1
      AND e.deleted_at IS NULL
    GROUP BY es.member_id
),
settled_paid AS (
    SELECT payer_member_id AS member_id,
           SUM(amount_cents) AS settled_out
    FROM settlements
    WHERE group_id = $1
      AND deleted_at IS NULL
    GROUP BY payer_member_id
),
settled_received AS (
    SELECT payee_member_id AS member_id,
           SUM(amount_cents) AS settled_in
    FROM settlements
    WHERE group_id = $1
      AND deleted_at IS NULL
    GROUP BY payee_member_id
)
SELECT
    m.id AS member_id,
    m.display_name,
    COALESCE(p.paid_total, 0)      AS paid_total_cents,
    COALESCE(o.owed_total, 0)      AS owed_total_cents,
    COALESCE(sp.settled_out, 0)    AS settled_out_cents,
    COALESCE(sr.settled_in, 0)     AS settled_in_cents,
    COALESCE(p.paid_total, 0)
      - COALESCE(o.owed_total, 0)
      + COALESCE(sp.settled_out, 0)
      - COALESCE(sr.settled_in, 0) AS net_cents
FROM members m
LEFT JOIN paid            p ON p.member_id = m.id
LEFT JOIN owed            o ON o.member_id = m.id
LEFT JOIN settled_paid   sp ON sp.member_id = m.id
LEFT JOIN settled_received sr ON sr.member_id = m.id
WHERE m.group_id = $1
ORDER BY net_cents DESC;

-- Expected execution plan (group with 10 members, 100 expenses):
-- Hash Join → Seq Scan on members (10 rows) → Hash Agg on expenses
-- Estimated cost: < 5ms with indexes on expenses(group_id) and
-- expense_splits(member_id). idx_expenses_group_id_not_deleted is critical.
```

**Query 2: List active expenses for a group (paginated)**

```sql
SELECT
    e.id,
    e.description,
    e.amount_cents,
    e.currency,
    e.split_type,
    e.expense_date,
    e.created_at,
    m_payer.display_name AS payer_name,
    m_logger.display_name AS logged_by_name,
    COUNT(es.id) AS split_count
FROM expenses e
JOIN members m_payer  ON m_payer.id  = e.payer_member_id
JOIN members m_logger ON m_logger.id = e.logged_by_member_id
JOIN expense_splits es ON es.expense_id = e.id
WHERE e.group_id = $1
  AND e.deleted_at IS NULL
GROUP BY e.id, m_payer.display_name, m_logger.display_name
ORDER BY e.created_at DESC
LIMIT $2 OFFSET $3;

-- Expected plan: Index Scan on idx_expenses_group_id_active (covering),
-- Nested Loop join on members (2 rows each), Hash Agg on expense_splits.
-- Performance: < 10ms for 200 expenses with correct indexes.
```

**Query 3: Get expense detail with full split breakdown**

```sql
SELECT
    e.id,
    e.description,
    e.amount_cents,
    e.currency,
    e.split_type,
    e.expense_date,
    e.created_at,
    m_payer.id           AS payer_id,
    m_payer.display_name AS payer_name,
    m_logger.display_name AS logged_by_name,
    es.member_id         AS split_member_id,
    m_split.display_name AS split_member_name,
    es.amount_cents      AS split_amount_cents,
    es.percentage        AS split_percentage
FROM expenses e
JOIN members m_payer   ON m_payer.id   = e.payer_member_id
JOIN members m_logger  ON m_logger.id  = e.logged_by_member_id
JOIN expense_splits es ON es.expense_id = e.id
JOIN members m_split   ON m_split.id    = es.member_id
WHERE e.id = $1
  AND e.deleted_at IS NULL;

-- Expected plan: Index Scan on expenses(id) PK, 3x Nested Loop joins
-- on members. All lookups by PK. < 2ms.
```

**Query 4: Check idempotency key before processing a mutation**

```sql
SELECT response_body, status_code
FROM idempotency_keys
WHERE key = $1
  AND expires_at > NOW();

-- Expected plan: Index Scan on idempotency_keys PK. < 1ms.
```

**Query 5: List settlements for balance computation**

```sql
SELECT
    s.payer_member_id,
    s.payee_member_id,
    s.amount_cents,
    s.currency,
    s.created_at,
    m_payer.display_name AS payer_name,
    m_payee.display_name AS payee_name
FROM settlements s
JOIN members m_payer ON m_payer.id = s.payer_member_id
JOIN members m_payee ON m_payee.id = s.payee_member_id
WHERE s.group_id = $1
  AND s.deleted_at IS NULL
ORDER BY s.created_at DESC;

-- Expected plan: Index Scan on idx_settlements_group_id_active,
-- 2x Nested Loop on members. < 3ms.
```

---

## 4. API Design

### API Versioning Strategy

All endpoints are prefixed with `/api/v1/`. Version is in the URL path. No header-based versioning. When breaking changes are introduced, `/api/v2/` is added and `/api/v1/` is maintained for a deprecation period of 6 months.

### Standard Response Envelopes

**Singleton response** — used for: auth/session endpoints, single-resource GET, POST, PATCH, DELETE.  
The resource object is returned directly at the top level. No wrapper.

```json
// GET /api/v1/groups/{group_id}
// 200 OK
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Nashville Trip",
    "description": "June 2026 friend group",
    "invite_token": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "status": "active",
    "default_currency": "USD",
    "member_count": 6,
    "expense_count": 23,
    "created_at": "2026-04-15T14:00:00Z",
    "updated_at": "2026-04-15T18:30:00Z"
}
```

**List response** — used for: collection GET endpoints (expenses, members, settlements).

```json
// GET /api/v1/groups/{group_id}/expenses
// 200 OK
{
    "data": [ ... ],
    "total": 23,
    "page": 1,
    "per_page": 20
}
```

**Error response** — used for all 4xx and 5xx responses.

```json
// 422 Unprocessable Entity
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Amount must be greater than zero.",
        "field": "amount",
        "request_id": "req_abc123"
    }
}
```

### Authentication Flow

```
Client                              Server
  │                                   │
  │  POST /api/v1/groups              │
  │  Body: {name, description, admin_name} │
  │  Header: X-Idempotency-Key: <uuid>│
  │──────────────────────────────────►│
  │                                   │  1. Validate idempotency key
  │                                   │  2. Create group + member row
  │                                   │  3. Sign JWT:
  │                                   │     { sub: member_id,
  │                                   │       group_id: group_id,
  │                                   │       is_admin: true,
  │                                   │       iat: now,
  │                                   │       exp: now+30d }
  │                                   │  4. Set-Cookie: fairsplit_member_token
  │◄──────────────────────────────────│     HttpOnly; Secure; SameSite=Lax
  │  201 Created                      │     Max-Age=2592000 (30 days)
  │  Body: {group, member, token}     │
  │  Cookie: fairsplit_member_token   │
  │                                   │
  │  [Frontend stores token in localStorage as cache]
  │                                   │
  │  GET /api/v1/groups/{id}          │
  │  Cookie: fairsplit_member_token   │
  │──────────────────────────────────►│
  │                                   │  5. Read cookie
  │                                   │  6. Verify JWT signature + expiry
  │                                   │  7. Extract member_id + group_id
  │                                   │  8. Verify member belongs to group
  │◄──────────────────────────────────│  9. Reset cookie Max-Age (rolling)
  │  200 OK                           │
  │                                   │
  │  [Session expires after 30 days of inactivity]
  │                                   │
  │  GET /api/v1/groups/{id}          │
  │  Cookie: <expired token>          │
  │──────────────────────────────────►│
  │                                   │  10. JWT expired → 401
  │◄──────────────────────────────────│
  │  401 SESSION_EXPIRED              │
  │  [Frontend redirects to /join/{id}│
  │   with "session expired" notice]  │
```

### Rate Limiting

Rate limiting is implemented at the application level using slowapi (FastAPI rate limiting library). No external infrastructure (Redis) required for the target scale.

| Endpoint | Limit | Window | Rationale |
|---|---|---|---|
| `POST /api/v1/groups` | 10 req | per IP per hour | Prevent group spam |
| `POST /api/v1/groups/{id}/members` | 30 req | per IP per hour | Allow burst joins when group link is shared |
| `POST /api/v1/groups/{id}/expenses` | 60 req | per member per hour | ~1 expense/minute is a natural maximum |
| `GET *` | 300 req | per IP per minute | Standard read protection |
| `DELETE *` | 30 req | per member per hour | Prevent accidental mass deletion |

Rate limit headers returned on all responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 54
X-RateLimit-Reset: 1713200000
Retry-After: 42  (only on 429 responses)
```

### Pagination Strategy

**Offset pagination** is used for the expense list. The expense list is sorted by `created_at DESC` with a stable UUID tiebreaker. Cursor-based pagination is deferred to Phase 2 when groups exceed 1,000 expenses (not expected in MVP).

Default page size: 20. Maximum page size: 100.

```
GET /api/v1/groups/{id}/expenses?page=2&per_page=20
```

### Error Codes (Machine-Readable)

| Code | HTTP Status | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 422 | Request body or query params failed validation |
| `GROUP_NOT_FOUND` | 404 | Group ID does not exist |
| `MEMBER_NOT_FOUND` | 404 | Member ID does not exist |
| `EXPENSE_NOT_FOUND` | 404 | Expense ID does not exist or is soft-deleted |
| `SETTLEMENT_NOT_FOUND` | 404 | Settlement does not exist or is soft-deleted |
| `INVALID_INVITE_TOKEN` | 404 | Invite token does not match any active group |
| `GROUP_ARCHIVED` | 409 | Action not allowed on archived group |
| `PERMISSION_DENIED` | 403 | Member does not have rights for this action |
| `NO_SESSION` | 401 | No session cookie or bearer token present |
| `SESSION_EXPIRED` | 401 | JWT has expired; client must re-join |
| `SESSION_INVALID` | 401 | JWT signature invalid or malformed |
| `MEMBER_WRONG_GROUP` | 403 | Session token is for a different group |
| `IDEMPOTENCY_CONFLICT` | 409 | Idempotency key reused with different payload |
| `SPLIT_SUM_MISMATCH` | 422 | Expense splits do not sum to total amount |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Unhandled server error (logs contain details) |

---

## 5. Non-Functional Requirements

### Performance

| Requirement | Target | Measurement | Alert Threshold |
|---|---|---|---|
| API p50 latency | < 50ms | Prometheus histogram | > 100ms |
| API p95 latency | < 200ms | Prometheus histogram | > 500ms |
| API p99 latency | < 500ms | Prometheus histogram | > 1,000ms |
| Balance computation | < 200ms p95 | Prometheus histogram | > 400ms |
| Settle-up computation (50 members) | < 100ms p95 | Unit test assertion + Prometheus | > 200ms |
| Settle-up computation (100 members) | < 50ms algorithm | Unit test assertion | > 100ms |
| Page LCP (mobile 4G) | < 2.5s | Core Web Vitals (Lighthouse CI) | > 4s |
| Page TTI | < 3.5s | Core Web Vitals | > 6s |
| DB query p99 | < 50ms | Prometheus + pg_stat_statements | > 100ms |
| Group creation API p95 | < 300ms | Prometheus | > 500ms |
| Expense save API p95 | < 300ms | Prometheus | > 500ms |
| Join API p95 | < 300ms | Prometheus | > 500ms |

### Scalability

**API statelessness:** No in-memory state. Session state is encoded entirely in the JWT cookie (which is signed but stateless — the server reads the cookie on every request without a database lookup, except for revocation which is not needed in MVP). The database is the single source of truth. Multiple API instances can run behind a load balancer without sticky sessions.

**Database connection pooling:**
```
pool_size=5           # per API instance
max_overflow=10       # burst headroom
pool_timeout=30       # seconds to wait for a connection
pool_recycle=1800     # recycle connections every 30 minutes
```
At 3 API instances: max 45 connections. PostgreSQL 16 default: 100. Adequate for 500 concurrent users.

**Polling strategy:** Frontend polls `/api/v1/groups/{id}/balances` every 10 seconds via SWR's `refreshInterval`. At 500 concurrent users viewing group dashboards: ~50 req/second to the balance endpoint. A single FastAPI instance handles ~500 req/second (Techempower benchmarks). No scaling action needed until ~5,000 concurrent polling users.

**Read replica:** Not needed for MVP scale. Add when write latency affects read performance (not expected below 5,000 users).

**Cache strategy:** No application-level cache in MVP. PostgreSQL's shared buffer cache (default 128MB in Docker) handles repeated queries. The balance query is well-indexed and completes in < 5ms. No Redis needed at this scale.

### Availability

| Metric | Prototype Target | Production Target |
|---|---|---|
| Uptime | 95% (Fly.io free tier restarts are acceptable) | 99.5% |
| RTO (Recovery Time Objective) | 30 minutes | 10 minutes |
| RPO (Recovery Point Objective) | 24 hours | 1 hour |

**Failure modes:**
- API instance crash: Fly.io restarts the container automatically. New session cookie on next request handles re-auth transparently.
- Database crash: All API requests fail with 503. Persistent volume retains data. Container restart recovers in < 30 seconds.
- Frontend build failure: Previous build remains served by Vercel (immutable deployments).
- Network partition between API and DB: API returns 503. Client shows "Connection error. Please try again."

**Backup strategy:**
- Local development: `docker compose` volume (no backup needed — dev data)
- Staging: Fly Postgres automatic daily snapshots (free tier). 7-day retention.
- Production: pg_dump to a local file daily; also use Fly Postgres automatic backups if on paid tier.

**Health check endpoint:** `GET /api/v1/health`
- Returns 200 if: database connection is alive (1-query ping), no pending error state.
- Returns 503 if: database unreachable.
- Response body: `{"status": "healthy", "db": "connected", "timestamp": "2026-04-15T14:00:00Z"}`
- Not authenticated. Excluded from rate limiting.

### Reliability

**Transaction scope:**
- Group creation: single transaction (INSERT groups + INSERT members + set cookie).
- Expense creation: single transaction (INSERT expenses + INSERT expense_splits). Idempotency key checked outside the transaction; recorded inside.
- Settlement creation: single transaction.
- Expense deletion (soft): single UPDATE transaction.

**Operations that are eventually consistent:**
- Balance and settle-up views: computed fresh on each request from the database. Any expense logged by another member is visible on the next request (no eventual consistency delay — the read is always from the current state of the DB).

**Retry strategy:**
- Client retries on network failure: SWR's `onErrorRetry` with exponential backoff (1s, 2s, 4s). Maximum 3 retries.
- Server-side: no automatic retries on DB operations. Failures surface as 500 and the client retries.
- Idempotency keys prevent duplicate writes during client retry storms.

**Circuit breaker:** Not applicable at this scale (no external services). If the database is unavailable, all API requests fail fast (< 30s connection timeout) and return 503.

### Security

**Authentication:**
- Token type: JWT (HS256), signed with `SECRET_KEY` env var.
- Payload: `{sub: member_id (UUID), group_id: UUID, is_admin: bool, iat: int, exp: int}`.
- Lifetime: 30 days from issue, rolling (cookie Max-Age reset on each valid request).
- Storage: httpOnly, Secure, SameSite=Lax cookie. Not in localStorage (ITP risk).
- Rotation: tokens are stateless; rotation requires a new join or an admin-reset flow (Phase 2).

**Authorization (RBAC model):**

| Action | Admin | Expense Logger (own) | Any Member |
|---|---|---|---|
| View group, members, balances, settle-up | Yes | Yes | Yes |
| Add expense | Yes | Yes | Yes |
| Edit own expense | Yes | Yes | No |
| Edit any expense | Yes | No | No |
| Delete own expense | Yes | Yes | No |
| Delete any expense | Yes | No | No |
| Record settlement | Yes | Yes | Yes |
| Delete own settlement | Yes | Yes | No |
| Delete any settlement | Yes | No | No |
| Edit group name/description | Yes | No | No |
| Archive/re-open group | Yes | No | No |

Authorization is enforced in the service layer, not just the router. Every service method that mutates data receives `current_member: MemberContext` and checks permissions before executing.

**Input validation:**
- Backend: Pydantic v2 on all request bodies. All string fields are stripped of leading/trailing whitespace. Length limits enforced at Pydantic level, not just DB constraint.
- Frontend: HTML5 validation + React state validation (mirrors backend rules). Frontend validation is UX only; backend is authoritative.
- Amount fields: client sends string decimal (e.g., `"42.50"`); backend converts to integer cents (4250). Amounts larger than 999,999.99 are rejected (max 99,999,999 cents).

**Secrets management:**
- All secrets in environment variables only. Never in code or committed to git.
- Required env vars:
  - `SECRET_KEY` — JWT signing key (minimum 32 characters, random). Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
  - `DATABASE_URL` — PostgreSQL connection string
  - `CORS_ORIGINS` — comma-separated list of allowed frontend origins
- `.env` file is gitignored. `.env.example` is committed with placeholder values.

**HTTPS and security headers (enforced by the reverse proxy / Fly.io):**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'
```

**CORS:** Only the frontend origin is allowed. `CORS_ORIGINS` env var controls this. Credentials are allowed (for cookie-based auth).

**Rate limiting:** Implemented with slowapi at the API level (documented in §4).

**Dependency scanning:** `uv audit` (backend) and `pnpm audit` (frontend) run in CI on every PR. GitHub Dependabot enabled for automated security PRs.

**SQL injection:** Prevented by SQLAlchemy's parameterized queries. No raw string concatenation in any query.

**Group enumeration:** Group IDs are UUIDs (non-sequential). The only way to access a group is via the invite link (which contains the invite_token UUID) or by having a valid session token for that group. Group IDs are not guessable.

### Observability

**Logging — structured JSON to stdout (mandatory):**

Every backend request is logged with:
```json
{
    "timestamp": "2026-04-15T14:00:00.123Z",
    "level": "INFO",
    "request_id": "req_abc123",
    "method": "POST",
    "path": "/api/v1/groups/550e84.../expenses",
    "status": 201,
    "duration_ms": 45,
    "group_id": "550e84...",
    "member_id": "7c9e66...",
    "is_admin": false
}
```

Every error is logged with `exc_info=True`:
```json
{
    "timestamp": "2026-04-15T14:00:01Z",
    "level": "ERROR",
    "request_id": "req_def456",
    "error": "INTERNAL_ERROR",
    "message": "Database connection timeout after 30s",
    "exc_info": "Traceback (most recent call last): ..."
}
```

**What is never logged:** display_name values in PII-sensitive contexts (settlement amounts with names are acceptable since there's no real PII), raw JWT tokens, full cookie values.

**Metrics (Prometheus):**
- `http_requests_total{method, path, status}` — request counter
- `http_request_duration_seconds{method, path}` — latency histogram (buckets: 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
- `db_query_duration_seconds{query_name}` — DB operation latency
- `settle_up_computation_seconds` — algorithm latency histogram
- `active_groups_total` — gauge (updated every 60 seconds from DB)
- `active_members_total` — gauge
- Cardinality limit: `path` label uses parameterized paths (e.g., `/api/v1/groups/{id}/expenses`), never raw UUIDs.

Grafana dashboard provisioned via `src/infra/grafana/dashboards/fairsplit.json` (committed to repo). No manual setup required after `docker compose up`.

**Distributed tracing:** OpenTelemetry SDK installed but spans exported only to console in development. In production: OTLP export to Grafana Tempo (free tier) if needed. Not required at launch scale.

**Alerting rules (Prometheus + Grafana):**
| Alert | Condition | Channel |
|---|---|---|
| High error rate | `error_rate > 5% over 5 minutes` | GitHub issue (logged) |
| High API latency | `p95 > 500ms over 5 minutes` | GitHub issue |
| DB unreachable | `health check 503 for 2 consecutive checks` | Fly.io alert + GitHub issue |

---

## 6. Testing Strategy

| Type | Tool | Coverage Target | Runs In |
|---|---|---|---|
| Unit (backend) | pytest 8.x + pytest-asyncio | 90% line coverage; 100% of settle-up algorithm | Local + CI |
| Unit (frontend) | Vitest 2.x + React Testing Library | 80% line coverage on hooks and utility functions | Local + CI |
| Integration (API) | pytest + httpx (async test client) | All 25+ API endpoints; all error codes | CI |
| E2E | Playwright 1.x | All user flows: create group, join, add expense, settle up, mark paid | CI (nightly) |
| Contract | — (deferred; no external consumers in MVP) | — | — |
| Performance | Locust 2.x | Balance endpoint, settle-up endpoint at 100 concurrent users | Weekly |
| Security | `uv audit` (Python) + `pnpm audit` (Node) | All dependencies | CI (every PR) |
| Algorithm exhaustive | pytest parametrize | Groups of 2–20 members; all circular debt patterns; rounding edge cases | CI |

### Settle-Up Algorithm — Mandatory Test Cases

These test cases must all pass before the settle-up algorithm is considered done. Any failure blocks the PR.

```python
# src/backend/tests/test_settle_algorithm.py

import pytest
from uuid import UUID
from backend.services.settle_service import compute_settle_up

def uuid(n: int) -> UUID:
    return UUID(f"00000000-0000-0000-0000-{n:012d}")

MEMBER_NAMES = {uuid(i): f"Member{i}" for i in range(1, 21)}

@pytest.mark.parametrize("balances, expected_transfers", [
    # Case 1: Two-person group — exactly 1 transfer
    ({uuid(1): 4200, uuid(2): -4200}, 1),

    # Case 2: Three-person circular debt (A→B→C→A each $10) — 2 transfers
    ({uuid(1): 1000, uuid(2): 0, uuid(3): -1000}, 1),  # simplified
    ({uuid(1): 500, uuid(2): 500, uuid(3): -1000}, 2), # two creditors, one debtor

    # Case 3: Four-person group — at most N-1 = 3 transfers
    ({uuid(1): 3000, uuid(2): 1000, uuid(3): -2000, uuid(4): -2000}, 3),

    # Case 4: All balances zero — 0 transfers
    ({uuid(1): 0, uuid(2): 0, uuid(3): 0}, 0),

    # Case 5: Single member — 0 transfers
    ({uuid(1): 0}, 0),

    # Case 6: One creditor, many debtors
    ({uuid(1): 9000, uuid(2): -3000, uuid(3): -3000, uuid(4): -3000}, 3),

    # Case 7: Many creditors, one debtor
    ({uuid(1): 3000, uuid(2): 3000, uuid(3): 3000, uuid(4): -9000}, 3),

    # Case 8: 1-cent balance (edge case — must not be dropped)
    ({uuid(1): 1, uuid(2): -1}, 1),
])
def test_transfer_count(balances, expected_transfers):
    transfers = compute_settle_up(balances, MEMBER_NAMES)
    assert len(transfers) == expected_transfers

def test_all_balances_clear_after_settlement():
    """After applying all transfers, every member's balance should be 0."""
    balances = {uuid(1): 5000, uuid(2): -2000, uuid(3): -3000}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    running = dict(balances)
    for t in transfers:
        running[t.creditor_id] -= t.amount_cents
        running[t.debtor_id]   += t.amount_cents
    assert all(v == 0 for v in running.values())

def test_amounts_are_positive():
    balances = {uuid(1): 4200, uuid(2): -4200}
    transfers = compute_settle_up(balances, MEMBER_NAMES)
    assert all(t.amount_cents > 0 for t in transfers)

def test_at_most_n_minus_1_transfers():
    """Algorithm property: at most N-1 transfers for N members with nonzero balances."""
    balances = {
        uuid(1): 3000, uuid(2): 2000, uuid(3): 1000,
        uuid(4): -2000, uuid(5): -4000
    }
    nonzero_members = sum(1 for v in balances.values() if v != 0)
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) <= nonzero_members - 1

def test_performance_100_members():
    """Algorithm must complete in under 50ms for 100 members."""
    import time
    # Construct 50 creditors and 50 debtors, each with 100 cents
    balances = {}
    for i in range(1, 51):
        balances[uuid(i)] = 100
    for i in range(51, 101):
        balances[uuid(i)] = -100
    start = time.perf_counter()
    compute_settle_up(balances, {uuid(i): f"M{i}" for i in range(1, 101)})
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 50, f"Algorithm took {elapsed_ms:.1f}ms for 100 members"
```

### Test Data Strategy

- **Unit tests:** Factory functions create in-memory objects. No database.
- **Integration tests:** `pytest-asyncio` with a dedicated test database (`fairsplit_test`). Each test function runs in a transaction that is rolled back after the test. No test isolation issues.
- **E2E tests:** Playwright tests run against the full Docker stack. A `seed.py` script populates test data before E2E suite runs.
- **Seed data:** `src/backend/seed.py` creates:
  - 2 groups (one active "Nashville Trip", one archived "Roommates 2025")
  - 3–5 members per group (including one admin)
  - 8–12 expenses per group with all three split types represented
  - 1–2 settlements (to verify balance adjustments)
  - All seeded members land on a populated dashboard (not a blank screen)

---

## 7. Deployment Architecture

### CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CI Pipeline (GitHub Actions — triggered on every PR)                   │
│                                                                         │
│  PR opened                                                              │
│     │                                                                   │
│     ▼                                                                   │
│  [Lint] ruff (Python) + ESLint (TypeScript) — fail fast                │
│     │                                                                   │
│     ▼                                                                   │
│  [Type Check] mypy (Python) + tsc --noEmit (TypeScript)                │
│     │                                                                   │
│     ▼                                                                   │
│  [Unit Tests] pytest (backend) + vitest (frontend) — parallel           │
│     │                                                                   │
│     ▼                                                                   │
│  [Integration Tests] pytest + httpx against test DB (postgres:16-alpine)│
│     │                                                                   │
│     ▼                                                                   │
│  [Security Audit] uv audit + pnpm audit                                 │
│     │                                                                   │
│     ▼                                                                   │
│  [Docker Build] docker build backend + frontend — verify images build   │
│     │                                                                   │
│     ▼                                                                   │
│  [Lighthouse CI] Core Web Vitals check on built frontend                │
│     │                                                                   │
│  PR approved + all checks green → merge to main                        │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  CD Pipeline (GitHub Actions — triggered on merge to main)              │
│                                                                         │
│  merge to main                                                          │
│     │                                                                   │
│     ▼                                                                   │
│  [Run Migrations] alembic upgrade head (against staging DB)            │
│     │                                                                   │
│     ▼                                                                   │
│  [Deploy Backend] fly deploy (Fly.io — zero-downtime rolling deploy)   │
│     │                                                                   │
│     ▼                                                                   │
│  [Deploy Frontend] vercel deploy --prod (Vercel — atomic deploy)       │
│     │                                                                   │
│     ▼                                                                   │
│  [Smoke Tests] curl /api/v1/health + Playwright login smoke test       │
│     │                                                                   │
│     ├── PASS → done                                                     │
│     └── FAIL → alert + automatic rollback (fly rollback)               │
└─────────────────────────────────────────────────────────────────────────┘
```

### Environments

| Environment | Purpose | Backend URL | Frontend URL | Database | Secrets Source |
|---|---|---|---|---|---|
| Local (docker compose) | Development | http://localhost:8000 | http://localhost:3000 | postgres:16-alpine container | `.env` file (gitignored) |
| CI | Test | http://localhost:8000 (ephemeral) | N/A (build only) | postgres:16-alpine service container | GitHub Actions secrets |
| Staging | Pre-production validation | https://fairsplit-api.fly.dev | https://fairsplit.vercel.app | Fly Postgres (free) | Fly.io secrets |
| Production | Live | https://api.fairsplit.app | https://fairsplit.app | Fly Postgres or self-hosted PostgreSQL | Fly.io secrets or VPS env file |

### Docker Compose Configuration

```yaml
# docker-compose.yml (local development — zero external dependencies)
version: "3.9"
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: fairsplit
      POSTGRES_USER: fairsplit
      POSTGRES_PASSWORD: fairsplit_dev
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fairsplit -d fairsplit"]
      interval: 5s
      timeout: 5s
      retries: 5

  migrate:
    build:
      context: ./src/backend
      dockerfile: Dockerfile
    command: alembic upgrade head
    environment:
      DATABASE_URL: postgresql+asyncpg://fairsplit:fairsplit_dev@db:5432/fairsplit
    depends_on:
      db:
        condition: service_healthy

  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile
    restart: unless-stopped
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      DATABASE_URL: postgresql+asyncpg://fairsplit:fairsplit_dev@db:5432/fairsplit
      SECRET_KEY: dev_secret_key_minimum_32_characters_change_in_prod
      CORS_ORIGINS: http://localhost:3000
      ENVIRONMENT: development
    ports:
      - "8000:8000"
    volumes:
      - ./src/backend:/app
    depends_on:
      migrate:
        condition: service_completed_successfully

  frontend:
    build:
      context: ./src/frontend
      dockerfile: Dockerfile
      args:
        NEXT_PUBLIC_API_URL: http://localhost:8000
        NEXT_PUBLIC_SHOW_DEV_PANEL: "true"
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    volumes:
      - ./src/infra/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:11-alpine
    restart: unless-stopped
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_AUTH_ANONYMOUS_ENABLED: "true"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./src/infra/grafana/provisioning:/etc/grafana/provisioning
    ports:
      - "3001:3000"
    depends_on:
      - prometheus

volumes:
  postgres_data:
  grafana_data:
```

### Deployment Strategy

**Staging/Production:** Fly.io rolling deployment. Fly deploys one new instance at a time. Health check (`GET /api/v1/health`) must return 200 before the old instance is terminated. Rollback: `flyctl releases rollback` reverts to the previous image.

**Database migrations:** Run before the new application version starts (handled by the `migrate` step in the CD pipeline). All migrations must be backward-compatible with the previous application version (additive-only: no column drops, no column renames in a single migration). Breaking schema changes require a 2-phase migration: add-then-remove.

### Infrastructure as Code

```
src/infra/
├── fly.toml                     — Fly.io app configuration (backend)
├── prometheus/
│   └── prometheus.yml           — Prometheus scrape config
└── grafana/
    ├── provisioning/
    │   ├── datasources/
    │   │   └── prometheus.yml   — Auto-provision Prometheus datasource
    │   └── dashboards/
    │       └── fairsplit.yml    — Dashboard provider config
    └── dashboards/
        └── fairsplit.json       — Pre-built FairSplit Grafana dashboard
```

---

## 8. Cost Analysis

### Local Docker Stack

$0/month. All containers run locally: PostgreSQL, FastAPI, Next.js, Prometheus, Grafana. No accounts required. `docker compose up` is the complete setup command.

### Staging (Free Tier)

| Service | Provider | Monthly Cost | Limit |
|---|---|---|---|
| Backend API | Fly.io free tier | $0 | 3 shared VMs (256MB RAM each), 160GB bandwidth |
| Frontend | Vercel free tier | $0 | 100GB bandwidth, unlimited deploys |
| Database | Fly Postgres (free) | $0 | 1 shared VM, 1GB storage |
| CI/CD | GitHub Actions | $0 | 2,000 minutes/month (public repo: unlimited) |
| Monitoring | Grafana Cloud free | $0 | 10K metrics, 50GB logs |
| Error tracking | Sentry free | $0 | 5,000 events/month |
| **Total** | | **$0** | |

### Break-Even Analysis (Self-Hosting vs. VPS)

A $6/month VPS (Hetzner CX11 or equivalent) handles:
- PostgreSQL 16 + FastAPI + Nginx = ~300MB RAM total
- ~500 concurrent users comfortably
- Unlimited bandwidth (Hetzner: 20TB/month)
- No per-seat or per-request limits

Break-even point: when Fly.io free tier (3 VMs, 256MB each) is insufficient, which occurs at approximately **500 concurrent users** during peak usage or when Fly.io ends the free tier. A VPS is the correct move when the demo instance gets sustained real traffic.

### Production Cost Estimates

| User Count | Architecture | Monthly Cost |
|---|---|---|
| 1,000 users | Single Fly.io hobby plan ($5/month) + Fly Postgres ($0 free) + Vercel free | ~$5–10 |
| 10,000 users | Fly.io 2x shared-cpu-1x ($14/month) + Fly Postgres shared ($15/month) + Vercel pro | ~$40–60 |
| 100,000 users | 3x Fly.io performance-1x ($57/month each) + Fly Postgres dedicated ($35/month) + Cloudflare CDN (free) | ~$220–280 |

Note: "100,000 users" means 100K registered groups/members — not necessarily concurrent. Concurrent load at 100K users (typical 5% active at peak): ~5,000 concurrent users. A single PostgreSQL instance with connection pooling (PgBouncer at that scale) handles this.

---

## 9. Migration & Evolution Path

### Prototype → Production

What stays the same:
- Core data model (groups, members, expenses, splits, settlements)
- API contract (`/api/v1/`)
- Authentication approach (httpOnly cookie JWT)
- Settle-up algorithm

What changes:
- `docker compose` → Fly.io + Vercel (or a VPS with Coolify/Dokku for full self-hosting)
- Dev-mode reload (`--reload`) → production workers (`gunicorn -w 4 -k uvicorn.workers.UvicornWorker`)
- `SECRET_KEY` rotated to a production value (32+ random bytes)
- Prometheus data retention increased from 15 days to 90 days

### Scale Milestones

| User Count | Trigger | Action |
|---|---|---|
| 500 concurrent | Fly.io free tier RAM limit | Move to $5–10/month Fly.io hobby plan |
| 2,000 active groups | PostgreSQL connection pool saturation | Add PgBouncer (connection pooler) in front of PostgreSQL |
| 5,000 concurrent | API latency p95 > 300ms | Add second API instance behind Fly.io load balancer |
| 10,000 active groups | Write latency affecting reads | Add PostgreSQL read replica (Fly.io: `fly pg attach` secondary) |
| 50,000 members | Balance query > 100ms p95 | Materialize balance table (cached per group, invalidated on expense mutation) |

### Data Migration Strategy

All schema changes follow the expand-contract pattern:

**Phase 1 (expand):** Add new column/table as nullable. Deploy new application version. Both old and new code work.

**Phase 2 (migrate):** Backfill existing rows in a background job. Verify completion.

**Phase 3 (contract):** Add NOT NULL constraint (if needed). Deploy. Remove compatibility shim.

Example: Adding `emoji` to the groups table:
1. `ALTER TABLE groups ADD COLUMN emoji VARCHAR(4);` — nullable, no downtime.
2. Backfill: `UPDATE groups SET emoji = '🤝' WHERE emoji IS NULL;`
3. `ALTER TABLE groups ALTER COLUMN emoji SET DEFAULT '🤝';` — done.

Breaking change example (renaming `display_name` to `name`):
1. `ALTER TABLE members ADD COLUMN name VARCHAR(40);`
2. `UPDATE members SET name = display_name;`
3. Deploy new code that writes to both `name` and `display_name`.
4. Deploy code that reads `name`.
5. Drop `display_name` (next release).

---

## 10. Architecture Decision Records (ADRs)

### ADR-001: httpOnly Cookie as Primary Session Store (not localStorage)

**Status:** Accepted

**Context:**  
Anonymous members (no email, no password) need a 30-day persistent session across browser visits. The PRD initially specified localStorage as the primary store. Safari's Intelligent Tracking Prevention (ITP) clears localStorage after 7 days of inactivity — confirmed by WebKit documentation and current browser behavior. This is a product-critical risk: if a member's session disappears after 7 days, they see the join screen again and perceive their data as lost.

**Decision:**  
Use a server-set `httpOnly`, `Secure`, `SameSite=Lax` cookie as the primary session store. The server issues this cookie on group creation and on group join. The cookie carries the signed JWT. localStorage is used only as an in-tab cache (token is copied from cookie to localStorage on page load for use by client-side code that needs the token without a server round-trip) but is not the authoritative store.

**Alternatives Considered:**  
- localStorage primary: Fails on Safari ITP after 7 days. Rejected.
- sessionStorage: Cleared when the browser tab closes. Unacceptable for 30-day persistence. Rejected.
- Server-side session (database row per session): More complex, requires session cleanup job, no benefit at this scale. Rejected.

**Consequences:**  
- Cookie is not accessible to JavaScript (`httpOnly`) — XSS cannot steal it. This is a security improvement.
- `SameSite=Lax` allows cookie to be sent on top-level navigations (clicking a link) but not on cross-site subresource requests — prevents CSRF.
- Cross-device session recovery remains impossible (by design, per PRD). A user on a new device must rejoin.
- The frontend still has access to session data (group_id, member_id) via the response body on join — stored in localStorage as read cache. If localStorage is cleared, the API call still works because the cookie is present.

---

### ADR-002: Greedy Max-Heap Algorithm for Minimum-Transfer Settle-Up

**Status:** Accepted

**Context:**  
The settle-up feature requires computing the minimum number of transfers to clear all debts. The general problem is NP-Complete (reducible from Sum of Subsets). The PRD mandates that the algorithm be "the minimum-transfer plan" and be exhaustively unit-tested.

**Decision:**  
Implement the greedy max-heap heuristic: at each step, match the largest creditor with the largest debtor. This is O(n log n) and produces the exact minimum for almost all practical group configurations (n ≤ 20 members). It is not provably optimal for all inputs, but for groups of 3–12 members (the typical case), it always finds the true minimum. The PRD assumption P11 explicitly documents this: "true minimum for n ≤ 20, approximately optimal for n ≤ 100."

**Alternatives Considered:**  
- Exact NP algorithm: Exponential time. Impractical for groups > 20. Rejected.
- Maximum-flow algorithm: O(V²E²). Produces provably optimal results but is significantly more complex to implement correctly and test. The marginal correctness gain over the greedy approach for groups of < 100 members does not justify the complexity. Rejected for MVP; noted as a Phase 2 upgrade path.
- Pre-computed cache: Store settle-up results and invalidate on expense changes. Adds cache invalidation complexity with no latency benefit (greedy runs in < 10ms for typical groups). Rejected.

**Consequences:**  
- The settle-up plan may not be provably optimal for groups > 20 members with highly specific balance distributions. This is documented in the FAQ.
- Exhaustive unit tests covering all patterns for groups up to 20 members provide high confidence in correctness for the target use case.
- The algorithm runs synchronously on each settle-up request (not cached), ensuring the result always reflects current balances.

---

### ADR-003: Offset Pagination for Expense List (not Cursor-Based)

**Status:** Accepted

**Context:**  
The expense list needs pagination. Two common strategies: offset (page/per_page) and cursor (keyset, using last_id as a bookmark).

**Decision:**  
Use offset pagination for MVP. The target maximum expense count per group is 200 (per PRD). At 200 items and 20 per page, this is 10 pages. Offset pagination is simple to implement, simple to understand, and adequate for this scale.

**Alternatives Considered:**  
- Cursor-based (keyset) pagination: Better performance at scale (no `OFFSET` scan), stable under concurrent inserts. The correct choice at 10,000+ items. Not needed for groups of 50–200 expenses. Deferred to Phase 2 (add when a group exceeds 1,000 expenses). Rejected for MVP.

**Consequences:**  
- If an expense is added while a user is paginating (concurrent insert), the offset-paginated list may show a duplicate item or miss an item. Acceptable at this scale and use case (this is a trip expense tracker, not a high-frequency ledger).
- Page 3 of 10 pages at 20 per page requires OFFSET 40 — negligible performance impact.
- Migration to cursor pagination in Phase 2 requires an API version bump (response shape changes) or an additional endpoint.

---

### ADR-004: Compute Balances at Read Time (not Write Time)

**Status:** Accepted

**Context:**  
Two strategies: (a) compute net balances on every read request from raw expense data, or (b) maintain a pre-computed balances table updated on every expense write.

**Decision:**  
Compute balances at read time. The SQL query that computes net balances (see §3 Query 1) is efficient with the defined indexes. For 200 expenses and 20 members, the query completes in < 5ms. The complexity of cache invalidation on pre-computed balances (invalidate on expense create, edit, soft-delete, settlement create, settlement delete) is not justified at this scale.

**Alternatives Considered:**  
- Pre-computed balance table: Faster reads, but requires transactional update on every mutation. Risk of stale data if any mutation path misses the invalidation. Testing complexity is higher. Deferred to Phase 2 if balance query latency becomes a bottleneck. Rejected for MVP.
- Redis cache: No Redis in the stack (zero external dependencies). Rejected.

**Consequences:**  
- Balance computation adds 5–20ms to every balance API request. Acceptable given the < 200ms p95 target.
- No risk of stale balances — every read reflects the current state of the database.
- Adding a `members.balance_cents` column later (as a denormalization for performance) requires a 2-phase migration and careful invalidation logic.

---

### ADR-005: PyJWT over python-jose for JWT Signing

**Status:** Accepted

**Context:**  
FastAPI's tutorial originally recommended `python-jose` for JWT signing. In 2021–2023, `python-jose` became effectively abandoned (no releases, Python 3.10+ compatibility issues). FastAPI's official documentation was updated in 2024 to recommend PyJWT instead.

**Decision:**  
Use PyJWT 2.10.x with HS256 algorithm. PyJWT is actively maintained, is the official FastAPI recommendation, and has no known critical security advisories as of April 2026.

**Alternatives Considered:**  
- python-jose: Abandoned since 2021. GitHub discussions in the FastAPI repo explicitly recommend migrating. Rejected.
- authlib: Full OAuth/OIDC library. Overkill for simple JWT signing in an anonymous session context. Rejected.
- Custom JWT implementation: Security anti-pattern. Rejected.

**Consequences:**  
- PyJWT's API is slightly different from python-jose (import path, method names). Engineers must use `jwt.encode()` and `jwt.decode()` from `import jwt` (not `from jose import jwt`).
- HS256 (symmetric) is appropriate for this use case — the same server that issues tokens also validates them. No asymmetric key infrastructure needed.

---

### ADR-006: No WebSockets — Polling at 10-Second Interval

**Status:** Accepted

**Context:**  
Balance views need to update when other members add expenses. Two options: server-sent events/WebSockets (push) or HTTP polling (pull).

**Decision:**  
Use HTTP polling at 10-second intervals via SWR's `refreshInterval`. Balance and expense list endpoints return fresh data on every poll. No WebSocket infrastructure needed.

**Alternatives Considered:**  
- WebSockets: Real-time push updates. Requires persistent connection management, reconnection logic, and a different server configuration (Fly.io handles WebSockets, but adds complexity). The latency benefit (0ms vs. up to 10 seconds) is not meaningful for the use case: groups are not co-editing in real time. Rejected for MVP; noted as a Phase 2 option if user complaints exceed 5% of active groups.
- Server-Sent Events (SSE): Simpler than WebSockets, unidirectional. FastAPI 0.135+ has native SSE support. Still requires persistent connection management. Rejected for MVP; preferred over WebSockets if push is ever needed.

**Consequences:**  
- Worst-case stale balance: 10 seconds. Acceptable for the use case.
- Server load from polling: At 500 concurrent dashboard viewers polling every 10 seconds = 50 req/sec to the balance endpoint. Well within single-instance capacity.
- The balance endpoint must be fast (< 50ms p95) to handle this polling load without a significant CPU spike.

---

### ADR-007: Idempotency Keys for Mutation Endpoints

**Status:** Accepted

**Context:**  
Mobile users on unreliable connections may retry a form submission after a timeout. Without idempotency protection, this creates duplicate expenses or duplicate groups.

**Decision:**  
The client generates a UUID when a form is opened (not on submit — so retries use the same key). This UUID is sent in `X-Idempotency-Key` on the first submission and all retries. The server checks the `idempotency_keys` table before processing; if the key exists and is not expired (24 hours), returns the stored response without re-processing.

**Alternatives Considered:**  
- Database-level unique constraints: Would prevent the duplicate write but would return a 409 error to the client, requiring the client to handle this case specially. The idempotency key approach returns the original 201 response, which is transparent to the client. Rejected as the primary mechanism.
- No idempotency: Accept duplicate expenses as a user problem. Rejected — the PRD explicitly requires protection against double-submit.

**Consequences:**  
- `idempotency_keys` table grows over time. A cleanup job (or TTL via `expires_at` column + periodic `DELETE WHERE expires_at < NOW()`) is required.
- The 24-hour window means a retry storm lasting more than 24 hours would create duplicates. Acceptable — 24 hours is well beyond any expected retry scenario.

---

## 11. Open Technical Questions

| Question | Owner | Due Date | Impact |
|---|---|---|---|
| Should the group invite link be permanent or expirable? Permanent is simpler; expirable adds security (prevents old links from being shared publicly). Current decision: permanent for MVP. | Product + Engineering | Before launch | Low — can be added later without breaking the data model (add `invite_token_expires_at` column) |
| Should non-members (link-openers who have not joined) be able to view the expense list in read-only mode? Privacy argument against; viral argument for. Current decision: show group name + member count only; require join to see expenses. | Product | Before design handoff | Medium — affects the join page UX design |
| At what group size should the settle-up algorithm print a disclaimer that the result may not be provably optimal? The greedy approach produces the true minimum for n ≤ 20 in all tested cases. | Engineering | During algorithm implementation | Low — text change only |
| What is the maximum number of members per group? No cap in MVP (per PRD). At 100+ members, the join page becomes unwieldy. Consider adding a soft cap at 50 with an admin override. | Product | Phase 2 | Low for MVP |
| Multi-currency settle-up: when a group has expenses in multiple currencies, each currency settles independently. Should the settle-up page show multiple sections (one per currency) or require the user to select a currency? | Product | Phase 2 | Medium — affects API response shape for multi-currency groups |

---

*End of Technical Specification*
