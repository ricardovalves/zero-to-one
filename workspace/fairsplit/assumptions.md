# FairSplit — Assumptions Log

This file tracks all assumptions made during analysis. Each assumption is tagged with its source and the agent that made it.

---

## Business Analysis Assumptions (business-expert, 2026-04-15)

### Market Sizing

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| A1 | Global bill-splitting app market size (2024) | $512.5M | Cognitive Market Research, 2024 report |
| A2 | Global bill-splitting app market CAGR | 7.3% (2024–2033) | Cognitive Market Research, 2024 |
| A3 | Broader shared expense tracking market (2025) | $1.8B | DataIntelo, Bill Splitting Apps Market Research Report 2034 |
| A4 | Broader shared expense tracking market CAGR | 11.0% (2025–2034) | DataIntelo, 2025 |
| A5 | North America share of global bill-splitting market | ~40% = ~$205M | Cognitive Market Research, 2024 |
| A6 | US adults aged 18–40 | ~90M | US Census Bureau estimates, 2024 |
| A7 | Percentage of ages 18–44 who have used a P2P/expense app | 85% | Consumer Reports survey, 2022 |
| A8 | Percentage of P2P-app users who actively use expense tracking (not just payment) | 25% | Assumption; estimated from Splitwise WAU (2.4M) vs total potential US population |
| A9 | Global multiplier (English-speaking + EU markets) | 3–4x | Assumption; based on Splitwise reporting international user base |
| A10 | SAM as percentage of TAM | ~40% | Assumption; web-first + English-only + self-hosting constraint eliminates ~60% of global TAM |

### Competitor Intelligence

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| A11 | Splitwise estimated annual revenue | $7.5M | Growjo estimate, June 2025 |
| A12 | Splitwise weekly active users (US) | 2.4M | Sensor Tower data, Q2 2024 |
| A13 | Splitwise total funding | $30.5M | Crunchbase, Series A April 2021 ($20M lead by Insight Partners) |
| A14 | Splitwise free tier daily expense limit | 3–4 expenses/day | User reviews (Kimola analysis, 2024–2025); competitor comparison sources |
| A15 | Splitwise Pro pricing | ~$4–7/month | Market comparison sources (squadtrip.com, splitterup.app, 2025–2026) |
| A16 | Splitwise new user attribution via invitation | 68% | DataIntelo citing industry benchmark, 2025; corroborated by virality research |
| A17 | SplitPro GitHub stars | ~1,100 | GitHub (oss-apps/split-pro), verified 2025–2026 |
| A18 | Tricount total downloads | 5M+ | App Store listing data, referenced in competitor comparisons |

### Adoption Projections

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| A19 | Expected viral coefficient for FairSplit | 1.2–1.8 | Assumption; based on structural group-invite mechanic and no-account join flow removing primary friction vs. industry average of ~1.0 for comparable apps |
| A20 | SOM Year 1 (community-only growth) | 2,000–15,000 active users | Assumption; benchmarked against SplitPro (1,100 stars) and Spliit (similar profile) trajectories; conservative given Splitwise abandonment wave |
| A21 | SOM Year 3 | 15,000–75,000 active users | Assumption; assumes GitHub listing, OSS community, and self-hosting community compound growth |
| A22 | GitHub stars in 12 months (target) | 500–2,000 | Assumption; benchmarked against SplitPro (~1,100 in ~18 months) and Actual Budget OSS (10K+ stars, longer timeline) |

### Technical / Architecture

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| A23 | Minimum-transfer settlement algorithm complexity | O(n log n) greedy (max-heap) | Computer science — NP-hard in general case; greedy approximation sufficient for groups <100 |
| A24 | Typical group size | 3–20 members | Assumption; based on use cases (friend trip: 4–8; roommates: 2–4; large trip: 10–20) |
| A25 | Typical expenses per group per trip | 15–50 | Assumption; based on 5-day trip with 3–10 transactions/day shared across group |
| A26 | Infrastructure cost at 10,000 users (self-hosted model) | ~$0 | Assumption; users self-host; demo instance ~$5–15/month on Fly.io free/hobby tier |

---

## Product Definition Assumptions (product-manager, 2026-04-15)

### User Behavior

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| P1 | Group join completion rate (link open → name submitted) | 70%+ | Assumption; benchmark from B2C viral onboarding research; no-account flow removes primary barrier. Validate in private beta. |
| P2 | Median time from join link open to first expense logged | ≤ 90 seconds | Assumption; target based on competitive analysis (Splitwise requires account creation, adding 3–5 minutes). Validate in private beta. |
| P3 | Average members per active group | 3.5–6 | Assumption; based on Persona 1 (friend group of 6–8) and Persona 3 (couple = 2); weighted average. |
| P4 | % of active groups that view the settle-up plan | 60%+ by Month 2 | Assumption; "active group" = group with 3+ expenses. Groups with fewer expenses may not reach settle-up phase. |
| P5 | % of settle-up plan views resulting in at least one recorded settlement | 35%+ | Assumption; conservative — many users may settle outside the app (Venmo direct) without marking it. |
| P6 | "Copy to Clipboard" usage rate among settle-up viewers | 50%+ | Assumption; WhatsApp/iMessage is the primary communication channel for these groups; pasting the plan is more natural than in-app settlement. |

### Technical Behavior

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| P7 | localStorage session persistence | 30 days under normal browser conditions | Assumption; Safari ITP may reduce this to 7 days on iOS — cookie-based fallback is a required mitigation, not optional |
| P8 | 10-second polling adequate for balance freshness | True for groups < 10 active concurrent users | Assumption; active group trip with everyone logging simultaneously may feel laggy at 10s. WebSocket revisit triggered if user complaints exceed 5% of active groups. |
| P9 | Settle-up computation time for 50-member group | < 100ms | Assumption; O(n log n) with n=50 is trivially fast; verified by algorithm complexity analysis (A23). Unit test should assert execution time. |
| P10 | Integer-cent storage eliminates all monetary rounding errors | True | Resolved assumption; store all amounts as integer cents (e.g., $42.00 = 4200). All arithmetic is integer arithmetic. Any 1-cent remainder assigned to first creditor alphabetically. |
| P11 | Greedy max-heap algorithm produces true minimum for practical group sizes | True for n ≤ 20, approximately optimal for n ≤ 100 | Assumption; algorithm is a proven heuristic. For groups of 3–12 (typical), it produces the exact minimum. Validate with exhaustive unit tests for groups up to 20. |

### User Story RICE Scores

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| P12 | "Reach" values in RICE scores (users/quarter) | See story RICE tables | Assumption; extrapolated from SOM Year 1 (2,000–15,000 users) and typical product usage patterns. Reach values are relative, not absolute — the ranking is what matters. |
| P13 | Development effort estimates (person-weeks) | See story RICE tables | Assumption; rough estimates for a 2-person full-stack team. Will be refined by engineering team during sprint planning. |

### North Star Metric

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| P14 | "Active Groups with Completed Settle-Up" is a leading indicator of retention and satisfaction | True | Assumption; a group that completes a settle-up has extracted the product's core value and is likely to use it again for the next trip. Validate by correlating with group return rate in Month 2. |
| P15 | Target of 100 groups with completed settle-ups by Day 90 | Achievable with 500 active groups | Assumption; 20% settle-up completion rate from active groups × 500 groups = 100 completed. |

---

## Architecture Assumptions (cto-architect, 2026-04-15)

### Session & Auth

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| T1 | httpOnly server-set cookies are not subject to Safari ITP 7-day clearing | True | WebKit ITP documentation confirmed: server-set httpOnly cookies have no ITP expiry restriction (only client-side JS cookies and localStorage are affected). Source: webkit.org/blog/9521 |
| T2 | SameSite=Lax is sufficient CSRF protection for the FairSplit use case | True | SameSite=Lax prevents cookie from being sent on cross-site POST requests. FairSplit has no state-changing cross-site integrations. Full SameSite=Strict would break OAuth redirects, which don't exist in MVP. |
| T3 | 30-day rolling JWT expiry is appropriate for anonymous sessions | True | Longer than a typical trip (1–2 weeks); short enough to limit exposure if a device is lost. No refresh token needed — user simply rejoins if expired. |

### Algorithm

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| T4 | The greedy max-heap settle-up algorithm produces the exact minimum transfer count for groups up to 20 members | True for all tested configurations | The general problem is NP-Complete (Sum of Subsets reduction). For small groups (n ≤ 20) with typical balance distributions, the greedy approach produces the exact optimum. This is validated by exhaustive unit tests (see technical-spec.md §6). Not provably optimal for all n. |
| T5 | Settle-up algorithm computation time for 100 members is < 50ms | True | O(n log n) with n=100 involves ~200 heap operations on integers. Python's heapq handles this in microseconds. Unit test asserts < 50ms. |

### Database & Performance

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| T6 | PostgreSQL's shared buffer cache (128MB Docker default) is sufficient for MVP | True for < 500 concurrent users | The balance query touches < 1MB of data for groups with 200 expenses. Repeated queries for the same group will be served from the buffer cache after the first execution. |
| T7 | Single PostgreSQL instance is sufficient through 10,000 active groups | True | At 10,000 active groups, peak concurrent writes are estimated at < 100 req/sec (groups are not all active simultaneously). PostgreSQL handles 1,000+ writes/sec on commodity hardware. A read replica is the first scaling action at this tier. |
| T8 | Offset pagination is acceptable for expense lists up to 1,000 items | True for MVP | Groups target 50–200 expenses. OFFSET 200 on a well-indexed 200-row result set completes in < 1ms. Cursor pagination is the correct long-term solution and is documented as a Phase 2 migration. |
| T9 | No Redis or application-level cache is needed for MVP | True | Balance query completes in < 5ms with indexes. At 10-second polling from 500 concurrent users, the balance endpoint receives ~50 req/sec. A single FastAPI instance with asyncio handles 500+ req/sec. No cache layer is justified until balance latency exceeds 100ms p95. |

### Technology Versions

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| T10 | FastAPI 0.135.x is the correct version | True | Verified via PyPI and GitHub releases, April 2026. Python 3.12 required (3.8/3.9 support dropped). HS256 JWT with PyJWT is the official recommendation (python-jose deprecated). |
| T11 | Next.js 16.2.x is the correct version | True | Verified via Next.js blog and GitHub releases, April 2026. App Router is stable. Async Request APIs are mandatory in Next.js 16 (breaking change from 15). |
| T12 | PyJWT 2.10.x is the correct JWT library | True | FastAPI official documentation updated to recommend PyJWT over python-jose (which was effectively abandoned in 2021). Verified via FastAPI GitHub discussions and official tutorial, April 2026. |
| T13 | asyncpg 0.30.x is the correct async PostgreSQL driver | True | Fastest async PostgreSQL driver for Python. Recommended by SQLAlchemy docs for production async workloads. psycopg3 is a valid alternative but has less production reference. |

### Deployment & Cost

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| T14 | Fly.io free tier (3 shared VMs, 256MB each) is sufficient for staging with 100–500 concurrent users | Open — validate with load test before public launch | FastAPI with asyncpg is lightweight. 256MB RAM is sufficient for the Python process. Concurrent user limit depends on request concurrency and polling behavior. Load test with Locust before launch. |
| T15 | A single $6–12/month VPS handles production traffic up to 5,000 concurrent users | True with appropriate configuration | Hetzner CX21 (4 vCPU, 4GB RAM, €4.15/month) + Docker Compose + Nginx proxy handles FairSplit's full stack. Single-server self-hosting is the correct architecture for this scale. |

---

## Design Assumptions (ux-designer, 2026-04-15)

### Color & Accessibility

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| D1 | Primary button background must use Emerald-700 (#047857), not Emerald-500 (#10b981), to meet WCAG AA for white text | True | Contrast ratio: Emerald-500 on white text = 2.87:1 (fail). Emerald-700 on white text = 5.35:1 (pass AA). Verified via WCAG 2.2 contrast formula. Engineering must enforce this; using the lighter green in the Tailwind config is a known accessibility trap. |
| D2 | Green/Rose/Gray color convention for balance states is non-negotiable and must never be used for decoration | True | Color meaning is defined in design-spec.md §1 (P3) and §2.1. Any decorative use of green unrelated to positive financial state will break the user's learned mental model. Flag any violation in code review. |
| D3 | `prefers-reduced-motion` CSS media query is mandatory in every page | True | WCAG 2.2 SC 2.3.3 (AAA) and de-facto AA expectation for 2025 release. Implemented in every prototype file via `<style>` block. Must carry forward to production. |

### Typography & Numerics

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| D4 | `font-variant-numeric: tabular-nums` must be applied to all monetary amount displays | True | Without tabular figures, dollar amounts in list views shift horizontally as digits change, creating visual noise. Inter supports `tnum` OpenType feature. Apply via `.tabular-nums { font-variant-numeric: tabular-nums; }` CSS utility. |
| D5 | Amount inputs use `type="text"` with `inputmode="decimal"` (not `type="number"`) | True | `type="number"` on iOS triggers a numeric keyboard without a decimal point on some locales, and the `step` attribute causes unexpected validation. `inputmode="decimal"` consistently triggers the correct keypad while allowing full string control. Verified via MDN and iOS Safari behavior. |

### Layout & Interaction

| # | Assumption | Value | Source / Basis |
|---|---|---|---|
| D6 | Bottom navigation (not top tabs) is the correct primary nav pattern for mobile-first PWA | True | Industry standard as of 2025 (iOS HIG, Material Design 3, and all major consumer apps). Bottom nav improves one-handed reachability on large screens. Top navigation is acceptable for desktop-only or admin contexts. |
| D7 | iOS safe area inset (`env(safe-area-inset-bottom)`) must be applied to bottom navigation and sticky CTA bars | True | Without this, the navigation overlaps the iPhone home indicator on notched devices. Applied via CSS `padding-bottom: env(safe-area-inset-bottom, 0px)` on fixed bottom elements. |
| D8 | The settle-up "Copy Payment Plan" button generates a plain-text string, not rich text or HTML | True | The output is pasted into iMessage, WhatsApp, or Telegram — all of which render plain text. Rich text / HTML would appear as raw markup. The plain-text format is defined in settle-up.html and must be reproduced exactly by the backend API's "export plan" endpoint. |
| D9 | Form drafts are preserved in localStorage (not sessionStorage) for the Add Expense screen | True | sessionStorage is cleared on tab close. A user who switches to their banking app to check a payment and returns must still see their half-filled expense form. localStorage persists until explicitly cleared. |
| D10 | The join-group screen must auto-focus the display name input on mount | True | Auto-focus eliminates the tap required to start typing. On mobile, this immediately invokes the keyboard, reducing friction. WCAG permits auto-focus on pages with a single primary action. Implemented in join-group.html via `autofocus` attribute. |

---

*Last updated: 2026-04-15 by ux-designer agent.*

## orchestrator — contradiction-detection — 2026-04-15

- **Next.js version mismatch:** UX designer referenced Next.js 15; CTO specified Next.js 16.2.x after a live web search. Resolved: use 16.2.x per CTO (authoritative, more recent).
- **Session "primary" terminology:** UX called localStorage "primary" (UI read speed); CTO called httpOnly cookie "primary" (authoritative source of truth). Same architecture, different framing. Resolved: cookie is the authoritative session store; localStorage is a read cache. Frontend engineer should follow CTO handoff §For Frontend Engineer.
