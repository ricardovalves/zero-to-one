# Workflow: New Product Pipeline

This document describes the end-to-end workflow for taking a new idea through the full AI-Startup pipeline. It is the reference implementation of the `/startup` skill.

---

## Overview

```
[Idea Input]
     │
     ▼ Phase 1: Strategy (sequential)
┌────────────────┐
│ Business Expert│ → business-analysis.md
└───────┬────────┘
        │
        ▼
┌────────────────┐
│Product Manager │ → prd.md
└───────┬────────┘
        │
        ▼ Phase 2: Design + Architecture (parallel)
┌───────┴───────┐
│               │
▼               ▼
UX Designer    CTO/Architect
design-spec.md  technical-spec.md
                api-spec.yaml
│               │
└───────┬───────┘
        │
        ▼ Phase 3: Planning
┌────────────────┐
│Project Manager │ → roadmap.md + Linear issues
└───────┬────────┘
        │
        ▼ Phase 4: Development (parallel by layer)
┌───────┬────────┬────────┬────────┐
│       │        │        │        │
▼       ▼        ▼        ▼        ▼
DB      Backend  Frontend Infra    AI Team
Schema  API      UI       CI/CD    (if needed)
│       │        │        │        │
└───────┴────────┴────────┴────────┘
        │
        ▼ Phase 5: Quality Gates (every PR, parallel)
┌───────┬────────┬────────┐
│       │        │        │
▼       ▼        ▼        ▼
Security Arch    PR
Engineer Review  Review
```

---

## Phase 1: Strategy

### Step 1.1 — Business Analysis
**Agent:** `business-expert`
**Input:** Raw idea description
**Output:** `workspace/{project}/business-analysis.md`

The business expert performs:
- Market sizing (TAM/SAM/SOM) using bottom-up and top-down approaches
- Competitive analysis via Porter's 5 Forces
- Business model assessment with unit economics (CAC/LTV)
- Go/No-Go recommendation

**Gate:** If verdict is NO-GO, present findings and require explicit user confirmation to continue.

### Step 1.2 — Product Requirements
**Agent:** `product-manager`
**Input:** `workspace/{project}/business-analysis.md` + original idea
**Output:** `workspace/{project}/prd.md`

The product manager produces:
- User personas with Jobs-to-be-Done framing
- RICE-prioritized user stories
- MVP feature scope (must be ruthlessly minimal)
- North Star metric + OKRs
- Success metrics

---

## Phase 2: Design + Architecture (run in parallel)

### Step 2.1 — UX Design
**Agent:** `ux-designer`
**Input:** `workspace/{project}/prd.md`
**Output:** `workspace/{project}/design-spec.md`

The designer produces:
- Complete design system (color tokens, typography, spacing, components)
- User flows for all MVP features
- Screen-by-screen layout specs with ASCII wireframes
- WCAG 2.2 AA accessibility compliance documentation

### Step 2.2 — Technical Architecture
**Agent:** `cto-architect`
**Input:** `workspace/{project}/prd.md`
**Output:** `workspace/{project}/technical-spec.md` + `workspace/{project}/api-spec.yaml`

The architect produces:
- C4 model (System Context, Container, Component diagrams)
- Technology stack selection with rationale
- Complete database schema (SQL DDL)
- OpenAPI 3.1 specification
- NFR definitions with measurable targets
- Deployment architecture (free-tier → production path)
- Architecture Decision Records

---

## Phase 3: Planning

### Step 3.1 — Roadmap + Linear
**Agent:** `project-manager`
**Input:** All workspace documents
**Output:** `workspace/{project}/roadmap.md` + Linear epics/issues

The project manager produces:
- Sprint-by-sprint roadmap (2-week sprints)
- Epic breakdown aligned to PRD features
- Dependency-mapped issues in Linear
- Critical path identification

---

## Phase 4: Development

Run Phase 0 (foundation) before all features.

### Phase 0 — Foundation (Sprint 1, always)
Run in this order (each step unblocks the next):

1. `db-engineer` — Initial schema + migration
2. `infra-engineer` — Docker Compose, CI/CD (parallel with step 1)
3. `backend-engineer` — App skeleton, auth, health endpoint
4. `frontend-engineer` — Next.js skeleton, layout, auth pages

### Phase 1+ — Feature Development
For each feature sprint:
- `backend-engineer` + `frontend-engineer` + `db-engineer` run in parallel
- Each produces a PR
- Every PR goes through Phase 5

---

## Phase 5: Quality Gates (every PR)

Run all three agents in parallel on every PR:

| Agent | Focus | Blocks Merge If |
|---|---|---|
| `security-engineer` | OWASP, STRIDE, CVEs | Any CRITICAL or HIGH finding |
| `architecture-reviewer` | Layer violations, NFRs, API compliance | Any BLOCKER finding |
| `pr-reviewer` | Code quality, tests, naming | Correctness bugs or untested public API |

All three must produce APPROVED or APPROVED WITH CONDITIONS before merge.

---

## Artifact Registry

| Artifact | Producer | Consumer(s) |
|---|---|---|
| `business-analysis.md` | business-expert | product-manager, ux-designer, cto-architect |
| `prd.md` | product-manager | ux-designer, cto-architect, project-manager |
| `design-spec.md` | ux-designer | frontend-engineer, project-manager |
| `technical-spec.md` | cto-architect | backend-engineer, frontend-engineer, infra-engineer, db-engineer, project-manager |
| `api-spec.yaml` | cto-architect | backend-engineer, frontend-engineer |
| `roadmap.md` | project-manager | all engineering agents |
| `src/` | engineering agents | quality gate agents |

---

## Time Estimates (rough)

| Phase | Duration |
|---|---|
| Business Analysis | 1 agent run |
| Product Requirements | 1 agent run |
| Design + Architecture | 2 parallel agent runs |
| Project Planning | 1 agent run |
| Foundation (Sprint 0) | 1-2 sprints |
| MVP Features | 2-4 sprints |
| Quality / Hardening | 1 sprint |
