Run the technical architecture phase for an existing project.

Produces a comprehensive technical specification (C4 architecture, full SQL DDL, NFRs, testing strategy, cost analysis, ADRs) and a complete OpenAPI 3.1 spec.

Usage: /architect <project-name>

Arguments: $ARGUMENTS

---

## Orchestration Rules

- Agent reads from `workspace/{project}/` (filesystem only)
- Produces execution report at the end

---

## Pipeline

### STEP 1: Verify prerequisites

Check that `workspace/{project}/prd.md` exists.
If missing: "Run `/ideate <idea>` first."

Read `workspace/{project}/handoffs/product-manager.md` if it exists.

### STEP 2: Launch CTO/Architect [SINGLE AGENT]

**Launch:** `cto-architect`
- Reads: `workspace/{project}/handoffs/product-manager.md` (primary), `workspace/{project}/prd.md`
- Writes:
  - `workspace/{project}/technical-spec.md` — complete architectural specification
  - `workspace/{project}/api-spec.yaml` — full OpenAPI 3.1 spec
  - `workspace/{project}/handoffs/cto-architect.md` — compressed handoff note

Wait for completion.

### STEP 3: Execution Report

Append to or create `workspace/{project}/execution-report.md`:

```markdown
# Architecture Phase — Execution Report

**Pipeline:** /architect
**Completed:** {datetime}

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | {framework} on {platform} |
| Backend | {framework} on {platform} |
| Database | {DB} on {platform} |
| Auth | {strategy} |

## API Coverage

| Count | Item |
|---|---|
| {N} | API endpoints defined in api-spec.yaml |
| {N} | Database tables designed |
| {N} | ADRs documented |
| {N} | NFR targets defined |

## Cost Analysis (prototype)

Monthly cost at launch: ~${X}/month ({breakdown})
Break-even at {N} users.

## Key Architectural Decisions

1. {ADR-001}: {decision summary}
2. {ADR-002}: {decision summary}
3. {ADR-003}: {decision summary}

## Open Technical Questions

{list any unresolved decisions}
```

### STEP 4: Summary to User

```
/architect complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:    {project}
Stack:      {frontend} + {backend} + {database}
Endpoints:  {N} API endpoints
DB Tables:  {N} tables
ADRs:       {N} decisions documented
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next: /build {project}
```
