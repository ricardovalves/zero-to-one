# Workflow: Feature Development

This workflow covers adding a new feature to an existing project that has already gone through the strategy and architecture phases.

---

## Prerequisites

The following must exist before feature development begins:
- `workspace/{project}/prd.md` — feature must be in the backlog
- `workspace/{project}/technical-spec.md`
- `workspace/{project}/api-spec.yaml`
- `workspace/{project}/design-spec.md`

---

## Flow

```
[Feature Request]
       │
       ▼
[PM: Is it in the PRD?]
  ├── Yes → proceed
  └── No → update PRD first (invoke product-manager)
       │
       ▼
[Architect: Does it need API changes?]
  ├── Yes → update api-spec.yaml (invoke cto-architect with narrow scope)
  └── No → proceed with existing spec
       │
       ▼
[Designer: Does it need new screens/components?]
  ├── Yes → update design-spec.md (invoke ux-designer with narrow scope)
  └── No → proceed with existing design system
       │
       ▼
[Project Manager: Create Linear issue(s)]
       │
       ▼
[Development — parallel]
  ├── backend-engineer → API endpoints
  ├── frontend-engineer → UI components + pages
  └── db-engineer → migrations (if schema changes needed)
       │
       ▼ (PR opened)
[Quality Gates — parallel]
  ├── security-engineer
  ├── architecture-reviewer
  └── pr-reviewer
       │
       ▼
[Merge + Deploy]
```

---

## Step-by-Step

### Step 1: Scope Validation
Before writing code, validate:
1. Is this feature in the PRD (Must Have or Should Have)?
2. Is the API contract defined in api-spec.yaml?
3. Is the UI design defined in design-spec.md?

If any are missing, update the relevant spec first. Never implement against an undefined spec.

### Step 2: Issue Creation
The `project-manager` agent creates a Linear issue with:
- Title: `[Team] Implement: {Feature Name}`
- Description: full context, requirements, and acceptance criteria
- Estimate: story points
- Dependencies linked

### Step 3: Development

**If the feature touches the database:**
- `db-engineer` writes a new Alembic migration
- PR opened with just the migration first
- Quality gates run on the migration PR

**Backend implementation:**
- `backend-engineer` implements API endpoints per the api-spec.yaml
- Unit + integration tests written alongside
- PR opened; quality gates run

**Frontend implementation:**
- `frontend-engineer` implements UI per the design-spec.md
- Integrates with backend API using typed API client
- E2E test added for the complete user flow
- PR opened; quality gates run

### Step 4: Quality Gates
Every PR runs `/review-pr <url>`:
- Three agents in parallel: security, architecture, code review
- Any BLOCKER = PR cannot merge
- Engineer addresses all blockers; re-review if substantial changes

### Step 5: Merge + Deploy
- Merge triggers CD pipeline
- Backend deploys automatically (Railway/ECS)
- Frontend deploys automatically (Vercel)
- Post-deploy smoke test verifies the feature works in production

---

## Common Patterns

### API-Only Feature (no UI changes)
1. Update api-spec.yaml (if new endpoint)
2. backend-engineer implements
3. quality gates on backend PR
4. Merge

### UI-Only Feature (existing API)
1. Update design-spec.md (if new screens)
2. frontend-engineer implements
3. quality gates on frontend PR
4. Merge

### Full-Stack Feature (most common)
1. Update specs if needed
2. backend-engineer + frontend-engineer work in parallel
3. Backend PR merges first (or use feature flag to hide incomplete UI)
4. Frontend PR merges when backend is live
