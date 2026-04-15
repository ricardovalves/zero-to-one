# Execution Report: fairsplit

**Pipeline:** /startup (full — strategic + engineering)
**Completed:** 2026-04-15
**Status:** COMPLETE

---

## Business Case

| Metric | Value |
|---|---|
| Verdict | GO |
| TAM | $1.8B (shared expense tracking, 2025) |
| SAM | $400–700M (English-speaking web users) |
| SOM (Year 1) | 2,000–15,000 active users |
| Business Model | Free — no monetisation |
| Top Competitor | Splitwise — weakness: 3-expense/day free-tier cap since 2024 |
| Moat | Free + no-account join + minimum-transfer algorithm — no competitor does all three |

---

## Product Scope

| Item | Value |
|---|---|
| North Star Metric | Active Groups with a Completed Settle-Up — target 100 by Day 90 |
| MVP Features | 10 Must-Have, 3 Should-Have |
| Primary Persona | Maya (Trip Organizer) — pays upfront, wants simple settle-up |
| Out of Scope | Receipt scanning, in-app payments, push notifications, native app, currency conversion |

---

## Design & Prototype

| Item | Value |
|---|---|
| Design System | #047857 (emerald-700), Inter (variable) |
| Prototype Screens | index, create-group, join-group, dashboard, add-expense, settle-up, expense-detail, empty |
| Key User Flow | Join via link → display name → dashboard (< 60 seconds, no account) |
| Hero Interaction | Settle-up screen: minimum-transfer plan + confetti on all-settled |
| Open in Browser | `workspace/fairsplit/prototype/index.html` |

---

## Architecture

| Layer | Technology |
|---|---|
| Frontend | Next.js 16.2.x (App Router, React 19) on Docker / Vercel |
| Backend | FastAPI 0.115.x + Python 3.12 on Docker / Fly.io |
| Database | PostgreSQL 16 (`postgres:16-alpine`) |
| ORM | SQLAlchemy 2.0 async + Alembic 1.14.x |
| Auth | JWT in httpOnly cookie (display name only — no email/password) |
| Monitoring | Prometheus + Grafana (auto-provisioned, no setup required) |
| CI/CD | GitHub Actions (CI on PR, CD on merge to main) |

---

## Key Engineering Decisions

1. **Minimum-transfer algorithm computed at read time** — not stored or cached. Greedy max-heap O(n log n), correct for groups < 100 members. 32 unit tests, all passing.
2. **Two-layer session model** — httpOnly cookie (authoritative, Safari ITP safe) + localStorage (read cache). Frontend falls back to `GET /members/me` before redirecting to join.
3. **All money as integer cents** — `amount_cents: int` throughout API, ORM, and DB. No float, no Decimal. Rounding remainders assigned to first creditor alphabetically.
4. **No-account group join via UUID invite token** — shareable link is the only auth needed. Anonymous members get a JWT bound to group_id + member_id.
5. **Idempotency keys on mutations** — `X-Idempotency-Key` header on POST /groups and POST /expenses prevents double-submission on slow connections.

---

## Delivery Plan

| Sprint | Dates | Goal | Points |
|---|---|---|---|
| 0 | Apr 20–May 03 | Foundation (DB, skeleton, Docker) | ~24 |
| 1 | May 04–May 17 | Group creation + auth + expense CRUD | ~36 |
| 2 | May 18–May 31 | Settle-up hero feature + settlements | ~32 |
| 3 | Jun 01–Jun 12 | CI/CD, polish, smoke tests, seed data | ~24 |

---

## Artifacts Produced

| File | Agent | Status |
|---|---|---|
| `business-analysis.md` | business-expert | ✓ |
| `prd.md` | product-manager | ✓ |
| `design-spec.md` | ux-designer | ✓ |
| `prototype/index.html` (+ 7 screens) | ux-designer | ✓ |
| `technical-spec.md` | cto-architect | ✓ |
| `api-spec.yaml` | cto-architect | ✓ |
| `roadmap.md` | project-manager | ✓ |
| `CLAUDE.md` | orchestrator | ✓ |
| `src/backend/` (full FastAPI app) | backend-engineer | ✓ |
| `src/backend/migrations/` (Alembic) | db-engineer | ✓ |
| `src/frontend/` (full Next.js 16 app) | frontend-engineer | ✓ |
| `src/docker-compose.yml` | infra-engineer | ✓ |
| `src/.github/workflows/` (CI + CD) | infra-engineer | ✓ |
| `src/infra/` (Prometheus + Grafana) | infra-engineer | ✓ |

---

## Warnings / Issues

- Frontend agent was interrupted mid-run and resumed — `ExpenseDetailClient.tsx` was created in the resume pass. All other pages were complete before interruption.
- Next.js version discrepancy between UX designer (referenced 15) and CTO (specified 16.2.x after live search) — resolved in favour of CTO. Logged in assumptions.md.
- No LINEAR_API_KEY set — Linear issues not created. Roadmap exists in `roadmap.md`.

---

## Next Steps

1. Open prototype: `workspace/fairsplit/prototype/index.html`
2. Run locally: `cd workspace/fairsplit/src && docker compose up`
3. Seed data: `docker compose exec backend python seed.py`
4. API docs: http://localhost:8000/docs
5. Dev panel: http://localhost:3000 (click-to-join seeded groups)
6. Grafana: http://localhost:3001 (admin/admin)
