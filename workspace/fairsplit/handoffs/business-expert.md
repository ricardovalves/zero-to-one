# Business Expert Handoff

## Key Facts (10 bullets — read this before opening business-analysis.md)

1. **Verdict:** GO — as a free, open-source demo/reference project. Not assessed for commercial viability (out of scope by design).
2. **TAM:** $1.8B global shared expense tracking market (2025) | Bill-splitting specific: $512.5M | User population: 57–76M potential users globally | **SAM:** ~$400–700M / 15–20M English-speaking web users | **SOM Year 1:** 2,000–15,000 active users via community channels (no marketing budget).
3. **Primary revenue model:** None — free by design. If ever commercialized, natural model is self-hosted free + managed hosting at $3–5/group/month, anchored below Splitwise Pro ($4–7/month).
4. **Top competitor:** Splitwise — 2.4M WAU (US), $7.5M ARR, $30.5M raised — key weakness: paywalled to 3 expenses/day on free tier since 2024, triggering mass abandonment and thousands of 1-star reviews calling it a "cash grab." This is the primary demand signal for FairSplit.
5. **LTV:CAC ratio:** Not applicable (free product). Adoption economics: marginal cost per user = $0 (self-hosted); viral coefficient expected at 1.2–1.8 (structurally above 1 due to shareable-link group join mechanic). 68% of expense app new users come from existing-user invitations (industry benchmark).
6. **Gross margin target:** Not applicable. Infrastructure cost at 10,000 users = ~$0 (users self-host; project pays only for its own demo instance).
7. **ICP:** Urban 25–35 year olds planning a group trip or starting a new roommate arrangement — the moment of zero switching cost (no historical data in another app, group forming fresh). Secondary ICP: developers and self-hosters seeking a clean reference implementation they can fork or deploy for their own group.
8. **Key differentiator:** The intersection of three constraints no competitor meets simultaneously — (1) completely free with no daily expense cap, (2) no account required to join a group (shareable link), and (3) minimum-transfer settlement algorithm that computes the optimal debt resolution path. The `docker compose up` zero-dependency architecture is the fourth differentiator for the developer audience.
9. **Top market risk:** Users expect a native mobile app (iOS/Android). A web-first product will lose users whose groups default to the App Store. Mitigation: PWA first, native wrapper later; target new groups rather than asking Splitwise users to migrate mid-usage.
10. **Recommended next step:** Build to `docker compose up` standard with real seed data, ship minimum-transfer algorithm as the hero feature, launch on GitHub + Hacker News (Show HN) + r/selfhosted. First validation metric: 100 GitHub stars in 30 days.

---

## For Product Manager

- **Biggest competitor gaps from user reviews (Splitwise):**
  1. 3-expense-per-day limit on free tier — makes it unusable during an active trip
  2. 10-second ads between expense entries on the free tier
  3. Aged, cluttered UI (designed 2011, minimally refreshed)
  4. Settlement routing not optimized — shows all balances but does not tell users the minimum number of transfers
  5. Account creation required for all group members — blocks viral adoption
  6. "Draft" mode missing — expense entry lost when switching to another app mid-input
  7. Single-currency default — frustrates international users

- **Pricing anchor:** Splitwise Pro $4–7/month, Settle Up Pro ~$3/month. FairSplit is $0 — this is the entire pricing strategy. Do not add a Pro tier to the MVP; it contradicts the product's identity.

- **Urgency argument:** Splitwise restricted the free tier in 2024. The community is actively mid-churn right now (2025–2026). Every week without FairSplit live is a week those users settle on Tricount or Spliit instead. The window to capture the abandonment wave is 12–18 months before the market restabilizes.

- **Key user flow to protect:** Group creation via shareable link → member joins without account creation → first expense logged in under 60 seconds. Any friction in this flow kills the viral loop. This is non-negotiable.

- **The settle-up moment is the hero feature.** The product should build toward it — every balance view should have a prominent "Settle Up" action that shows the minimum-transfer plan. This is the moment that creates "wow, this is so much better than Splitwise."

---

## For CTO/Architect

- **Budget constraint:** Prototype must run free-tier only — zero cloud accounts, zero credit cards, zero external APIs. This is a hard product constraint, not a technical preference. All dependencies must be open-source and Docker-runnable.

- **Scale at launch:** Design for 100–500 concurrent users, 5–20 members per group, 50–200 expenses per group. These are conservative numbers appropriate for a demo/reference project. The architecture should support scaling to 10,000 users without a rewrite.

- **Infrastructure budget at any scale:** ~$0 (self-hosted model). If a managed demo instance is run, target $5–15/month on a single VPS (Fly.io free tier or equivalent).

- **Algorithm complexity is the key engineering challenge:** The minimum-transfer debt settlement problem is NP-hard in the general case but solvable with a greedy algorithm (max-heap approach) for groups of <100 people in O(n log n). This must be implemented correctly and unit-tested exhaustively — it is the product's hero feature and correctness is non-negotiable.

- **No-account group join is the key architecture challenge:** Members join via a shareable link (UUID-based group token). They participate with a display name only — no email, no password. The group admin may optionally be a registered user. This session model needs careful design to prevent unauthorized expense editing.

- **Database:** PostgreSQL 16 in Docker. Schema centers on: Groups, Members, Expenses, ExpenseSplits, Settlements. The settle-up calculation is computed at read time (not stored), which keeps the write path simple.

- **Tech stack (per framework defaults):** Next.js 15 (App Router) for frontend, FastAPI for backend API, PostgreSQL 16 in Docker, no external storage needed (no file uploads in MVP), no billing, no email in MVP (shareable link replaces email invite). Auth is lightweight — group tokens for anonymous members, optional JWT for group admins.
