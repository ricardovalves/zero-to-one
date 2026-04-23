Systematically diagnose and fix a bug or error. Follows a six-step triage: Reproduce → Localize → Reduce → Fix Root Cause → Guard Against Recurrence → Verify End-to-End. Hands off to qa-engineer to write the regression test.

Usage: /debug <project> <description of the bug or error>

Arguments: $ARGUMENTS

---

## Orchestration

Parse: first word = {project}, rest = {bug description or error message}.

Read `workspace/{project}/handoffs/` for prior context on the project before launching.

### STEP 1: Launch debugging-and-error-recovery agent

**Launch:** `debugging-and-error-recovery`

Pass the full bug description and any error messages from the arguments. The agent will:
1. Reproduce the failure
2. Localize the root cause
3. Apply a surgical fix
4. Write a handoff to `workspace/{project}/handoffs/debugging-and-error-recovery.md`
5. Verify the fix in the running stack

Wait for completion.

### STEP 2: Launch qa-engineer for regression test (mandatory — never skip)

Read `workspace/{project}/handoffs/debugging-and-error-recovery.md`.

**Launch:** `qa-engineer` — unconditionally. Every bug fix requires a regression test. There are no exceptions.

Pass the full handoff note. The qa-engineer will write a regression test that:
- Encodes the exact input that triggered the bug
- Covers the full class of the bug, not just the exact reproduction case
- Lives alongside the existing test suite so it runs on every future build

Wait for completion.

### STEP 3: Verify the regression test passes

After the qa-engineer writes the test, run the full test suite to confirm:

```bash
# Run inside Docker where deps are installed
docker compose exec backend pytest tests/ -x -q 2>&1 | tail -20
```

The new regression test must pass (the fix is already applied). If it fails, the test was written incorrectly — ask the qa-engineer to correct it before proceeding.

A regression test that cannot run is not a regression test.

### STEP 4: Summary

```
/debug complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:    {project}
Bug:        {one-line description}
Root cause: {what was actually broken}
Fix:        {file}:{line} — {what changed}
Test:       {regression test file and test name}
Result:     {N} tests passing, 0 failures
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
