Reduce complexity in existing code without changing behaviour. Run after a feature is built and tested, before PR review. Applies guard clauses, function extraction, nesting flattening, and deduplication. Verifies tests pass after each change.

Usage: /simplify <project> [path or feature]

Arguments: $ARGUMENTS

---

## Orchestration

Parse: first word = {project}, optional rest = {specific file path or feature area to simplify}. If no path given, simplify the most recently modified source files.

Read `workspace/{project}/handoffs/` for context on what was just built before launching.

### STEP 1: Confirm tests pass

Before launching the simplification agent, verify the baseline:

```bash
docker compose exec backend pytest tests/ -q 2>/dev/null | tail -3
```

If tests are failing, do not proceed — surface the failures to the user and suggest running `/debug {project}` first. Simplification on a broken baseline makes it impossible to confirm behaviour is preserved.

### STEP 2: Launch code-simplification agent

**Launch:** `code-simplification`

Pass the project name and scope (specific path or "recently modified files"). The agent will:
1. Read the target files
2. Apply simplification patterns one at a time
3. Run tests after each change
4. Produce a simplification report

Wait for completion.

### STEP 3: Summary

```
/simplify complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:       {project}
Scope:         {path or "recently modified files"}
Lines removed: {N} (net)
Files changed: {N}
Tests:         {N} passing (no regressions)

Top changes:
  {file} — {pattern applied, e.g. "guard clauses, -12 lines"}
  {file} — {pattern applied}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Next: /review-pr {project} to review the simplified code
```
