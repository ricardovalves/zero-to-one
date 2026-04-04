Kick off the development pipeline. Coordinates engineering agents with maximum parallelism.

Agents communicate only through the filesystem. Foundation phase is always sequential (DB → then parallel). Feature development runs backend + frontend + infra in parallel.

Usage: /build <project-name> [feature-name]

Arguments: $ARGUMENTS

---

## Orchestration Rules

- Agents NEVER talk to each other — all through `workspace/{project}/`
- Foundation runs in a specific order (each step unblocks the next)
- Feature development: backend + frontend + infra/db run in PARALLEL per feature
- Every PR from agents goes through `/review-pr` before merging

---

## Pipeline

### STEP 1: Parse arguments + verify prerequisites

Parse: first word = {project}, rest = {feature} (if empty, build full MVP).

Required files — if any missing, tell user which command to run:
- `workspace/{project}/technical-spec.md` → need `/architect {project}`
- `workspace/{project}/api-spec.yaml` → need `/architect {project}`
- `workspace/{project}/design-spec.md` → need `/design {project}`
- `workspace/{project}/prototype/index.html` → need `/design {project}`

Read `workspace/{project}/handoffs/cto-architect.md` and `workspace/{project}/handoffs/ux-designer.md`.

### STEP 2: Project Management (if roadmap doesn't exist)

If `workspace/{project}/roadmap.md` doesn't exist:
**Launch:** `project-manager` — reads handoffs, writes roadmap + Linear issues.
Wait for completion.

### GATE 2: Plan & Milestones — MANDATORY STOP

Read `workspace/{project}/roadmap.md`. Present the execution plan to the user before launching any engineering agents:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EXECUTION PLAN — {project}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stack:    {frontend} + {backend} + {database}
Auth:     {strategy}
Hosting:  docker compose up (local first)

Milestones
  Sprint 0  Foundation      {start}–{end}   {N} pts
  Sprint 1  {goal}          {start}–{end}   {N} pts
  Sprint 2  {goal}          {start}–{end}   {N} pts
  ...

Epics & Tasks
  Epic 1: {name}
    [ ] {task} — {agent} — {estimate}
    [ ] {task} — {agent} — {estimate}
  Epic 2: {name}
    [ ] {task} — {agent} — {estimate}
    ...

Linear: {N} issues will be created if LINEAR_API_KEY is set.
Full roadmap: workspace/{project}/roadmap.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ready to start implementation? (yes / no / adjust scope)
```

Wait for explicit user confirmation. If the user adjusts scope, update `workspace/{project}/roadmap.md` before proceeding.

---

### STEP 3: Foundation Phase (always Sprint 1)

Foundation runs in this ORDER (each step produces files the next step needs):

**3a — PARALLEL: DB schema + Infra skeleton**

Launch simultaneously:
| Agent | Writes |
|---|---|
| `db-engineer` | `src/backend/migrations/`, `SCHEMA.md` |
| `infra-engineer` | `src/docker-compose.yml`, `src/backend/Dockerfile`, `src/frontend/Dockerfile`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml` |

Wait for both.

**3b — PARALLEL: Backend skeleton + Frontend skeleton** (depends on 3a)

Launch simultaneously:
| Agent | Writes |
|---|---|
| `backend-engineer` | `src/backend/app/` — FastAPI init, config, database, auth skeleton, security headers, rate limiting, health endpoint |
| `frontend-engineer` | `src/frontend/` — Next.js App Router, layout, auth pages, API client, PostHog initialization |

Wait for both.

**3c — PARALLEL: Billing + Email infrastructure** (depends on 3b — needs User model and auth skeleton)

Launch simultaneously:
| Agent | Writes |
|---|---|
| `stripe-engineer` | `src/backend/app/models/billing.py`, `src/backend/app/routers/billing.py`, `src/backend/app/services/billing_service.py`, `src/backend/app/dependencies/billing.py`, `src/frontend/src/components/PricingTable.tsx`, `src/frontend/src/hooks/useBilling.ts` |
| `email-engineer` | `src/backend/app/email/` — service, templates, tasks, providers; adds email_verified fields to User; adds Mailpit to docker-compose |

Wait for both. These can be omitted if the project has no billing or email requirements — but both are required for any product that will be used by real customers.

### STEP 4: Feature Development (per sprint or per {feature} arg)

For each feature in scope from the roadmap (or the specified {feature}):

**Launch simultaneously:**
| Agent | Writes |
|---|---|
| `backend-engineer` | API endpoints for this feature |
| `frontend-engineer` | UI pages + components for this feature |
| `db-engineer` | Additional migration if schema changes needed |

Wait for all three. Then:
- `backend-engineer` opens a PR → `/review-pr <pr-url>`
- `frontend-engineer` opens a PR → `/review-pr <pr-url>`

### STEP 5: Execution Report

Append to `workspace/{project}/execution-report.md`:

```markdown
# Build Phase — Execution Report

**Pipeline:** /build {feature or "MVP foundation"}
**Completed:** {datetime}

## What Was Built

| Component | Location | Status |
|---|---|---|
| Database schema | `src/backend/migrations/` | {✓ / ✗} |
| Backend API | `src/backend/app/` | {✓ / ✗} |
| Frontend app | `src/frontend/` | {✓ / ✗} |
| Docker Compose | `src/docker-compose.yml` | {✓ / ✗} |
| CI/CD pipeline | `.github/workflows/` | {✓ / ✗} |

## Run Locally

```bash
cd workspace/{project}/src
docker-compose up
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

## PRs Created

| PR | Verdict |
|---|---|
| {pr-url} | {APPROVED / BLOCKED} |

## Next Steps

- Open PR review: `/review-pr <url>`
- Plan next sprint: `/sprint {project}`
- Security audit: `/security-scan {project}`
```

### STEP 5b: Generate src/CLAUDE.md

After the foundation and feature builds complete, write `workspace/{project}/src/CLAUDE.md`. This gives Claude developer context when working in the src/ directory — it inherits from the root CLAUDE.md and the project CLAUDE.md automatically.

Read `seed.py` output (or the seed.py file itself) to get the actual emails, passwords, and roles. Read `workspace/{project}/technical-spec.md` for enum values. Populate every field from actual generated content — no placeholders.

```markdown
# {Product Name} — Developer Context

> Auto-generated by the /build pipeline.
> See `workspace/{project}/CLAUDE.md` for product context and architecture decisions.

## Run Locally

```bash
cd workspace/{project}/src
docker compose up
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Seed Accounts

Run `docker compose exec backend python seed.py` to populate development data.

| Email | Password | Role |
|---|---|---|
| {email from seed.py} | {password from seed.py} | {role} |

## Source Layout

```
src/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app + router registration
│   │   ├── config.py        # Settings (Pydantic BaseSettings)
│   │   ├── database.py      # Async SQLAlchemy engine + session
│   │   ├── models/          # SQLAlchemy ORM models (one file per entity)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── routers/         # API route handlers (one file per resource)
│   │   └── services/        # Business logic layer
│   ├── migrations/          # Alembic migrations
│   └── seed.py              # Dev data seeder (idempotent — safe to re-run)
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js App Router pages
│   │   ├── components/      # Reusable UI components
│   │   ├── hooks/           # Data-fetching hooks (one per resource)
│   │   ├── store/           # Zustand state stores
│   │   └── lib/api.ts       # Axios client with auth interceptor
│   └── Dockerfile
└── docker-compose.yml
```

## Status Enums (critical — never invent new values)

{List every Literal type from schemas/*.py, exactly as defined in code:}
- `{ModelName}Status`: `{value1}` | `{value2}` | `{value3}`
- `{ModelName}Role`: `{value1}` | `{value2}`

## Critical Patterns

**Scope auto-resolution** — workspace/tenant ID is resolved server-side from the auth token. Never require clients to send it as a query param or body field.

**Refresh token** — stored in Zustand (in-memory), sent in the request body when calling `/api/v1/auth/refresh`. Not just the Authorization header.

**Cookie security** — `secure=False` in development (HTTP localhost), `secure=True` in production. Gated on `settings.ENVIRONMENT`, never on `NODE_ENV`.

**Dev login panel** — shown when `NEXT_PUBLIC_SHOW_DEV_PANEL=true` (set in docker-compose as a build arg). Emails and passwords must match `seed.py` exactly.

**ORM alias** — When a SQLAlchemy relationship name differs from the API field name, use `AliasChoices` in the Pydantic schema and `populate_by_name=True` in `model_config`.

**Empty collections** — API endpoints return `200 + []` when a resource doesn't exist yet, never `404`. New users must see an onboarding/empty state, not an error.
```

---

### STEP 5c: Post-Build Smoke Tests

After the execution report, run these integration checks against the live stack. They catch the class of bugs that unit tests miss: schema mismatches, broken auth flows, silent empty responses, and new-user dead ends.

**Read the seed script's printed output** to get the actual emails, passwords, and API endpoints before running — do not assume credentials or routes.

```bash
BASE="http://localhost:8000/api/v1"

# 1. Seed loads cleanly (idempotent — safe to re-run)
docker compose exec backend python seed.py

# 2. Login — verify token is at the TOP LEVEL of the response body (not nested in {data: ...})
LOGIN_RESP=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"<seed email>","password":"<seed password>"}')
echo "Login status: $(echo $LOGIN_RESP | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'access_token' in d else 'FAIL — access_token not at top level, got: ' + str(list(d.keys())))")"

# 3. Obtain a token for subsequent checks
#    Note: response.data IS the body — access_token is at the top level, never nested
TOKEN=$(echo $LOGIN_RESP | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 4. Every authenticated endpoint must return 200 (never 422 or 500)
for EP in /dashboard/summary /billing/subscription; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE$EP" -H "Authorization: Bearer $TOKEN")
  echo "GET $EP → $STATUS"  # must be 200
done

# 5. Verify response FIELD NAMES match what the frontend hooks expect
#    This catches backend/frontend contract drift before the browser does
echo "--- Dashboard field check ---"
curl -s "$BASE/dashboard/summary" -H "Authorization: Bearer $TOKEN" | \
  python3 -c "
import sys, json
d = json.load(sys.stdin)
required = ['gross_income_cents', 'after_tax_income_cents', 'waterfall', 'client_contributions', 'quarterly_estimate_cents']
missing = [f for f in required if f not in d]
print('PASS' if not missing else 'FAIL — missing fields: ' + str(missing))
"

echo "--- List response shape check (must have data[], total, page, per_page) ---"
curl -s "$BASE/<primary_list_endpoint>" -H "Authorization: Bearer $TOKEN" | \
  python3 -c "
import sys, json
d = json.load(sys.stdin)
required = ['data', 'total', 'page', 'per_page']
missing = [f for f in required if f not in d]
print('PASS' if not missing else 'FAIL — missing fields: ' + str(missing))
print('data is array:', isinstance(d.get('data'), list))
"

# 6. Seeded users must have seeded data — empty dashboard for a seeded user is a seed failure
echo "--- Seeded data check ---"
curl -s "$BASE/dashboard/summary" -H "Authorization: Bearer $TOKEN" | \
  python3 -c "
import sys, json
d = json.load(sys.stdin)
print('gross_income_cents:', d.get('gross_income_cents'), '(should be > 0 for seeded users)')
"

# 7. Frontend responds
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
echo "Frontend → $STATUS"  # must be 200 or 307
```

**Interpreting failures:**
- `FAIL — access_token not at top level` → auth response is wrapped in `{data: ...}`; remove the wrapper from the auth router or fix the hook to not add `.data` twice
- `FAIL — missing fields` → backend schema field names don't match what the frontend hook expects; compare `api-spec.yaml` → backend response schema → frontend hook destructuring — find where the name drifted
- `422` on a list endpoint → scope auto-resolution is broken; the endpoint is requiring an ID the client doesn't have
- `500` on any endpoint → likely a Pydantic schema mismatch or Python async gotcha; check backend logs with `docker compose logs backend --tail=50`
- `gross_income_cents: 0` for a seeded user → seed didn't commit income entries, or RLS is blocking the query
- Empty `data: []` for a seeded user → seed status values don't match the schema enum `Literal` types

### STEP 6: Summary

```
/build complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project: {project}
Built:   {feature or "Foundation"}

To run:
  cd workspace/{project}/src && docker-compose up
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
