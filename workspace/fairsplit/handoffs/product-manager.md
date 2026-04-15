# Product Manager Handoff

## Key Facts for Downstream Agents

1. **Product name:** FairSplit
2. **Primary persona:** Maya, The Trip Organizer — 28-year-old urban professional who pays upfront for the group and needs to settle debts afterward without being the unpaid group accountant.
3. **Core JTBD:** "When I'm on a group trip paying for things upfront, I want to log every expense as it happens and send everyone a simple payment plan at the end, so I can stop being the group's unpaid accountant and actually enjoy the trip."
4. **MVP features (in RICE priority order):**
   - Balance view with personal net balance display (RICE: 9,900)
   - Mobile-responsive design / PWA behavior (RICE: 9,900)
   - Copy settle-up plan to clipboard (RICE: 15,200 — highest score, minimal effort)
   - Expense logging with equal/custom-amount/custom-percentage splits (RICE: 4,950)
   - One-tap minimum-transfer settle-up algorithm (RICE: 4,950)
   - No-account group join via shareable link (RICE: 3,713)
   - Group creation with shareable link (RICE: 2,475)
   - Settlement recording / mark-as-paid (RICE: 3,600)
   - Expense edit and delete (RICE: 2,550 and 4,320)
   - Group invite link sharing with Web Share API (RICE: 3,800)
5. **Must-Have vs Should-Have split:** 10 Must-Have features, 3 Should-Have features (group archive/close, multi-currency, group admin role management)
6. **North Star metric:** Active Groups with a Completed Settle-Up — target 100 groups by Day 90 post-launch.
7. **Key differentiator:** The only expense splitter that is simultaneously free forever, requires no account to join, computes the minimum-transfer settle-up algorithm, and runs with zero external dependencies (`docker compose up` only).
8. **Explicit non-goals (MVP):**
   - No receipt scanning or OCR (requires external API — violates zero-dependency constraint)
   - No in-app payments (FairSplit is a ledger, not a payment rail)
   - No push notifications or email (no accounts = no notification address)
   - No native iOS/Android app (PWA first; native is Phase 2)
   - No currency auto-conversion (requires FX API — Phase 2)
9. **Technology constraints from PM perspective:**
   - Zero external services at any layer — no AWS, no OpenAI, no Stripe, no email provider in MVP
   - All monetary amounts must be stored and computed as integer cents (not floats) — non-negotiable for correctness
   - Session management is localStorage-based (JWT), with a mandatory cookie-based fallback for Safari ITP (clears localStorage after 7 days on iOS)
   - Settle-up algorithm must be unit-tested exhaustively — correctness is zero-tolerance; a wrong result destroys user trust immediately
   - Balance polling interval: 10 seconds (not WebSocket) for v1; revisit at 500+ concurrent users
10. **Top risk:** Safari on iOS clears localStorage after 7 days (Intelligent Tracking Prevention). If the session token disappears, returning users see the join screen again — creating confusion and perceived data loss. This must be mitigated with an httpOnly cookie session fallback before public launch.

---

## For UX Designer

- **Most important user flow to nail:** Group join via link → display name entry → first expense logged. This flow must complete in under 60 seconds with zero account creation. Any friction in this flow breaks the product's viral loop. Every screen transition must feel instant.
- **Persona to prioritize:** Maya (Trip Organizer) for the expense logging and settle-up flows. Daniel (Reluctant Participant) for the join flow — he is the hardest user to retain and the most common new user archetype.
- **Key interaction that differentiates from competitors:** The settle-up moment. When a user taps "Settle Up" and sees a clean, minimal list — "Daniel pays Maya $42, Jake pays Tom $18.50, done" — that is the product's emotional peak. The design must make this feel like magic: clean, authoritative, instantly shareable. Compare to Splitwise's cluttered balance matrix showing 15 pairwise arrows — FairSplit should feel like a calculator gave you the answer, not like you have to find it yourself.
- **Design constraints:**
  - Mobile-first (320px minimum width, 44px minimum touch targets)
  - Amount input fields must trigger numeric keypad on iOS/Android
  - Green = creditor (owed money), Red = debtor (owes money), Gray = settled — these conventions must be consistent across all balance-related UI
  - Empty states must be instructional and positive, never error-like
  - Form draft persistence (localStorage) must be invisible to the user — it just works
  - The settle-up plan must be copy-pasteable as plain text — the "Copy" button is a primary action, not secondary

---

## For CTO/Architect

- **Scale expectations at launch:** 100–500 concurrent users, 5–20 members per group, 50–200 expenses per group. Architecture must support 10,000 users without a rewrite.
- **Real-time requirements:** No hard real-time requirement. 10-second polling for balance updates is acceptable for v1. Settle-up algorithm runs synchronously per request (< 100ms for groups up to 50 members).
- **External integrations required in MVP:** None. Zero. This is a hard constraint.
- **Data privacy considerations:** No PII collected. Members are identified by display names only — no email, no phone, no real name required. Session tokens (JWTs) stored in localStorage and httpOnly cookies contain only `{group_id, member_id}` — no identifying information. No regulatory concerns in MVP (no financial data custody, no personal data under GDPR definition since display names are pseudonymous and user-chosen).
- **Critical algorithm:** The minimum-transfer settle-up uses a greedy max-heap approach. Full pseudocode is in PRD Section 6, Feature 5. Correctness test cases are specified there — implement them as unit tests before the algorithm is considered done.
- **Critical data constraint:** All monetary amounts stored as integer cents (e.g., $42.00 = 4200). Never use floating-point for money. All arithmetic is integer arithmetic. Rounding remainders (1 cent) assigned to the first creditor alphabetically.
- **Session architecture:** Two-layer session storage required — localStorage (primary, fast) + httpOnly cookie (fallback for Safari ITP). Session JWT payload: `{group_id: uuid, member_id: uuid, exp: unix_timestamp}`. Signed with server secret. 30-day expiry from last activity.
- **Database schema centers on:** Groups, Members, Expenses, ExpenseSplits, Settlements. Settle-up is computed at read time from these tables — not stored or cached.
- **Idempotency:** Both group creation and expense save endpoints must accept an idempotency key (client-generated UUID, sent in `X-Idempotency-Key` header) to prevent double-submission.
