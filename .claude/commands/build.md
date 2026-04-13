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

### STEP 5c: Post-Build Smoke Tests (mandatory — do not skip, do not hand off until passing)

After the execution report, bring up the stack and run these checks against the live system. They catch the class of bugs that unit tests miss: broken auth flows, silent empty responses, schema drift, and seed failures. **Do not present the build as complete until all checks pass.**

#### 5c-i — Start the stack and wait for health

```bash
cd workspace/{project}/src

# Start in background
docker compose up -d

# Wait for backend to be healthy (max 60 seconds)
for i in $(seq 1 12); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
  if [ "$STATUS" = "200" ]; then echo "Backend healthy"; break; fi
  echo "Waiting for backend... ($i/12)"; sleep 5
done

# Wait for frontend to be healthy (max 60 seconds)
for i in $(seq 1 12); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
  if [ "$STATUS" = "200" ] || [ "$STATUS" = "307" ]; then echo "Frontend healthy"; break; fi
  echo "Waiting for frontend... ($i/12)"; sleep 5
done
```

#### 5c-ii — Seed the database

```bash
# Run seed (idempotent — safe to re-run)
docker compose exec backend python seed.py
```

Read the seed.py file at `workspace/{project}/src/backend/seed.py` to extract the actual test email and password. Do not hardcode them — they vary per project. Use the first admin or owner account.

#### 5c-iii — Run generic smoke tests

```bash
BASE="http://localhost:8000/api/v1"
SEED_EMAIL="<email read from seed.py>"
SEED_PASSWORD="<password read from seed.py>"
PASS=0; FAIL=0

# ── TEST 1: Login ──────────────────────────────────────────────────────────────
echo "=== TEST 1: Login ==="
LOGIN_RESP=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d "{\"email\":\"$SEED_EMAIL\",\"password\":\"$SEED_PASSWORD\"}")

python3 - <<'EOF'
import json, sys, os
resp = os.environ.get('LOGIN_RESP', '')
try:
    d = json.loads(resp)
except Exception:
    print("FAIL — login response is not valid JSON:", resp[:200])
    sys.exit(1)
if 'access_token' not in d:
    print("FAIL — access_token missing from login response. Got keys:", list(d.keys()))
    sys.exit(1)
if not d['access_token']:
    print("FAIL — access_token is empty")
    sys.exit(1)
print("PASS — login returns access_token at top level")
EOF
LOGIN_RESP="$LOGIN_RESP" python3 -c "
import json, sys, os
d = json.loads(os.environ['LOGIN_RESP'])
if 'access_token' in d and d['access_token']:
    print('PASS'); sys.exit(0)
else:
    print('FAIL'); sys.exit(1)
" && PASS=$((PASS+1)) || FAIL=$((FAIL+1))

TOKEN=$(echo "$LOGIN_RESP" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('access_token',''))" 2>/dev/null)

# ── TEST 2: Frontend loads ─────────────────────────────────────────────────────
echo "=== TEST 2: Frontend loads ==="
FE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [[ "$FE_STATUS" == "200" || "$FE_STATUS" == "307" ]]; then
  echo "PASS — frontend responds HTTP $FE_STATUS"; PASS=$((PASS+1))
else
  echo "FAIL — frontend returned HTTP $FE_STATUS"; FAIL=$((FAIL+1))
fi

# ── TEST 3: Authenticated endpoints return 200 (not 422 or 500) ───────────────
echo "=== TEST 3: Authenticated GET endpoints ==="
# Extract GET paths from api-spec.yaml (paths with get: operations)
GET_PATHS=$(python3 -c "
import yaml, sys
try:
    spec = yaml.safe_load(open('../../api-spec.yaml'))
    paths = [p for p,v in spec.get('paths',{}).items() if 'get' in v and '{' not in p]
    print('\n'.join(paths[:10]))  # test first 10 non-parameterized GET paths
except Exception as e:
    print('', file=sys.stderr)
" 2>/dev/null)

if [ -n "$GET_PATHS" ] && [ -n "$TOKEN" ]; then
  while IFS= read -r EP; do
    [ -z "$EP" ] && continue
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE$EP" -H "Authorization: Bearer $TOKEN")
    if [[ "$STATUS" == "200" || "$STATUS" == "201" || "$STATUS" == "204" ]]; then
      echo "PASS — GET $EP → $STATUS"; PASS=$((PASS+1))
    else
      echo "FAIL — GET $EP → $STATUS (expected 200)"; FAIL=$((FAIL+1))
      if [[ "$STATUS" == "500" ]]; then
        echo "  → Check backend logs: docker compose logs backend --tail=30"
      elif [[ "$STATUS" == "422" ]]; then
        echo "  → Scope auto-resolution broken: endpoint requires param the frontend cannot provide"
      fi
    fi
  done <<< "$GET_PATHS"
fi

# ── TEST 4: Seeded users have seeded data (not empty after login) ──────────────
echo "=== TEST 4: Seeded data present ==="
# Find collection endpoints (those that should return paginated lists)
LIST_PATHS=$(python3 -c "
import yaml, sys
try:
    spec = yaml.safe_load(open('../../api-spec.yaml'))
    # Look for endpoints whose response schema has a 'data' array property
    candidates = []
    for path, methods in spec.get('paths', {}).items():
        if 'get' not in methods or '{' in path: continue
        resp = methods['get'].get('responses', {}).get('200', {})
        schema = resp.get('content', {}).get('application/json', {}).get('schema', {})
        props = schema.get('properties', {})
        if 'data' in props or 'items' in props or path.endswith('s'):
            candidates.append(path)
    print('\n'.join(candidates[:5]))
except Exception:
    pass
" 2>/dev/null)

if [ -n "$LIST_PATHS" ] && [ -n "$TOKEN" ]; then
  while IFS= read -r EP; do
    [ -z "$EP" ] && continue
    RESP=$(curl -s "$BASE$EP" -H "Authorization: Bearer $TOKEN")
    python3 - <<PYEOF
import json, sys
try:
    d = json.loads("""$RESP""")
except:
    print("FAIL — GET $EP response not valid JSON"); sys.exit(1)
# Check paginated list shape
if isinstance(d, dict) and 'data' in d:
    total = d.get('total', len(d['data']))
    if total > 0:
        print(f"PASS — $EP has {total} seeded record(s)")
    else:
        print("FAIL — $EP returned empty data for seeded user (seed failure or status enum mismatch)")
        sys.exit(1)
elif isinstance(d, list):
    if len(d) > 0:
        print(f"PASS — $EP has {len(d)} seeded record(s)")
    else:
        print("FAIL — $EP returned empty list for seeded user")
        sys.exit(1)
else:
    print(f"PASS — $EP returned a non-list response (may not be a list endpoint)")
PYEOF
    if [ $? -eq 0 ]; then PASS=$((PASS+1)); else FAIL=$((FAIL+1)); fi
  done <<< "$LIST_PATHS"
fi

# ── TEST 5: No 500 errors in backend logs ──────────────────────────────────────
echo "=== TEST 5: Backend error log check ==="
ERROR_COUNT=$(docker compose logs backend 2>/dev/null | grep -c '"level":"ERROR"\|"level": "ERROR"\|ERROR:' || echo 0)
if [ "$ERROR_COUNT" -eq 0 ]; then
  echo "PASS — no ERROR-level log entries"; PASS=$((PASS+1))
else
  echo "WARN — $ERROR_COUNT ERROR-level entries in backend logs (may be expected during startup)"; PASS=$((PASS+1))
  docker compose logs backend 2>/dev/null | grep '"level":"ERROR"\|ERROR:' | tail -5
fi

# ── SUMMARY ────────────────────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SMOKE TEST RESULTS: $PASS passed, $FAIL failed"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$FAIL" -gt 0 ]; then exit 1; fi
```

#### 5c-iv — Interpret failures and fix before handoff

If any test failed, **do not mark the build complete**. Diagnose and fix:

| Failure | Root cause | Fix |
|---|---|---|
| `FAIL — access_token missing` | Auth response wrapped in `{data: {...}}` | Remove wrapper from auth router, or fix frontend hook to not double-unwrap |
| `FAIL — GET /endpoint → 422` | Scope ID required but not auto-resolved | Apply the scope auto-resolution pattern in the endpoint's service layer |
| `FAIL — GET /endpoint → 500` | Pydantic schema mismatch or async gotcha | `docker compose logs backend --tail=50`; fix the specific error shown |
| `FAIL — empty data for seeded user` | Seed status values don't match schema `Literal` types | Compare seed.py status strings against Pydantic schema Literal values exactly |
| `FAIL — frontend HTTP 5xx` | Build error or missing env var | `docker compose logs frontend --tail=30`; check `.env.local` / docker-compose env |

After fixing each failure, re-run the relevant test to confirm the fix before moving on. Do not batch all fixes and re-run once — fix and verify incrementally.

#### 5c-iv-b — Write systemic patterns back to agent files (mandatory when applicable)

After fixing any smoke test failure, ask: "Is this a class of bug that will recur in future projects, or is it a one-off project-specific mistake?"

- **One-off** (typo, wrong env var value, project-specific seed datum): no agent update needed.
- **Systemic** (a structural failure mode that could affect any project built with these agents): update the relevant agent file immediately.

**Which agent to update:**

| Failure class | Agent file |
|---|---|
| Auth response contract broken (token location, envelope shape) | `backend-engineer.md` + `frontend-engineer.md` |
| Scope/tenant ID required but not auto-resolved from auth token | `backend-engineer.md` |
| Seed enum/status values don't match schema Literal types | `db-engineer.md` |
| Status/state values with no corresponding UI representation | `frontend-engineer.md` |
| API response unwrapping wrong (client double-unwraps) | `frontend-engineer.md` |
| ORM relationship name mismatches schema field name | `backend-engineer.md` |
| Docker service fails to start cleanly or service ordering wrong | `infra-engineer.md` |
| Seeded users have no associated data (blank screen after login) | `db-engineer.md` |
| Nested response objects flat-mapped to IDs (N+1 on client) | `backend-engineer.md` |
| Async/sync mismatch blocks runtime (CPU-bound in async handler) | `backend-engineer.md` |

**Update rules:**
1. Open the agent file and find the existing section where this pattern logically belongs — never append to the bottom
2. Write the rule at the concept level: describe the root cause, the symptom, and the fix
3. Keep it generic (no project-specific names, entity types, or values)
4. Keep it technology-agnostic where possible — if the concept applies across stacks, say so at the principle level; add a stack-specific code example only as illustration
5. Check that the pattern isn't already covered before adding — update existing entries rather than duplicating

This step closes the feedback loop. Every build makes the framework smarter for every future build.

#### 5c-v — Write results to handoff

Append to `workspace/{project}/handoffs/smoke-test-results.md`:

```markdown
# Smoke Test Results — {datetime}

| Test | Result | Notes |
|---|---|---|
| Login (access_token) | PASS/FAIL | {detail} |
| Frontend loads | PASS/FAIL | HTTP {code} |
| GET /endpoint → 200 | PASS/FAIL | {any failures} |
| Seeded data present | PASS/FAIL | {total count or failure reason} |
| No backend ERRORs | PASS/WARN | {count} entries |

## Failures found and fixed
{list any bugs found during smoke testing, how they were diagnosed, and what was changed}

## Agent files updated
{for each systemic pattern found: which agent file was updated, what section, and what rule was added — or "none" if all failures were one-off}
```

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
