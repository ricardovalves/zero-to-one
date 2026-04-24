Rapid prototype pipeline: idea → working demo in the fastest path possible.

Skips all strategic analysis, full specifications, and quality gate reviews. Produces a running app you can put in front of real users today. When those users want it → run /startup to build it properly.

Usage: /prototype <idea description>

Arguments: $ARGUMENTS

---

## What This Does (and Doesn't Do)

**Does:** Creates a working demo with seeded data, login, and one core feature — enough to show five people and get a yes or no.

**Does not:** Business analysis, full PRD, design system, API spec, UX prototype, Linear issues, security review, architecture review, test suites, billing, email, CI/CD.

**When to use instead:**
- `/startup` — when you're committed to building this and want the full strategic + execution pipeline
- `/prototype` — when you want to validate the idea before investing in the full pipeline

---

## Orchestration Rules

1. **You write the specs directly.** No business-expert, product-manager, ux-designer, cto-architect, or project-manager agents. You synthesize from the user's answers.
2. **Engineering agents only.** infra-engineer, db-engineer, backend-engineer, frontend-engineer.
3. **No review gates.** No security-engineer, architecture-reviewer, or qa-engineer at any slice.
4. **Maximum parallelism within each slice.** All eligible agents launch simultaneously.
5. **Speed over completeness.** Good enough to demo beats perfect but unbuilt.

---

## Pipeline

### STEP 1: Setup

Derive a short project slug from the idea in $ARGUMENTS (e.g., "a kanban board for freelancers" → "kanban-freelance").
Create directory: `workspace/{project}/handoffs/` (ensure it exists).
Record start time.

---

### STEP 1b: Idea Sharpening — ask before anything runs

Present all four questions at once. These are different from /startup — focused on the demo, not the business model.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
4 quick questions before we build.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Who is the primary user?
   (e.g. "solo freelancers", "operations managers at mid-size companies")

2. What ONE action must they complete in this demo?
   (e.g. "create a task and move it to done", "generate an invoice from time entries")

3. What data do they need to see to feel the value?
   (e.g. "a board with tasks already assigned to them", "a dashboard showing hours logged this week")

4. Who are you showing this to, and what would make them say yes?
   (e.g. "potential customers — they say yes if they ask how to sign up",
    "investors — they say yes if the core loop is self-explanatory in under 2 minutes")

Answer all four, or type "skip" to proceed with only the original idea.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Wait for the user's response.

After receiving answers (or "skip"), synthesize a `workspace/{project}/prototype-brief.md` directly. Do not delegate this — you write it.

```markdown
# Prototype Brief — {project}

**Idea:** {from $ARGUMENTS}
**Primary user:** {answer or "not specified"}
**Demo action:** {answer or "not specified"}
**Value signal:** {what data the user needs to see}
**Audience:** {who sees the demo and what success looks like}

## Stack

| Layer | Choice |
|---|---|
| Frontend | Next.js 15 (App Router) |
| Backend | FastAPI (Python 3.12) |
| Database | PostgreSQL 16 |
| Auth | JWT (httpOnly cookie) |
| Local | docker compose up |

## Data Model

{Write 2–3 tables only. One is always `users`. The other 1–2 are the minimum to make the demo action work.}

| Table | Key columns |
|---|---|
| users | id, email, name, hashed_password, email_verified, role |
| {primary_entity} | id, user_id (FK), {2–4 domain columns}, status, created_at |
| {secondary_entity} | id, {primary_entity}_id (FK), {1–3 domain columns} |

## API Endpoints (~7 total)

| Method | Path | Description |
|---|---|---|
| GET | /health | Health check |
| POST | /api/v1/auth/register | Register user |
| POST | /api/v1/auth/login | Log in, set cookie |
| GET | /api/v1/auth/me | Current user |
| GET | /api/v1/{primary_entity} | List (scoped to current user) |
| POST | /api/v1/{primary_entity} | Create |
| PATCH | /api/v1/{primary_entity}/{id} | Update (e.g., change status) |

## Seed Data

Seed exactly one demo user and enough {primary_entity} records for the value signal to be visible:

- **Email:** demo@{project}.local
- **Password:** password123
- **Name:** Demo User
- **Data:** {describe 3–5 seeded records that make the demo action visually clear}
```

---

### GATE: Build Confirmation — MANDATORY STOP

Present to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROTOTYPE PLAN — {project}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Building: {one sentence — what the demo does, e.g. "A kanban board where freelancers
           can create projects, add tasks, and drag them through three status columns."}

Stack: Next.js 15 + FastAPI + PostgreSQL — runs with docker compose up

Slice 0  Infrastructure    docker compose up, /health → 200
Slice 1  Auth              login works with demo@{project}.local / password123
Slice 2  {core feature}    {seeded entity} visible on dashboard

No reviews, no tests, no billing, no email. This is a validation artifact.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Start building? (yes / no / adjust)
```

Wait for explicit confirmation. If the user adjusts, update `prototype-brief.md` before proceeding.

---

### STEP 2: Git Init

```bash
cd workspace/{project}
git init -q
git add -A
git commit -q -m "init: prototype brief"
```

---

### STEP 3: Slice 0 — Infrastructure

**Goal:** Full stack starts cleanly. `/health` returns 200.

Write slice contracts for each agent directly here (do not delegate contract writing):

**infra-engineer contract:**
- Write `workspace/{project}/src/docker-compose.yml` with: `db` (postgres:16-alpine), `backend` (FastAPI), `frontend` (Next.js), `mailpit` (axllent/mailpit — always included)
- Write `workspace/{project}/src/backend/Dockerfile` (multi-stage, python:3.12-slim, non-root user)
- Write `workspace/{project}/src/frontend/Dockerfile` (multi-stage, node:20-alpine, Next.js standalone)
- Write `workspace/{project}/src/.env.example` with DATABASE_URL, SECRET_KEY, FRONTEND_URL, SMTP_HOST=mailpit, SMTP_PORT=1025, NEXT_PUBLIC_API_URL
- Write `workspace/{project}/src/.env` (copy of .env.example with real local values — git-ignored)
- Write `workspace/{project}/src/backend/.dockerignore` and `workspace/{project}/src/frontend/.dockerignore`
- Read `workspace/{project}/prototype-brief.md` for project name and stack context

**db-engineer contract:**
- Read `workspace/{project}/prototype-brief.md` for the data model
- Write `workspace/{project}/src/backend/migrations/` — Alembic setup + initial migration creating the `users` table and `{primary_entity}` table(s) from the data model
- Include indexes on FK columns and status columns
- No foreign key to tables not yet created

**backend-engineer contract:**
- Read `workspace/{project}/prototype-brief.md` for stack and endpoints
- Write FastAPI skeleton: `app/main.py`, `app/config.py` (pydantic-settings), `app/database.py` (async SQLAlchemy), `app/models/user.py`, `app/models/{primary_entity}.py`
- Write `GET /health` endpoint returning `{"status": "ok", "version": "0.1.0"}`
- Write `app/routers/__init__.py` and `app/main.py` router registration
- Structured JSON logging to stdout on every request (method, path, status, duration)
- Read `workspace/{project}/prototype-brief.md` for entity names and column definitions

**frontend-engineer contract:**
- Read `workspace/{project}/prototype-brief.md` for project name and demo action
- Write Next.js 15 App Router skeleton: `app/layout.tsx`, `app/page.tsx` (redirect to /login), `app/globals.css`
- Write `lib/api.ts` (axios instance pointing to NEXT_PUBLIC_API_URL)
- Plain functional UI — no design system required. Tailwind CSS for styling.
- No placeholder screens — the root page redirects to /login (which is built in Slice 1)

**Launch all four agents simultaneously.**

Wait for all four to complete.

**Slice 0 Health Gate (you run this directly with Bash):**

```bash
cd workspace/{project}/src
cp .env.example .env  # if .env doesn't exist
docker compose build 2>&1 | tail -20
docker compose up -d
# Poll /health up to 60s:
for i in $(seq 1 12); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
  if [ "$STATUS" = "200" ]; then echo "✓ /health → 200"; break; fi
  echo "  waiting... ($i/12)"; sleep 5
done
docker compose logs backend 2>&1 | grep -c "ERROR" | xargs -I{} sh -c 'if [ {} -gt 0 ]; then echo "✗ ERROR entries in backend logs"; docker compose logs backend; exit 1; else echo "✓ No ERROR entries in backend logs"; fi'
```

If any check fails, diagnose and fix before proceeding to Slice 1. Do not continue with a broken stack.

**After Slice 0 passes:** Commit.

```bash
cd workspace/{project}
git add -A
git commit -q -m "slice-0: infrastructure — docker compose up, /health 200"
```

---

### STEP 4: Slice 1 — Auth

**Goal:** A user can log in with demo@{project}.local / password123 and land on a page (even if empty).

**db-engineer contract:**
- Add Alembic migration: add `email_verified` (bool, default false), `email_verified_at` (timestamptz nullable) to users table
- No new tables in this slice

**backend-engineer contract:**
- Read `workspace/{project}/prototype-brief.md` for user model and seed spec
- Write `app/routers/auth.py` with:
  - `POST /api/v1/auth/register` — bcrypt hash, create user, return user (no email verification gate in prototype mode — register immediately sets email_verified=True)
  - `POST /api/v1/auth/login` — verify password, set httpOnly JWT cookie, return user object
  - `GET /api/v1/auth/me` — return current user from JWT cookie, 401 if not authenticated
  - `POST /api/v1/auth/logout` — clear cookie
- Write `app/dependencies/auth.py` — `get_current_user` dependency
- Write `app/schemas/user.py` — request/response schemas (explicit field allowlist, no raw ORM objects)
- Write `workspace/{project}/src/backend/seed.py` — creates demo@{project}.local / password123 (idempotent: delete and recreate, or skip if exists)

**frontend-engineer contract:**
- Read `workspace/{project}/prototype-brief.md` for project name and demo credentials
- Write `app/(auth)/login/page.tsx` — login form + dev panel (always visible, shows demo@{project}.local / password123 with click-to-fill — no env gate needed in prototype mode)
- Write `app/(dashboard)/layout.tsx` — auth guard (redirect to /login if no valid session), navigation shell
- Write `app/(dashboard)/dashboard/page.tsx` — empty dashboard shell ("Your {primary_entity} will appear here" placeholder — seeded data appears in Slice 2)
- Write `lib/auth.ts` — login(), logout(), getMe() API calls + cookie handling
- Write `hooks/useUser.ts` — SWR-based current user hook

**Launch all three agents simultaneously.**

Wait for all three to complete.

**Slice 1 Browser Gate (you run this directly):**

```bash
cd workspace/{project}/src
docker compose restart backend frontend 2>/dev/null || true
# Wait for restart
sleep 10
# Run seed
docker compose exec backend python seed.py
# Smoke test auth
COOKIE_JAR=$(mktemp)
LOGIN=$(curl -s -w "\n%{http_code}" -c "$COOKIE_JAR" -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@{project}.local","password":"password123"}')
LOGIN_STATUS=$(echo "$LOGIN" | tail -1)
if [ "$LOGIN_STATUS" = "200" ]; then
  echo "✓ Login → 200"
else
  echo "✗ Login failed: $LOGIN_STATUS"
  echo "$LOGIN"
  exit 1
fi
ME=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE_JAR" http://localhost:8000/api/v1/auth/me)
[ "$ME" = "200" ] && echo "✓ /me → 200" || { echo "✗ /me failed: $ME"; exit 1; }
rm "$COOKIE_JAR"
```

Then open `http://localhost:3000` in a browser. Verify: login page loads, dev panel is visible, login with demo credentials redirects to dashboard (even if dashboard is empty). No JavaScript errors in browser console.

If any check fails, diagnose and fix before proceeding to Slice 2.

**After Slice 1 passes:** Commit.

```bash
cd workspace/{project}
git add -A
git commit -q -m "slice-1: auth — login, JWT cookie, seed user"
```

---

### STEP 5: Slice 2 — Core Feature

**Goal:** Seeded data is visible. The demo action is completable end-to-end.

Read `workspace/{project}/prototype-brief.md` for the primary entity, API endpoints, and seed data spec. Pass these to agents as their inline contracts.

**db-engineer contract:**
- Write Alembic migration for any remaining tables (secondary entities if specified in prototype-brief.md)
- Update seed.py to create the seeded {primary_entity} records described in prototype-brief.md

**backend-engineer contract:**
- Read `workspace/{project}/prototype-brief.md` for the 4–5 entity endpoints
- Write `app/routers/{primary_entity}.py` with all endpoints from the prototype brief
- All list endpoints scoped to the current authenticated user (read user_id from JWT, filter by it)
- Response schemas use explicit field allowlists (no raw ORM objects)
- Paginated list endpoints enforce a maximum page size (default 50, max 100)
- Each endpoint verifies the current user owns the requested object before returning it

**frontend-engineer contract:**
- Read `workspace/{project}/prototype-brief.md` for demo action, value signal (what data to show), and seed data spec
- Replace `app/(dashboard)/dashboard/page.tsx` with a real dashboard: SWR fetch of `GET /api/v1/{primary_entity}`, render seeded records in a list or table
- Write the UI for the demo action: e.g., if the action is "create a task and move it to done", add a create form and status toggle buttons
- The seeded data must be visible immediately on login — no "empty state" for the demo user
- Plain functional UI — no polish required. The goal is demonstrable, not beautiful.

**Launch all three agents simultaneously.**

Wait for all three to complete.

**Slice 2 Browser Gate (you run this directly):**

```bash
cd workspace/{project}/src
docker compose restart backend frontend 2>/dev/null || true
sleep 10
docker compose exec backend python seed.py
# Auth + data check
COOKIE_JAR=$(mktemp)
curl -s -c "$COOKIE_JAR" -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@{project}.local","password":"password123"}' > /dev/null
DATA=$(curl -s -w "\n%{http_code}" -b "$COOKIE_JAR" http://localhost:8000/api/v1/{primary_entity})
DATA_STATUS=$(echo "$DATA" | tail -1)
DATA_BODY=$(echo "$DATA" | head -1)
[ "$DATA_STATUS" = "200" ] && echo "✓ GET /{primary_entity} → 200" || { echo "✗ Failed: $DATA_STATUS"; echo "$DATA_BODY"; exit 1; }
RECORD_COUNT=$(echo "$DATA_BODY" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('data', d) if isinstance(d, dict) else d))" 2>/dev/null || echo "0")
[ "$RECORD_COUNT" -gt 0 ] && echo "✓ Seeded data present ($RECORD_COUNT records)" || { echo "✗ No seeded data returned"; exit 1; }
rm "$COOKIE_JAR"
# Check for backend errors
docker compose logs backend 2>&1 | grep -c "ERROR" | xargs -I{} sh -c 'if [ {} -gt 0 ]; then echo "✗ ERROR in backend logs"; docker compose logs backend 2>&1 | grep "ERROR"; exit 1; else echo "✓ No ERROR entries"; fi'
```

Then open `http://localhost:3000` in a browser. Verify: login redirects to dashboard, seeded records are visible, the demo action is completable (e.g., creating a task, changing a status, etc.). No JavaScript errors in browser console.

If any check fails, diagnose and fix before writing the summary.

**After Slice 2 passes:** Final commit.

```bash
cd workspace/{project}
git add -A
git commit -q -m "slice-2: core feature — {primary_entity} CRUD, seeded data visible"
```

---

### STEP 6: Summary to User

Write `workspace/{project}/execution-report.md`:

```markdown
# Execution Report: {project}

**Pipeline:** /prototype
**Completed:** {datetime}
**Duration:** {total time}
**Status:** PROTOTYPE COMPLETE

---

## What Was Built

{one paragraph — what the demo does, who it's for, what the demo action is}

## Run It

```bash
cd workspace/{project}/src
docker compose up
# Frontend: http://localhost:3000
# Login: demo@{project}.local / password123
```

## Slices Delivered

| Slice | Goal | Status |
|---|---|---|
| 0 — Infrastructure | docker compose up, /health → 200 | ✓ |
| 1 — Auth | login + cookie + seed user | ✓ |
| 2 — Core Feature | {seeded entity} visible, demo action works | ✓ |

## What This Is Not

This prototype has no: tests, security review, error handling, email, billing, CI/CD, or production deployment. It is a validation artifact — not a product.

**The code is throwaway.** `/startup` does not extend this prototype — it designs the architecture from scratch using a full PRD, cto-architect, and ux-designer. Expect the schema and codebase to be rebuilt. That is correct behavior.

## Next Steps

- **Validate first.** Show this to 5 real users. Watch them use it. If they ask "how do I sign up?" — you have signal.
- **If validated:** `/startup {project}` — full pipeline: business analysis, PRD, design system, architecture, Linear roadmap, full build with reviews. The prototype code gets replaced — that's expected.
- **If not:** You spent hours, not weeks. Adjust the idea or move on.
```

Print to user:

```
/prototype complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:  {project}
Demo:     http://localhost:3000
Login:    demo@{project}.local / password123

3 slices. Working login. Seeded data. Demonstrable.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Show this to 5 real users.
If they want it → /startup {project} to build it properly.
(This code is throwaway — /startup rebuilds from scratch. That's expected.)
```
