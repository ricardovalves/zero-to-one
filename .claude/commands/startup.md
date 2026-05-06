Run the full Zero-to-One pipeline from idea to working prototype.

Orchestrates all agents with maximum parallelism. Agents communicate only through the filesystem — never directly. Produces a full execution report at the end.

**Not sure if the idea is worth building?** Run `/prototype` first — it produces a working demo in hours without any strategic analysis. Show it to real users. If they want it, come back here.

Usage: /startup <idea description>

Arguments: $ARGUMENTS

---

## Orchestration Rules

1. **Agents never talk to each other.** All communication is through `workspace/{project}/`. You (the orchestrator) read outputs and invoke the next wave of agents.
2. **Run agents in parallel whenever possible.** Use multiple simultaneous Agent tool calls.
3. **Always produce an execution report** at the end: `workspace/{project}/execution-report.md`.

---

## Pipeline

### STEP 1: Setup
Derive a short project slug from the idea in $ARGUMENTS (e.g., "a recipe sharing app" → "recipehub").
Create directory: `workspace/{project}/handoffs/` (ensure it exists).
Record start time.

---

### STEP 1b: Idea Sharpening — ask before anything runs

Present all four questions at once. Do not launch any agent until you have the answers (or an explicit skip).

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before we start — 4 quick questions to sharpen the analysis.
Better input = better output from every agent.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Who is the primary user?
   (e.g. "solo freelancers", "ops managers at mid-size SaaS companies")

2. How are they solving this problem today?
   (e.g. "spreadsheets + Slack", "a legacy tool they hate", "nothing — they just don't")

3. What is the one thing the MVP must do — the core action?
   (e.g. "track time and generate invoices", "match candidates to jobs in under 60 seconds")

4. B2B or B2C? And rough monetisation idea?
   (e.g. "B2B SaaS, ~$30/seat/month", "B2C freemium with a pro tier")

Answer all four, or type "skip" to proceed with only the original idea.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Wait for the user's response.

After receiving answers (or "skip"), write `workspace/{project}/idea-brief.md`:

```markdown
# Idea Brief — {project}

**Original idea:** {from $ARGUMENTS}
**Primary user:** {answer or "not specified"}
**Current solution:** {answer or "not specified"}
**Core MVP action:** {answer or "not specified"}
**Business model:** {answer or "not specified"}

## Sharpened Brief

{2–3 sentence synthesis of the above. Concrete, specific, no filler. This is the primary input for every downstream agent.}
```

All agents will read `idea-brief.md` as their primary context. The raw idea string from $ARGUMENTS is the fallback when idea-brief.md is not available.

---

### STEP 2: Business Analysis [SEQUENTIAL — nothing to parallelize yet]

**Launch:** `business-expert` agent
- Input: the idea in $ARGUMENTS + project name
- Reads: nothing (first agent in chain)
- Writes: `workspace/{project}/business-analysis.md` + `workspace/{project}/handoffs/business-expert.md`

Wait for completion. Read `workspace/{project}/handoffs/business-expert.md`.

---

### GATE 1: Viability Check — MANDATORY STOP

Read the business analysis. Present the viability report to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VIABILITY REPORT — {project}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verdict:      {GO / CONDITIONAL GO / NO-GO}

Market
  TAM:        ${X}B
  SAM:        ${X}B
  SOM Yr 1:   ${X}M

Economics
  Rev Model:  {model}
  LTV:CAC:    {X}x
  Break-even: {X} months

Competition
  #1 rival:   {name} — weakness: {weakness}
  Moat:       {your defensible advantage}

Top Risks
  1. {risk} — {mitigation}
  2. {risk} — {mitigation}
  3. {risk} — {mitigation}

Full report: workspace/{project}/business-analysis.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If `workspace/{project}/assumptions.md` exists, append a summary beneath the report:

```
Key assumptions made so far:
{list up to 5 bullets from assumptions.md — the most consequential ones}
→ Full log: workspace/{project}/assumptions.md
```

**If NO-GO:** Stop here. Do NOT offer to continue. Present the risks and let the user decide.

**If CONDITIONAL GO or GO:** Ask: *"Do you want to proceed to product definition and design? (yes / no / adjust idea)"*

> **Tip:** Before committing to the full pipeline, consider running `/prototype {project}` first — it builds a working demo in hours (no specs, no reviews, no billing). Show it to 5 real users. A validated prototype makes the /startup investment much safer.

Wait for explicit user confirmation before moving to Step 3.

---

### STEP 3: Product Requirements [SEQUENTIAL — depends on Step 2]

**Launch:** `product-manager` agent
- Input: project name
- Reads: `workspace/{project}/handoffs/business-expert.md` (primary), `workspace/{project}/business-analysis.md` (if needed)
- Writes: `workspace/{project}/prd.md` + `workspace/{project}/handoffs/product-manager.md`

Wait for completion. Read `workspace/{project}/handoffs/product-manager.md`.

---

### STEP 4: Design + Architecture [PARALLEL — both depend only on Step 3]

**Launch BOTH simultaneously in a single response:**

| Agent | Reads | Writes |
|---|---|---|
| `ux-designer` | `handoffs/product-manager.md`, `prd.md` | `design-spec.md`, `prototype/*.html`, `handoffs/ux-designer.md` |
| `cto-architect` | `handoffs/product-manager.md`, `prd.md` | `technical-spec.md`, `api-spec.yaml`, `handoffs/cto-architect.md` |

Wait for BOTH to complete before proceeding.

Read: `workspace/{project}/handoffs/ux-designer.md` and `workspace/{project}/handoffs/cto-architect.md`

---

### STEP 4b: Contradiction Detection

Before proceeding to project management, scan all four handoff files for contradictions. Look specifically for mismatches in these fields:

| Field | Where to find it | What to compare |
|---|---|---|
| Target user | PM handoff (primary persona) | UX handoff (persona designed for) |
| B2B vs B2C | Business expert handoff | UX handoff (design patterns chosen) |
| Scale assumptions | Business expert (SOM, user count) | CTO handoff (infrastructure scale target) |
| MVP scope | PM handoff (must-have features) | CTO handoff (what was architected) |
| Real-time requirements | PM handoff | CTO handoff (architecture decisions) |
| Out-of-scope items | PM handoff (explicit non-goals) | CTO handoff (anything built that shouldn't be) |

If contradictions are found, present them before Gate 2:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTRADICTIONS DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{For each contradiction:}
⚠  {Field}: PM assumed {X}, but {agent} assumed {Y}
   → Recommend: {which to trust and why, or ask user to clarify}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Resolve these before proceeding? (yes — I'll clarify / no — proceed anyway)
```

Wait for user response. If they clarify, update the relevant handoff files accordingly before continuing. If they say proceed, log the unresolved contradictions in `workspace/{project}/assumptions.md`.

If no contradictions are found, continue silently.

---

### STEP 5: Project Management [SEQUENTIAL — depends on Step 4]

**Launch:** `project-manager` agent
- Input: project name
- Reads: `handoffs/product-manager.md`, `handoffs/cto-architect.md`, `handoffs/ux-designer.md`
- Writes: `workspace/{project}/roadmap.md` + `workspace/{project}/handoffs/project-manager.md`
- If `LINEAR_API_KEY` is set: also creates Linear issues via `python .claude/tools/linear_client.py`

Wait for completion. Read `workspace/{project}/roadmap.md` and `workspace/{project}/handoffs/project-manager.md`.

---

### STEP 5b: Generate Project CLAUDE.md

Read all handoff files and generate `workspace/{project}/CLAUDE.md`. This file gives Claude dense project context when anyone opens the workspace directory — it inherits the framework rules from the root CLAUDE.md and adds project-specific knowledge.

Write the file using this structure (populate every field from actual document content — no placeholders):

```markdown
# {Product Name} — Project Context

> Auto-generated by the /startup pipeline. The root CLAUDE.md contains framework rules.
> This file provides project-specific context when working in this directory.

## Product Overview

{2–3 sentences: what the product does, who it serves, core value proposition — from prd.md}

## Users & Personas

| Persona | Role | Primary Goal |
|---|---|---|
| {name} | {role} | {goal} |

## Core Entities

| Entity | Description | Key Fields |
|---|---|---|
| {entity} | {what it is} | {field1, field2, field3} |

## Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | {framework + version} | {key decision} |
| Backend | {framework + version} | {key decision} |
| Database | {db + version} | {key decision} |
| Auth | {strategy} | {key decision} |
| Storage | {solution} | {key decision} |

## Status Enums (critical — never invent new values)

{List every status/role Literal type from technical-spec.md, e.g.:}
- `TaskStatus`: `todo` | `in_progress` | `blocked` | `on_hold` | `done`
- `UserRole`: `admin` | `member` | `viewer`

## Key API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | /api/v1/auth/login | Authenticate user |
| GET | /api/v1/{primary-resource} | List resources (scope auto-resolved from token) |
| POST | /api/v1/{primary-resource} | Create resource |
| ... | | |

## Key User Flows

1. **{flow name}**: {brief description}
2. **{flow name}**: {brief description}
3. **{flow name}**: {brief description}

## North Star Metric

{metric — from prd.md}

## MVP Scope

**Must-Have:**
{list from prd.md}

**Out of Scope (v1):**
{list from prd.md}

## Run Locally

```bash
cd workspace/{project}/src
docker compose up
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Documentation

| Document | Path |
|---|---|
| Business case | `workspace/{project}/business-analysis.md` |
| PRD | `workspace/{project}/prd.md` |
| Design spec | `workspace/{project}/design-spec.md` |
| Technical spec | `workspace/{project}/technical-spec.md` |
| API spec | `workspace/{project}/api-spec.yaml` |
| Roadmap | `workspace/{project}/roadmap.md` |
```

---

### GATE 2: Plan & Milestones — MANDATORY STOP

Read the roadmap. Present the execution plan to the user:

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

Wait for explicit user confirmation before launching any engineering agents (db-engineer, backend-engineer, frontend-engineer, infra-engineer).

If the user adjusts scope, update `workspace/{project}/roadmap.md` accordingly before proceeding.

---

### STEP 6: Execution Report

Write `workspace/{project}/execution-report.md` using the template at `.claude/templates/execution-report.md` as your structure.
Read all handoff notes to populate the report accurately.

```markdown
# Execution Report: {project}

**Pipeline:** /startup
**Completed:** {datetime}
**Duration:** {total time}
**Status:** COMPLETE / PARTIAL (list what's missing)

---

## Business Case

| Metric | Value |
|---|---|
| Verdict | {GO / NO-GO / CONDITIONAL GO} |
| TAM | ${X}B |
| SOM (Year 1) | ${X}M |
| LTV:CAC | {X}x |
| Top Competitor | {name} — weakness: {weakness} |

---

## Product Scope

| Item | Value |
|---|---|
| North Star Metric | {metric} |
| MVP Features | {N} Must-Have, {N} Should-Have |
| Primary Persona | {name} — {role} |
| Out of Scope | {top 3 deferred items} |

---

## Design & Prototype

| Item | Value |
|---|---|
| Design System | {primary color}, {font} |
| Prototype Screens | {list of .html files} |
| Key User Flow | {flow name} |
| Open in Browser | `workspace/{project}/prototype/index.html` |

---

## Architecture

| Layer | Technology |
|---|---|
| Frontend | {framework} on {platform} |
| Backend | {framework} on {platform} |
| Database | {DB} on {platform} |
| Auth | {strategy} |
| CI/CD | {platform} |

---

## Delivery Plan

| Sprint | Dates | Goal | Points |
|---|---|---|---|
| 0 | {start}–{end} | Foundation | {N} |
| 1 | ... | Core features | {N} |
| ... | | | |

---

## Artifacts Produced

| File | Agent | Status |
|---|---|---|
| `business-analysis.md` | business-expert | {✓ / ✗} |
| `prd.md` | product-manager | {✓ / ✗} |
| `design-spec.md` | ux-designer | {✓ / ✗} |
| `prototype/index.html` | ux-designer | {✓ / ✗} |
| `technical-spec.md` | cto-architect | {✓ / ✗} |
| `api-spec.yaml` | cto-architect | {✓ / ✗} |
| `roadmap.md` | project-manager | {✓ / ✗} |

---

## Decisions Made

1. {key decision}: {what was decided and why}
2. {key decision}: {what was decided and why}
3. {key decision}: {what was decided and why}

---

## Warnings / Issues

- {any NO-GO flags, missing data, or low-confidence decisions}

---

## Next Steps

1. Review prototype: open `workspace/{project}/prototype/index.html` in browser
2. Review PRD: `workspace/{project}/prd.md`
3. When ready: `/build {project}` to start development
4. Individual phases: `/design {project}`, `/architect {project}`
```

---

### STEP 7: Summary to User

Print:
```
/startup complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:   {project}
Verdict:   {GO/NO-GO}  |  TAM: ${X}B  |  SOM: ${X}M
Stack:     {frontend} + {backend} + {database}
Prototype: workspace/{project}/prototype/index.html
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
7 artifacts generated. Full report:
  workspace/{project}/execution-report.md

Next: /build {project}
```
