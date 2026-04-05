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

### STEP 2: Launch qa-engineer for regression test

Read `workspace/{project}/handoffs/debugging-and-error-recovery.md`.

If the handoff includes a "Regression Test Needed" section:

**Launch:** `qa-engineer`

Pass the handoff note. The qa-engineer will write a regression test that:
- Fails before the fix (encodes the bug)
- Passes after the fix (verifies the fix)
- Covers the full class of the bug, not just the exact reproduction

Wait for completion.

### STEP 3: Summary

```
/debug complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:    {project}
Bug:        {one-line description}
Root cause: {what was actually broken}
Fix:        {file}:{line} — {what changed}
Test:       {regression test file}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
