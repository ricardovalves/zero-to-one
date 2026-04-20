Continuously improve an existing working product. Takes a change idea — UX refinement, new feature, backend improvement, or architectural upgrade — and runs it through the full product, design, and engineering pipeline. Respects the existing architecture, creates Linear issues, validates with real browser tests, and never breaks what's already working.

Usage: /iterate <project> [description of improvement]

Arguments: $ARGUMENTS

---

## When to use /iterate vs other commands

| Need | Command |
|---|---|
| First build of a new project | `/build` |
| Fix a specific broken thing | `/debug` |
| Refine a spec doc (PRD, design, arch) | `/refine` |
| Add/improve something on a working product | `/iterate` ← you are here |

`/iterate` assumes:
- The project has at least one passing `/build` checkpoint
- The stack is currently running (`docker compose up` works)
- You want the change to go through the full product/engineering process — not a hotfix

---

## Orchestration Rules

- Agents NEVER talk to each other — all communication through `workspace/{project}/`
- The orchestrator (you) runs ALL validation gates via Bash — never delegates this
- Each iteration is numbered as a new slice (after the last checkpoint slice)
- **Never re-read the full technical-spec.md, api-spec.yaml, or PRD from scratch** — use the latest checkpoint as the prior-state source of truth, supplement with targeted reads only
- Respect the existing architecture. If the proposed change requires violating it, surface the conflict to the user before proceeding

---

## Pipeline

### STEP 1: Parse arguments + read existing state

Parse $ARGUMENTS: first word = {project}, remainder = {improvement_description} (may be empty).

**Read the latest checkpoint:**
```bash
ls workspace/{project}/checkpoints/ 2>/dev/null | sort | tail -1
```
Read that file. It contains: stack facts, seed credentials, enum values, bugs fixed — everything needed without re-reading 5 large docs.

**If no checkpoints exist:** The project has not been built yet. Tell the user:
```
No build checkpoints found for {project}. Run /build {project} first to establish a working baseline.
```
Stop.

**If no improvement description provided:** Read `workspace/{project}/prd.md` (§ OKRs and feature priorities) and the latest checkpoint (§ what's built), then surface the top 5 improvement opportunities ordered by product impact:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPROVEMENT OPPORTUNITIES — {project}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Based on the PRD priorities and what's currently built:

  1. {opportunity} — {why it matters, 1 sentence}
  2. {opportunity} — {why it matters, 1 sentence}
  3. {opportunity} — {why it matters, 1 sentence}
  4. {opportunity} — {why it matters, 1 sentence}
  5. {opportunity} — {why it matters, 1 sentence}

Which would you like to tackle? Or describe your own:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Wait for the user's response. Once you have a description, continue.

---

### STEP 2: Classify the improvement

Classify the proposed change. This determines which agents run and in what order.

| Class | Definition | Agents involved |
|---|---|---|
| **UX Polish** | Visual/interaction change to an existing screen — no new endpoints, no schema change | `ux-designer` → `frontend-engineer` |
| **Feature Addition** | New screen, new endpoint, or new data entity | `product-manager` → `ux-designer` + `cto-architect` (parallel) → `project-manager` → `qa-engineer` → `backend-engineer` + `frontend-engineer` + `db-engineer` (parallel) |
| **Backend Improvement** | New/changed endpoint or business logic — no new UI pages | `cto-architect` (mini-spec only) → `qa-engineer` → `backend-engineer` |
| **Data/Schema Change** | New table, new column, index, query optimization | `cto-architect` (mini-spec only) → `db-engineer` → `backend-engineer` |
| **Architectural Upgrade** | Changes tech stack, adds new service, restructures existing code | `cto-architect` (full impact assessment) → user approval gate → full team |

**Present the classification to the user before proceeding:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ITERATION PLAN — {project}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Improvement:  {description}
Class:        {UX Polish | Feature Addition | Backend Improvement | Data/Schema Change | Architectural Upgrade}
Slice:        Slice {N+1} (after last passing slice {N})

Pipeline:
  {ordered list of agents that will run, e.g.:}
  1. product-manager — validates against PRD goals, writes user story
  2. ux-designer — designs the new flow or updated screen
  3. cto-architect — assesses architectural impact, writes mini-spec
  4. project-manager — creates Linear issue, adds to roadmap
  5. qa-engineer — writes tests before any implementation
  6. backend-engineer + frontend-engineer + db-engineer — implement in parallel
  7. compile gate + browser gate (orchestrator runs these directly)

What changes:
  Backend:  {endpoints added/changed, or "none"}
  Database: {schema changes, or "none"}
  Frontend: {pages/components added/changed, or "none"}

What does NOT change:
  {list of existing features/endpoints that are out of scope for this iteration}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Proceed? (yes / no / adjust scope)
```

Wait for explicit confirmation before launching any agents.

---

### STEP 3: Write the iteration brief

Before launching any agents, write a concise iteration brief that all agents will read. This replaces the need for each agent to reconstruct context from scratch.

Write to `workspace/{project}/iterations/iter-{N}.md`:

```markdown
# Iteration {N}: {short name}

**Project:** {project}
**Class:** {UX Polish | Feature Addition | ...}
**Slice:** Slice {N+1}
**Date:** {date}

## What to build

{3–5 sentences describing the improvement, what success looks like, and why it matters to the user}

## Context from latest checkpoint (Slice {last_N})

{paste key facts from the checkpoint: stack, enums, seed credentials, critical patterns}

## What's already built — DO NOT re-implement

{bullet list from checkpoint: endpoints, pages, DB tables that exist}

## What to add/change

{specific endpoints to add, pages to change, schema migrations needed}

## Constraints

- Must not break existing functionality (regression test the full smoke suite)
- Must match existing code patterns (see CLAUDE.md in src/)
- Enum values must match those in the checkpoint (do not invent new values)
- Existing API contracts must not change (backwards-compatible only)
```

---

### STEP 4: Product validation (Feature Addition only — skip for other classes)

Skip to Step 5 for UX Polish, Backend Improvement, Data/Schema Change.

**4a — Product Manager:** Validate the feature against the product's OKRs and existing priorities.

Invoke `product-manager`:
> "Read `workspace/{project}/iterations/iter-{N}.md` and `workspace/{project}/prd.md`. Evaluate this proposed iteration against the product's existing OKRs and feature priorities. Write a user story with acceptance criteria, a RICE score, and a recommendation (ship / defer / descope). If descope is recommended, state what the minimal version is. Write your output to `workspace/{project}/iterations/iter-{N}-pm.md`. Do NOT rewrite the full PRD — append only to `workspace/{project}/prd.md` under a ## Iteration {N} section."

Wait for completion.

Read `workspace/{project}/iterations/iter-{N}-pm.md`. If the PM recommends **defer**, surface the reasoning to the user and ask if they want to continue anyway or pick a different improvement.

**4b — UX Designer + CTO Architect (parallel, Feature Addition only):**

Invoke both simultaneously:

`ux-designer`: "Read `workspace/{project}/iterations/iter-{N}.md`, `workspace/{project}/iterations/iter-{N}-pm.md` (user story + acceptance criteria), and `workspace/{project}/design-spec.md` (existing design system — use its tokens and components, do NOT invent new ones). Design only the new or changed screen(s) for this iteration. Write a focused design addition to `workspace/{project}/iterations/iter-{N}-design.md`. Do NOT rewrite design-spec.md. Create or update only the relevant prototype HTML in `workspace/{project}/prototype/`."

`cto-architect`: "Read `workspace/{project}/iterations/iter-{N}.md`, `workspace/{project}/technical-spec.md` §3 (Data Architecture) and §4 (API Design), and `workspace/{project}/api-spec.yaml`. Assess the architectural impact of this iteration. Write a mini-spec to `workspace/{project}/iterations/iter-{N}-arch.md` covering: new/changed endpoints (full OpenAPI snippets), any schema changes (Alembic migration outline), and any NFR implications. Do NOT rewrite technical-spec.md or api-spec.yaml. Append new endpoints to api-spec.yaml under their relevant tag."

Wait for both.

---

### STEP 5: Project management — create Linear issue

Invoke `project-manager`:
> "Read `workspace/{project}/iterations/iter-{N}.md` and (if it exists) `workspace/{project}/iterations/iter-{N}-pm.md`. Create a Linear issue for this iteration: title, description, acceptance criteria, estimate. If LINEAR_API_KEY is set, create it via the API. Add this iteration to `workspace/{project}/roadmap.md` under the appropriate epic. Write the issue key to `workspace/{project}/iterations/iter-{N}-issue.md`."

Wait for completion.

---

### STEP 6: Write slice contracts

Write focused agent contracts (same pattern as /build):

```bash
mkdir -p workspace/{project}/slices/slice-{N+1}-tests
```

For backend (if needed):
```bash
cat > workspace/{project}/slices/slice-{N+1}-backend.md << 'EOF'
# Slice {N+1}: {name} — Backend Contract

## Source of truth
workspace/{project}/iterations/iter-{N}.md
workspace/{project}/iterations/iter-{N}-arch.md  (if exists)

## Endpoints to implement
{paste from iter-{N}-arch.md or describe inline}

## Already built — DO NOT re-implement or modify
{list from checkpoint}

## Tests to pass
workspace/{project}/slices/slice-{N+1}-tests/test_{name}.py

## Enum values (use EXACTLY these — do not invent new values)
{from checkpoint}
EOF
```

For frontend (if needed):
```bash
cat > workspace/{project}/slices/slice-{N+1}-frontend.md << 'EOF'
# Slice {N+1}: {name} — Frontend Contract

## Source of truth
workspace/{project}/iterations/iter-{N}.md
workspace/{project}/iterations/iter-{N}-design.md  (if exists)

## Pages/components to implement or change
{list with exact routes and component names}

## API shapes this page consumes
{paste relevant response schemas from iter-{N}-arch.md or existing api-spec.yaml}

## Already built — DO NOT modify unless explicitly listed above
{list from checkpoint}

## Import types from
src/frontend/src/types/api-generated.ts  (generated from live OpenAPI)
EOF
```

---

### STEP 7: Test-first (skip for UX Polish)

Invoke `qa-engineer` before any implementation agent:
> "Read `workspace/{project}/slices/slice-{N+1}-backend.md`. Write pytest integration tests for every new or changed endpoint. Use httpx AsyncClient with a real test database. Cover happy path + error cases for each endpoint. Write to `workspace/{project}/slices/slice-{N+1}-tests/test_{name}.py`. Implementation does not exist yet — write against the spec."

Wait for qa-engineer. Then launch implementation agents.

---

### STEP 8: Implement (parallel within the slice)

Launch only the agents relevant to this iteration's class:

| Class | Agents to launch |
|---|---|
| UX Polish | `frontend-engineer` only |
| Feature Addition | `db-engineer` + `backend-engineer` + `frontend-engineer` (parallel) |
| Backend Improvement | `backend-engineer` only |
| Data/Schema Change | `db-engineer` → `backend-engineer` (sequential — schema first) |
| Architectural Upgrade | All relevant engineers (sequential or parallel per dependency) |

Brief each agent:
- **db-engineer**: "Read `workspace/{project}/slices/slice-{N+1}-backend.md` and the latest checkpoint `workspace/{project}/checkpoints/slice-{last_N}.md`. Write ONLY the Alembic migration for this iteration's schema changes. Do NOT modify existing migrations. This is Slice {N+1}."
- **backend-engineer**: "Read `workspace/{project}/slices/slice-{N+1}-backend.md` and `workspace/{project}/slices/slice-{N+1}-tests/test_{name}.py`. Your implementation is complete when `pytest slices/slice-{N+1}-tests/` passes. Modify only the files needed for this iteration — do not refactor existing code."
- **frontend-engineer**: "Read `workspace/{project}/slices/slice-{N+1}-frontend.md`. Implement or update only the listed pages and components. All types must come from `src/types/api-generated.ts` — do not hand-write API response types. Do not modify pages outside the scope of this iteration."

Wait for all relevant agents.

---

### STEP 9: Regenerate TypeScript types (if backend changed)

If any backend endpoints were added or changed:

```bash
# Wait for backend to be running with new endpoints
curl -s http://localhost:8001/openapi.json \
  | npx openapi-typescript /dev/stdin \
  -o workspace/{project}/src/frontend/src/types/api-generated.ts

echo "[PASS] api-generated.ts updated from live OpenAPI"
```

---

### STEP 10: Compile gate

```bash
cd workspace/{project}/src

docker compose exec backend bash -c "
  ruff check app/ --quiet && echo '[PASS] ruff' || { echo '[FAIL] ruff'; exit 1; }
  python -m compileall app/ -q && echo '[PASS] syntax' || { echo '[FAIL] syntax'; exit 1; }
  pytest slices/slice-{N+1}-tests/ -x -q 2>&1 | tail -30 && echo '[PASS] tests' || { echo '[FAIL] tests'; exit 1; }
"

docker compose exec frontend bash -c "
  npx tsc --noEmit --pretty 2>&1 | tail -20 && echo '[PASS] TypeScript' || { echo '[FAIL] TypeScript'; exit 1; }
"
```

Fix any failures before proceeding. Do not proceed to the browser gate with a failing compile gate.

---

### STEP 11: Regression smoke test

Before testing the new feature, verify existing features still work:

```bash
# Existing health check
CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/api/v1/health)
[ "$CODE" = "200" ] && echo "[PASS] health" || echo "[FAIL] health — $CODE"

# Login still works (use credentials from latest checkpoint)
LOGIN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"{seed_email}","password":"{seed_pass}"}' \
  -w "\n%{http_code}")
CODE=$(echo "$LOGIN" | tail -1)
[ "$CODE" = "200" ] && echo "[PASS] login" || echo "[FAIL] login — $CODE"

# All non-parameterized GETs still return 2xx
# (add any project-specific critical endpoints here)
```

If any regression test fails: diagnose and fix before writing the checkpoint.

---

### STEP 12: Browser gate (Playwright)

Verify the new feature works in a real browser AND existing features still work:

```bash
node -e "
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  const errors = [];
  page.on('console', m => m.type() === 'error' && errors.push(m.text()));

  // --- Regression: existing features ---
  // (test at least one critical existing user flow from prior slices)

  // --- New feature ---
  // (test the specific new page/interaction added in this iteration)

  await browser.close();
  if (errors.length > 0) {
    console.error('[FAIL] JS errors:', errors);
    process.exit(1);
  }
  console.log('[PASS] browser gate');
})();
"
```

---

### STEP 13: Security check (if auth, billing, or user data is touched)

If the iteration touches authentication, payment, user PII, or API key handling, invoke `security-engineer`:
> "Read `workspace/{project}/iterations/iter-{N}-arch.md` and the relevant backend files modified in this iteration. Assess security implications: OWASP Top 10, STRIDE threats specific to the change, auth boundary violations. Report any HIGH or CRITICAL findings that must be fixed before shipping."

If any HIGH/CRITICAL findings: fix before writing checkpoint.

---

### STEP 14: Git commit

```bash
cd workspace/{project}/src
git add -A
git commit -m "iter-{N}-{name}: {brief description} — compile+browser gates pass"
```

---

### STEP 15: Write checkpoint

```bash
mkdir -p workspace/{project}/checkpoints
SHA=$(git -C workspace/{project}/src rev-parse --short HEAD)
cat > workspace/{project}/checkpoints/slice-{N+1}.md << EOF
# Slice {N+1}: {name} — Checkpoint (Iteration {iter_N})

**Completed:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Git SHA:** $SHA
**Prior checkpoint:** slice-{N}.md

## What was added/changed this iteration
- {brief description of each change}

## Seed credentials (unchanged from prior)
{copy from prior checkpoint}

## Schema facts (updated if schema changed)
{copy from prior checkpoint, add any new facts}

## Bugs fixed this slice
- {any bugs found and fixed}

## Agent files updated
- {any .claude/agents/*.md files updated with new patterns}

## Gate results
- Compile: PASS
- Regression smoke: PASS
- Browser: PASS ({what was tested})
EOF
```

---

### STEP 16: Framework self-improvement

If any bug was found and fixed during this iteration that represents a **systemic pattern** (not project-specific), update the relevant agent file in `.claude/agents/` before declaring done. Rules:
- Generic: describe the class of bug, not project values
- Technology-agnostic where possible
- Integrated into the existing relevant section, not appended as "lessons learned"

---

### STEP 17: Completion report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ITERATION COMPLETE — {project}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Improvement:  {description}
Slice:        {N+1} (Iteration {iter_N})
Git SHA:      {sha}

What shipped:
  {bullet list of what was built}

What was verified:
  ✓ Compile gate (ruff, py_compile, tsc, {N} tests)
  ✓ Regression smoke ({N} existing endpoints still healthy)
  ✓ Browser gate ({what was tested in the browser})
  {✓ Security scan — no HIGH/CRITICAL findings | — not applicable}

Linear:
  {Issue key and title, or "— set LINEAR_API_KEY to sync"}

What's next:
  - Run /iterate {project} to keep improving
  - Run /sprint {project} to plan the next sprint
  - Run /review-pr {project} before merging to main
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Scope guardrails (non-negotiable)

1. **One improvement per iteration.** If the user describes multiple improvements, implement the first one and offer a follow-up `/iterate` for the rest. Combining improvements in one slice makes regressions impossible to bisect.
2. **No backwards-incompatible API changes.** If the improvement requires a breaking change, the orchestrator must surface this to the user and propose a versioning strategy (new endpoint, `v2/` prefix) before any agent writes code.
3. **No re-architecture.** If the proposed change requires rewriting existing core services (not adding to them), classify it as Architectural Upgrade and get explicit user approval at Step 2.
4. **Enum values are frozen unless deliberately extended.** If a new enum value is required, it must be added to both the DB enum, the Pydantic schema, the frontend type, AND the seed script in one migration — never piecemeal.
5. **The seed script must stay valid.** Any schema or enum changes must be backwards-compatible with the existing `seed.py`, or `seed.py` must be updated in the same slice.
