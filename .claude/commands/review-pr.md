Run a full 3-agent parallel PR review: security, architecture, and code quality.

All three agents run simultaneously and independently via the filesystem. Results are aggregated into a unified report.

Usage: /review-pr <PR-url or branch-name or file-paths>

Arguments: $ARGUMENTS

---

## Orchestration Rules

- Three agents run in PARALLEL — they have no dependency on each other
- Each agent reads code files from the filesystem independently
- They do NOT communicate with each other
- Results are aggregated by the orchestrator (you) into one report
- Report is posted to GitHub if a PR URL is provided

---

## Pipeline

### STEP 1: Gather code to review

If $ARGUMENTS is a GitHub PR URL:
```bash
python tools/github_client.py get-pr --url "$ARGUMENTS"
python tools/github_client.py get-diff --url "$ARGUMENTS" --output /tmp/pr-diff.txt
```

Identify the project from file paths (e.g., `workspace/my-project/src/` → `my-project`).

Read changed files into context.

### STEP 2: Load compressed context (fast)

Read `workspace/{project}/handoffs/cto-architect.md` — architecture contract (used by all 3 agents).
Do NOT read full spec files — agents will read what they need.

### STEP 3: Launch all 3 review agents SIMULTANEOUSLY

**Launch all three in a single response (true parallel execution):**

| Agent | Focus | Reads |
|---|---|---|
| `security-engineer` | OWASP, STRIDE, CVEs, auth | Changed code + `handoffs/cto-architect.md` |
| `architecture-reviewer` | Layer violations, NFR compliance, API contract | Changed code + `handoffs/cto-architect.md` |
| `pr-reviewer` | Code quality, SOLID, tests, naming | Changed code only |

Wait for ALL THREE to complete before proceeding.

### STEP 4: Aggregate into unified report

```markdown
# PR Review: {PR title or branch}

**Date:** {datetime}
**Scope:** {N} files, +{insertions} -{deletions}
**Project:** {project}

## ⚡ Overall Verdict: {APPROVED / APPROVED WITH CONDITIONS / BLOCKED}

{If BLOCKED}: **This PR cannot merge. Fix the following before re-review:**
{list of CRITICAL/BLOCKER findings}

---

## Security Review — {APPROVED / BLOCKED}

{security-engineer full output}

---

## Architecture Review — {APPROVED / BLOCKED}

{architecture-reviewer full output}

---

## Code Quality Review — {APPROVED WITH NITS / CHANGES REQUESTED / BLOCKED}

{pr-reviewer full output}

---

## Consolidated Findings

| ID | Severity | Agent | Location | Summary |
|---|---|---|---|---|
| ... | CRITICAL | Security | `file:line` | ... |
| ... | BLOCKER | Architecture | `file:line` | ... |
| ... | CHANGE REQUESTED | Code Quality | `file:line` | ... |
| ... | NIT | Code Quality | `file:line` | ... |

## Action Required Before Merge

{Only BLOCKER + CRITICAL items, with specific fix instructions}
```

### STEP 5: Post to GitHub (if PR URL provided)

```bash
python tools/github_client.py post-review \
  --url "$ARGUMENTS" \
  --body-file /tmp/review-report.md \
  --event {APPROVE|REQUEST_CHANGES|COMMENT}
```

Map verdict to GitHub event:
- APPROVED → `APPROVE`
- APPROVED WITH CONDITIONS → `COMMENT`
- BLOCKED → `REQUEST_CHANGES`

### STEP 6: Enforcement

Print final verdict prominently:

```
PR Review Complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verdict: {APPROVED / BLOCKED}

Security:     {PASS / {N} findings}
Architecture: {PASS / {N} findings}
Code Quality: {PASS / {N} findings}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{If BLOCKED}: DO NOT MERGE. Fix {N} blocker(s) first.
{If APPROVED}: Safe to merge.
```
