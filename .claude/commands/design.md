Run the UX design phase for an existing project.

Produces design-spec.md (complete design system + screen specs) AND a working end-to-end HTML prototype in prototype/*.html.

Usage: /design <project-name>

Arguments: $ARGUMENTS

---

## Orchestration Rules

- Agent reads from `workspace/{project}/` (filesystem only — no direct agent communication)
- Produces execution report at the end

---

## Pipeline

### STEP 1: Verify prerequisites

Check that `workspace/{project}/prd.md` exists.
If missing: "Run `/ideate <idea>` first — the UX designer needs a PRD."

Read `workspace/{project}/handoffs/product-manager.md` if it exists.

### STEP 2: Launch UX Designer [SINGLE AGENT]

**Launch:** `ux-designer`
- Reads: `workspace/{project}/handoffs/product-manager.md` (primary), `workspace/{project}/prd.md`
- Writes:
  - `workspace/{project}/design-spec.md` — full design specification
  - `workspace/{project}/prototype/index.html` — entry point with navigation to all screens
  - `workspace/{project}/prototype/*.html` — one file per major screen
  - `workspace/{project}/handoffs/ux-designer.md` — compressed handoff note

Wait for completion.

### STEP 3: Verify prototype

Check that these files exist:
- `workspace/{project}/prototype/index.html`
- At least 3 additional `.html` files in `workspace/{project}/prototype/`

If missing, report which files were not produced.

### STEP 4: Execution Report

Append to or create `workspace/{project}/execution-report.md`:

```markdown
# Design Phase — Execution Report

**Pipeline:** /design
**Completed:** {datetime}

## Design System

| Token Type | Count | Primary |
|---|---|---|
| Colors | {N} | {primary color hex} |
| Type styles | {N} | {primary font} |
| Components | {N} atoms + {N} molecules + {N} organisms | — |

## Prototype

| Screen | File | Route |
|---|---|---|
| Entry point | `prototype/index.html` | / |
| {screen} | `prototype/{file}.html` | {route} |
| ...  | | |

**Open prototype:** `workspace/{project}/prototype/index.html`

## Key Design Decisions

1. {decision}: {rationale}
2. {decision}: {rationale}

## Accessibility

- WCAG 2.2 AA: {compliant / issues noted}
- Keyboard navigation: {implemented / partial}
- Color contrast: {all pass / issues noted}
```

### STEP 5: Summary to User

```
/design complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:   {project}
Screens:   {N} HTML pages in prototype/
Open now:  workspace/{project}/prototype/index.html
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next: /architect {project}  (then /build {project})
```
