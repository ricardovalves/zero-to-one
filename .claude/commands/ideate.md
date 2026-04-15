Run the strategic ideation phase: business analysis → full PRD.

Agents communicate only through the filesystem. Produces an execution report at the end.

Usage: /ideate <idea description>

Arguments: $ARGUMENTS

---

## Orchestration Rules

- Agents never talk to each other — all communication through `workspace/{project}/`
- business-expert and product-manager are sequential (PM reads BE's output)
- Produces `workspace/{project}/execution-report.md` at the end

---

## Pipeline

### STEP 1: Setup

Derive project slug from $ARGUMENTS. Create `workspace/{project}/handoffs/`.

---

### STEP 1b: Idea Sharpening

Present all four questions at once before launching any agent:

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

Wait for response. Then write `workspace/{project}/idea-brief.md`:

```markdown
# Idea Brief — {project}

**Original idea:** {from $ARGUMENTS}
**Primary user:** {answer or "not specified"}
**Current solution:** {answer or "not specified"}
**Core MVP action:** {answer or "not specified"}
**Business model:** {answer or "not specified"}

## Sharpened Brief

{2–3 sentence synthesis. Concrete, specific, no filler.}
```

---

### STEP 2: Business Analysis [SEQUENTIAL]

**Launch:** `business-expert`
- Reads: the idea from $ARGUMENTS
- Writes: `workspace/{project}/business-analysis.md` + `workspace/{project}/handoffs/business-expert.md`

Wait. Read `workspace/{project}/handoffs/business-expert.md`.

---

### GATE 1: Viability Check — MANDATORY STOP

Present the viability report to the user:

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

**If NO-GO:** Stop here. Do NOT offer to continue. Present the risks clearly and let the user decide.

**If CONDITIONAL GO or GO:** Ask: *"Do you want to proceed to product definition? (yes / no / adjust idea)"*

Wait for explicit user confirmation before moving to Step 3.

---

### STEP 3: Product Requirements [SEQUENTIAL — depends on Step 2]

**Launch:** `product-manager`
- Reads: `workspace/{project}/handoffs/business-expert.md` (primary), `business-analysis.md` (depth)
- Writes: `workspace/{project}/prd.md` + `workspace/{project}/handoffs/product-manager.md`

Wait. Read `workspace/{project}/handoffs/product-manager.md`.

---

### STEP 4: Execution Report

Write `workspace/{project}/execution-report.md`:

```markdown
# Execution Report: {project}

**Pipeline:** /ideate
**Completed:** {datetime}
**Status:** COMPLETE

---

## Business Case

| Metric | Value |
|---|---|
| Verdict | {GO / NO-GO / CONDITIONAL GO} |
| TAM | ${X}B |
| SOM Year 1 | ${X}M |
| Revenue Model | {model} |
| LTV:CAC | {X}x |

---

## Product Scope

| Item | Value |
|---|---|
| North Star | {metric} |
| Primary Persona | {name} — {role} |
| MVP Features | {N} Must-Have |
| Top RICE Feature | {feature} (score: {X}) |
| Key Differentiator | {one sentence} |

---

## Artifacts

| File | Status |
|---|---|
| `business-analysis.md` | ✓ |
| `prd.md` | ✓ |

---

## Key Decisions

1. {decision}: {what and why}
2. {decision}: {what and why}

---

## Next Steps

1. `/design {project}` → UX design system + working HTML prototype
2. `/architect {project}` → Technical architecture + API spec
3. Or run both with `/startup {project idea}` to continue from here
```

---

### STEP 5: Summary to User

```
/ideate complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:      {project}
Verdict:      {GO/NO-GO}
TAM:          ${X}B | SOM Year 1: ${X}M
North Star:   {metric}
MVP Features: {N} Must-Have ({top 2 by RICE})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Report: workspace/{project}/execution-report.md
```

Ask the user: *"Would you like to continue to design and architecture? I can run `/design {project}` and `/architect {project}` in parallel, or the full `/startup` pipeline if you haven't already done so. (yes to continue / no to stop here)"*

Wait for their response before proceeding.
