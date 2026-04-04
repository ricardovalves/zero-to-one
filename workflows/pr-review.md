# Workflow: PR Quality Gate

Every PR that modifies source code in `workspace/{project}/src/` must pass this quality gate before merging.

---

## Overview

Three agents review every PR simultaneously and independently. Their findings are aggregated into a unified report. Any single BLOCKER from any agent prevents the merge.

```
[PR Opened]
     │
     ├──────────────────────────────────┐
     ▼                                  ▼                      ▼
Security Engineer           Architecture Reviewer         PR Reviewer
(OWASP, STRIDE, CVEs)       (C4, NFRs, Layer integrity)   (Quality, Tests, Naming)
     │                                  │                      │
     └──────────────────────────────────┘
                          │
                    [Aggregate]
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
           BLOCKED   APPROVED WITH  APPROVED
         (blockers)   CONDITIONS   (clean)
```

---

## Security Engineer Checks

The `security-engineer` agent reviews for:

**OWASP Top 10 (2021):**
- A01 Broken Access Control — auth checks on all protected endpoints
- A02 Cryptographic Failures — no cleartext secrets, proper hashing
- A03 Injection — parameterized queries, no string interpolation in SQL/commands
- A04 Insecure Design — rate limits, business logic validation
- A05 Security Misconfiguration — CORS allowlist, no debug mode
- A06 Vulnerable Components — pip-audit / npm audit for new dependencies
- A07 Auth Failures — JWT validation, brute force protection
- A08 Software Integrity — lockfile committed, no supply chain risks
- A09 Security Logging — auth events logged, PII not logged
- A10 SSRF — user-supplied URL input validated

**STRIDE for new features:**
- Spoofing, Tampering, Repudiation, Information Disclosure, DoS, Elevation of Privilege

**Blocking thresholds:**
- CRITICAL finding → always blocks
- HIGH finding → blocks unless exception approved

---

## Architecture Reviewer Checks

The `architecture-reviewer` agent reviews for:

**Layer integrity:**
- Routers: HTTP concerns only (no business logic, no direct DB)
- Services: Business logic only (no SQLAlchemy, no HTTP)
- Repositories: Data access only (no business logic)

**API compliance:**
- Every new endpoint exists in api-spec.yaml
- Response format matches standard envelope
- Error format matches standard error schema

**NFR compliance:**
- No in-memory state preventing horizontal scaling
- No N+1 queries on tables > 10K rows
- External API calls have retry + timeout
- Observability maintained (logging, metrics)

**12-Factor compliance:**
- No hardcoded config (URLs, secrets, ports)
- Stateless request handling

**Blocking thresholds:**
- Layer violations → always blocks
- N+1 queries on large tables → blocks
- Hardcoded secrets → blocks (+ escalates to security-engineer)

---

## PR Reviewer Checks

The `pr-reviewer` agent reviews for:

**Correctness:**
- Edge cases handled (null, empty, zero, concurrent)
- Error paths propagated correctly
- No off-by-one errors

**Code quality:**
- Self-documenting names (no single-letter vars, no misleading names)
- Functions single-responsibility, < 40 lines
- Cyclomatic complexity < 10 per function
- No commented-out code
- DRY: no duplicated logic (threshold: 2 duplications)
- YAGNI: no speculative generality

**Testing:**
- Every new public function/method has tests
- Happy path + error path + edge cases
- No tests that only test mock calls
- Test names describe the scenario

**Type safety:**
- No TypeScript `any`, no Python unhandled `Optional`

**Blocking thresholds:**
- Correctness bugs → always blocks
- Untested public API → blocks
- Misleading names causing future bugs → blocks

---

## Unified Report Format

```markdown
# PR Review: {title}

**Overall Verdict:** BLOCKED | APPROVED WITH CONDITIONS | APPROVED
**Blocking Issues:** {N}

## Action Required Before Merge
{list of all BLOCKER/CRITICAL findings with locations and fixes}

## Security — {BLOCKED/APPROVED}
[security-engineer report]

## Architecture — {BLOCKED/APPROVED}
[architecture-reviewer report]

## Code Quality — {APPROVED WITH NITS/APPROVED}
[pr-reviewer report]
```

---

## Merge Policy

| Condition | Action |
|---|---|
| Any CRITICAL security finding | BLOCK — do not merge |
| Any HIGH security finding | BLOCK — requires documented exception |
| Any architecture BLOCKER | BLOCK — fix and re-review |
| Any code quality BLOCKER | BLOCK — fix and re-review |
| Only CHANGE REQUESTED items | May merge after fixing the listed items |
| Only NITs | APPROVED — fix NITs in follow-up PR or inline |
| All APPROVED | Merge freely |

---

## Re-Review Policy

After a blocked PR is updated:
- Only the agents that found blockers need to re-review (unless the fix touches unrelated areas)
- Use `/review-pr <url>` — it always runs all three agents fresh
- Do not re-merge a blocked PR without at least one re-review cycle
