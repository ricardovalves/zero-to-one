# Project Manager Handoff — FairSplit

**Date:** 2026-04-15  
**Authored by:** Project Manager Agent

---

## Key Decisions for Downstream Engineering Agents

1. **Sprint structure:** 3 sprints of 2 weeks each, starting 2026-04-20. Sprint 0 (Foundation) is Apr 20–May 3 and is a hard gate — no feature work begins until `docker compose up` runs cleanly and all engineers are unblocked.

2. **Critical path is explicit and protected.** The 10-issue chain `F-01 → F-02 → F-03 → F-04 → G-01 → E-01 → E-05 → S-01 → S-02 → S-05` is the critical path to the hero feature. Any delay on this chain delays the whole product. Assign the most senior available engineer to E-05 (balance CTE), S-01 (settle algorithm), and S-02 (settle-up endpoint).

3. **Settle-up algorithm has zero correctness tolerance.** S-01 (implementation) and S-10 (exhaustive unit tests) are treated as a single unit — S-10 must pass before S-02 is merged. The test cases are specified in the roadmap and cover 6 edge cases including the 3-member circular debt scenario and 1-cent remainder handling. Do not ship without all tests green.

4. **Safari ITP session recovery (G-08) is Sprint 1, not a post-launch fix.** The PM identified this as the product's top risk. G-05 (GET /members/me) and G-08 (frontend recovery logic) must ship in Sprint 1. The pattern: localStorage miss → call /members/me with cookie → restore token → never redirect to join without attempting recovery first.

5. **All monetary arithmetic is integer cents — no exceptions.** The backend stores `amount_cents: INTEGER`. The frontend sends string decimals; the backend converts. No float or NUMERIC type is used for money anywhere in the system. The 1-cent rounding remainder rule: assign to first creditor alphabetically by display_name. This applies in E-01 (expense creation) and S-01 (algorithm). Violation of this rule in any PR is a blocker.

6. **Sprint 1 is over-allocated — contingency plan is in the roadmap.** At 70% capacity across backend and frontend engineers, Sprint 1 has 52 pts of identified work. The contingency: if Sprint 1 is at risk, defer E-09 (expense detail edit/delete UI) to Sprint 2. The API endpoints (E-03, E-04) stay in Sprint 1 because the frontend can defer the edit/delete UI without blocking balance and settle-up work.

7. **Sprint 3 is the buffer sprint.** It is intentionally lighter (32 pts) to absorb any Sprint 2 carryover and to give infra and QA work the focus it needs. CI/CD (I-01, I-02), seed data (I-03), and smoke tests (I-07) are the Sprint 3 gates — nothing ships without all three.

8. **Parallel execution mandated in Foundation sprint.** DB engineer and infra engineer work in parallel on F-01 (Docker Compose) and F-02 (migrations). Backend and frontend engineers start their skeletons (F-03, F-05) on Day 1 of Sprint 0 — no waiting for F-02 to finish since skeleton work doesn't touch the DB.

9. **Dev panel (I-04) is mandatory, not optional.** It is gated on `NEXT_PUBLIC_SHOW_DEV_PANEL=true` (a Dockerfile ARG, set in docker-compose.yml — not NODE_ENV). It lists both seeded groups with click-to-join links per member (one admin, one regular per group). The seed script (I-03) is the source of truth for emails, names, and data — the dev panel and seed script must match exactly.

10. **Issue estimates are honest.** Estimates follow the story-point scale: 1=hours, 2=half day, 3=1 day, 5=2-3 days, 8=1 week. No issue in this roadmap is estimated above 8. E-05 (balance CTE) and S-01 (settle algorithm) are both at 5 points — treat them as 2-3 day items requiring focused work without context switching.

---

## Files Written

- `workspace/fairsplit/roadmap.md` — complete: epics, 40 Linear-ready issues with estimates and acceptance criteria, sprint plan, dependency map, risk register
- `workspace/fairsplit/handoffs/project-manager.md` — this file
