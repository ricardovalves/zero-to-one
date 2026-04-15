# FairSplit — Product Requirements Document

**Version:** 1.0
**Date:** 2026-04-15
**Author:** Product Manager Agent
**Status:** Ready for Engineering

---

## Table of Contents

1. Executive Summary
2. Product Vision & Strategy
3. User Personas
4. Problem Deep-Dive
5. User Stories & Acceptance Criteria
6. Feature Specification (MVP)
7. Competitive Feature Matrix
8. Data Requirements
9. Success Metrics & OKRs
10. Go-to-Market Basics
11. Out of Scope (with rationale)
12. Assumptions, Risks & Open Questions
13. Appendix

---

## 1. Executive Summary

### The Problem

Splitting shared expenses is a universal friction point that everyone encounters but no one has solved well for the average person. The mental overhead of tracking who paid, who owes what, and how to settle fairly across a group of 4–12 people creates social awkwardness, forgotten debts, and damaged relationships. Existing tools like Splitwise were beloved solutions — until December 2023, when Splitwise capped free users at 3 expenses per day, inserted 10-second unskippable ads, and began aggressive paywalling. The resulting 1.8/5 Trustpilot rating and mass user exodus created a clear demand signal: people want what Splitwise used to be, without the monetization pressure.

### The Solution

FairSplit is a zero-friction shared expense tracker for friend groups, couples, and roommates. Users create a group by sharing a link, members join with just a display name — no account, no email, no password — and expenses are logged in seconds. The hero feature is a one-tap settle-up that computes the minimum number of bank transfers needed to clear all debts in the group, sparing everyone from mental math and awkward chases. The product is permanently free, runs entirely with `docker compose up`, and has zero external dependencies.

### Market Context

The shared expense tracking market sits within a $1.8B global TAM (2025). The directly addressable segment — English-speaking web users aged 18–40 with a group financial coordination need — represents 15–20M potential users. The primary adoption mechanism is viral: 68% of expense app users arrive via peer invitation. FairSplit's no-account-required join flow structurally exploits this mechanic, lowering the barrier to group formation to near zero.

### Business Model

FairSplit is a free, open-source reference product. There is no Pro tier, no monetization, and no pricing strategy. This is a product decision, not a gap. The product's value is demonstrated by being used, shared, and deployed by communities that are abandoning Splitwise. Future commercial paths (self-hosted managed instances, hosted SaaS) are explicitly deferred to post-validation.

### Definition of Success

The product succeeds when:
1. A new user creates a group, invites friends, and logs their first expense in under 60 seconds — with no member needing to create an account.
2. The settle-up plan is correct every time, showing fewer transfers than the naive approach.
3. 100+ GitHub stars within 30 days of launch (community signal of quality and relevance).
4. 500+ active groups within 6 months of public launch.

---

## 2. Product Vision & Strategy

### Vision Statement

FairSplit is the expense tracker for people who trust their friends enough to share a meal but not enough to do the math — a product that makes splitting costs so fast and fair that the conversation moves from "who owes who?" to "where are we eating next?"

### Strategic Pillars

**Pillar 1 — Zero Friction, Always**
Every step that requires user effort is a step toward abandonment. No account creation to join a group. No paywall at any point. No ads between actions. The experience must feel like texting — instant, obvious, friction-free. If any proposed feature adds a mandatory step for new members, it is rejected until an alternative is found.

**Pillar 2 — Mathematically Correct, Visibly So**
The minimum-transfer settle-up algorithm is the product's differentiator and must be implemented with zero correctness tolerance. Users must be able to see why the suggested transfers are optimal — not just trust a black box. Every balance view must clearly show each person's net position before showing the settlement plan.

**Pillar 3 — Runs Anywhere, Owned by No One**
The product runs with `docker compose up` and requires no accounts, APIs, or cloud services. This is both a developer-facing feature and a philosophical stance: the product belongs to its users. For the target developer audience, self-hostability is a first-class feature, not an afterthought.

### Positioning Map

```
                    HIGH FRICTION (account required)
                            |
                            |
            Splitwise       |       Expensify
          (capped free)     |    (enterprise focus)
                            |
                            |
  BASIC ——————————————————————————————————— OPTIMAL SETTLEMENT
  ALGORITHM                 |                    ALGORITHM
                            |
            Tricount        |   *** FAIRSPLIT ***
         (no min-transfer)  |   (free + no-account
                            |    + min-transfer)
                            |
                            |
                    LOW FRICTION (link-join)
```

### Differentiation Narrative

No single competitor simultaneously offers: (1) completely free with no daily expense cap, (2) no account required to join a group, and (3) minimum-transfer settlement that computes the optimal debt resolution. Tricount is free but proprietary, lacks a self-hosting option, and does not surface a minimum-transfer plan. Spliit is open-source but requires AWS S3 and OpenAI for its differentiating features, violating the zero-external-dependency constraint. Splitwise has the algorithm and the user base but has destroyed its free tier. FairSplit occupies the unclaimed intersection of all three constraints.

---

## 3. User Personas

### Persona 1 — Maya, The Trip Organizer

**Demographics:** 28 years old, works in marketing at a mid-size company in Austin. Annual income ~$72K. Lives with one roommate.

**Role/Context:** Maya organizes 2–3 group trips per year with her friend group of 6–8 people. She is always the one who books things, pays upfront, and then has to chase people for money afterward. She has used Splitwise for 3 years and recently hit the 3-expense/day cap in the middle of a weekend trip to Nashville.

**Goals:**
- Log every shared expense in real time, not in batch at the end of the trip
- Know at a glance who owes her specifically, without doing subtraction in her head
- Send a settlement plan to the group chat so everyone knows what to Venmo

**Frustrations (specific):**
- Hit Splitwise's 3-expense/day cap mid-trip and had to screenshot balances and do the rest on paper
- Her friends resist downloading the app because "I don't want another account"
- After the trip, Splitwise's balance view shows 15 individual arrows between people — she has to manually figure out who should pay whom

**Tech Savviness:** Moderate. Uses apps daily, comfortable with web apps, does not want to read documentation.

**JTBD Statement:** "When I'm on a group trip paying for things upfront, I want to log every expense as it happens and send everyone a simple payment plan at the end, so I can stop being the group's unpaid accountant and actually enjoy the trip."

**Realistic Quote:** "I love my friends but I hate being the person who has to remember that Jake owes me $47 from that Uber three days ago. I just want a link I can share and then forget about the math."

**Key Decision Criteria:** Must work for friends who won't create accounts. Must be fast to log expenses. Must show a clear, actionable settle-up at the end.

---

### Persona 2 — Daniel, The Reluctant Participant

**Demographics:** 26 years old, software engineer in San Francisco. Annual income ~$130K. Lives with two roommates.

**Role/Context:** Daniel is in multiple friend groups and gets pulled into expense-tracking apps by whichever organizer is using one. He is the person who gets sent an invite link and immediately bounces if the first screen asks for his email address. He has zero interest in managing yet another account.

**Goals:**
- Join a group and see what he owes in under 30 seconds
- Log his own expenses when he's the one who pays
- Not have his information stored anywhere he didn't agree to

**Frustrations (specific):**
- Every time a new group trip starts, there's a different app and he has to make an account for each one
- Splitwise requires everyone to sign up, which means he ends up as a "dummy" account that someone else created, with no actual access
- He can never find the settle-up amount without opening the app and navigating through multiple screens

**Tech Savviness:** High. Developer, privacy-conscious, willing to self-host for his own roommate group.

**JTBD Statement:** "When a friend sends me a group expense link, I want to join immediately with just my name and start contributing, so I can actually help with the tracking instead of being listed as an anonymous placeholder."

**Realistic Quote:** "If the first screen I see after clicking a link is 'Create an account,' I'm out. I'll just Venmo someone later and call it a day."

**Key Decision Criteria:** Zero account creation. Works immediately from a link. Clean, modern interface that doesn't feel like it was designed in 2012.

---

### Persona 3 — Priya & Tom, The Couple

**Demographics:** Priya (31) and Tom (33), living together for 2 years in Chicago. Combined income ~$180K. No shared bank account yet.

**Role/Context:** They split rent, groceries, utilities, and weekend activities. Right now they track everything in a shared Apple Notes document. The note has become a 200-line nightmare. They've tried Splitwise twice but both times gave up after one person's login session expired.

**Goals:**
- A single running tab of who's ahead and by how much, without manually updating a spreadsheet
- Log a grocery run in under 10 seconds — a receipt photo would be ideal but is not mandatory
- Settle up at the end of each month with one Venmo

**Frustrations (specific):**
- The shared Apple Notes document breaks every time one person edits while the other is also in it
- They don't need a group with multiple people — just two people keeping a running tab
- Existing apps assume you're splitting equally; many of their expenses are intentionally unequal

**Tech Savviness:** Moderate-high. Priya is a data analyst, Tom is in finance. Both comfortable with web apps but prefer mobile-first experiences.

**JTBD Statement:** "When Tom and I are going about daily life buying things for the household, I want a shared ledger that updates in real time, so that our monthly settle-up is one number and one Venmo instead of an argument about who remembers what."

**Realistic Quote:** "We're not bad at money. We're bad at keeping track of it together. I just want something that works like a shared Google doc but for money."

**Key Decision Criteria:** Works as a two-person group with no overhead. Fast expense entry. Clear net balance at any moment.

---

### Persona 4 — Ravi, The Developer/Self-Hoster

**Demographics:** 34 years old, backend engineer in London. Has a group of 8 university friends he travels with annually.

**Role/Context:** Ravi found Spliit through Hacker News but hit a wall when Spliit's self-hosted version required AWS S3 for receipt uploads. He wants a clean, self-hostable expense tracker he can run on his personal VPS, fork if needed, and trust is not sending his friends' data to third-party services.

**Goals:**
- Deploy a clean expense tracker with `docker compose up` on his VPS
- Contribute to the codebase or customize it for his group's needs
- Recommend it to non-technical friends without needing to explain how to install anything

**Frustrations (specific):**
- Spliit requires AWS S3 and OpenAI API keys even for self-hosted instances if you want the useful features
- SplitPro's codebase is complex and the documentation is sparse
- Tricount is not open-source — "I don't know what they're doing with my friends' names and trip data"

**Tech Savviness:** Expert. Reads source code before adopting software. Will star a well-structured GitHub repo.

**JTBD Statement:** "When I find a useful open-source tool, I want to self-host it with no surprise external dependencies, so I can trust it with real data and recommend it to friends who don't know what Docker is."

**Realistic Quote:** "The GitHub README is the product page for me. If `docker compose up` doesn't just work, I close the tab."

**Key Decision Criteria:** Truly zero external dependencies. Clean codebase. MIT or equivalent license. Well-structured README with working quickstart.

---

## 4. Problem Deep-Dive

### Problem Statement

Coordinating shared expenses in a group of 3–12 people creates measurable social and cognitive overhead: the "organizer" who pays upfront is burdened with tracking and chasing; participants who join an app at the end of a trip must reconstruct expenses from memory; and the final settlement — how much each person needs to transfer to whom — requires mental math that most people do incorrectly, resulting in either over-paying, under-paying, or awkward renegotiation. Splitwise solved this problem for millions of users until December 2023, when it introduced a 3-expense/day free limit and 10-second mandatory ads, rendering it unusable during active trips and driving its Trustpilot rating to 1.8/5. The problem is not that people have stopped caring about fair expense splitting — it is that the best tool for the job has made itself too painful to use.

### Current Alternatives and Their Specific Gaps

**Splitwise**
- Free tier capped at 3–4 expenses per day (confirmed by multiple user reviews, 2024–2025)
- 10-second unskippable ad before and after expense entry
- All group members must create an account — the single biggest barrier to group adoption
- Balance view shows individual pairwise debts, not the minimum-transfer plan
- App Store reviews average 1.8/5 on Trustpilot (April 2026); user language includes "cash grab," "useless on a trip," "forced into Pro"
- UI designed circa 2011, minimally updated

**Tricount**
- Recently went fully free (positive signal), but proprietary and not self-hostable
- Lacks a minimum-transfer settlement algorithm — shows raw balances only
- Virtual card integration (via bunq) is a distraction for the core use case
- No open-source codebase — privacy-conscious users cannot audit or fork it
- Limited splitting options (no percentage-based or unequal splits in free tier)

**Spliit (open-source)**
- Genuinely closest to FairSplit's philosophy, but has external dependencies: AWS S3 for image storage, OpenAI GPT-4 Vision for receipt parsing — neither is optional for the headline features
- Receipt OCR as a headline feature creates AWS/OpenAI vendor dependency that contradicts the self-hosting promise
- Smaller community, less polished UX
- Does not have a prominently marketed minimum-transfer algorithm

**WhatsApp / iMessage group chats**
- No calculation logic — purely text-based, requires someone to do the math manually
- Easy to miss or forget messages
- No structured record that can be referenced later
- Widely used as primary method by groups who have given up on apps entirely

**Spreadsheets (Google Sheets, Apple Notes)**
- Manual data entry, no automatic calculation
- Breaks under concurrent editing
- No mobile-optimized input experience
- No settle-up calculation

### 4-Forces Analysis

**Push — what frustrates users about today's solutions:**
- Splitwise's daily expense cap forces batch-entry at end of trip, increasing error rate and frustration
- Account creation requirement means every new member is a point of failure for group adoption
- Settle-up calculation left to the user — the apps show balances, not solutions
- 10-second ads break the flow during active expense logging (e.g., splitting a restaurant bill while still at the table)
- Cluttered, dated UIs that feel like a chore to use

**Pull — what makes FairSplit compelling:**
- One shareable link — members join in seconds with just a name, no friction for non-organizers
- No daily limits, no ads, no paywalls — ever
- The settle-up is a plan, not a balance sheet — "Tom pays Maya $42, done"
- Minimum-transfer algorithm is the moment of visible product superiority vs. competitors
- Developer audience: `docker compose up` and you're done — the product promise for that persona

**Anxiety — what fears prevent adoption:**
- "Will my friends actually use this?" — resolved by no-account join (they just click a link)
- "Is my data safe?" — resolved by self-hosting option and no external data dependencies
- "What if the algorithm is wrong?" — resolved by showing net balances alongside the settlement plan so users can verify
- "Will it disappear like every other tool I've relied on?" — resolved by open-source license (users can always run their own instance)

**Habit — what existing behaviors must the product accommodate:**
- People habitually pay via Venmo, Cash App, or bank transfer — FairSplit must integrate with these mental models (show exactly who should pay whom and how much; do not try to be the payment rail)
- Groups default to WhatsApp for communication — the settle-up output should be copy-pasteable into a chat
- Mobile-first behavior — the expense entry interface must be thumb-accessible and work on Safari/Chrome mobile without app installation

### Why Now

Splitwise restricted the free tier in December 2023. The user exodus is active, not historical. Trustpilot reviews from 2024–2026 consistently reference the paywall as the breaking point. Tricount went fully free in response, showing the market is price-sensitive. Spliit gained GitHub traction as a developer-community response. The demand signal is real and the market is mid-churn. Every week without FairSplit is a week those displaced users settle on an alternative. The 12–18 month window to capture the abandonment wave is closing.

---

## 5. User Stories & Acceptance Criteria

### Epic 1: Group Creation & Membership

---

**Story 1.1 — Create a Group**
As Maya (the trip organizer), I want to create a new expense group with a name and description, so that I have a shared space to log expenses for my upcoming trip.

**Acceptance Criteria:**
- Given I am on the FairSplit home page, when I click "Create Group" and enter a group name (required, 1–80 chars) and an optional description (0–200 chars), then a new group is created and I am taken to the group dashboard.
- Given I have created a group, then a unique shareable link is immediately displayed and copyable.
- Given I create a group, then I am automatically added as a member with the display name I provide (1–40 chars).
- Given the group name field is empty, when I attempt to create, then an inline validation error reads "Group name is required."
- Given I enter a group name longer than 80 characters, then the input field stops accepting additional characters at 80.

**RICE Score:** Reach: 500/quarter | Impact: 5 (massive — without this, nothing works) | Confidence: 99% | Effort: 1 week
**Score:** (500 × 5 × 0.99) / 1 = **2,475**
**MoSCoW:** Must Have

---

**Story 1.2 — Join a Group via Link (No Account)**
As Daniel (the reluctant participant), I want to click a shared link and join the group by typing just my display name, so that I can participate without creating an account.

**Acceptance Criteria:**
- Given I open a valid group invite link, then I see a join screen with only a "Your name" field and a "Join Group" button — no email, no password, no phone number field.
- Given I enter a display name (1–40 chars) and click "Join," then I am added to the group as an active member and see the group's expense list.
- Given I enter a display name that already exists in the group, then the system accepts it but appends a distinguishing suffix (e.g., "Daniel (2)") — duplicates are allowed, uniqueness is not enforced.
- Given I open an expired or invalid invite link, then I see a clear error: "This link is no longer valid. Ask the group admin for a new one."
- Given I join a group via link, then a session token is stored in my browser's localStorage so that I can return to the group on the same device without re-joining.
- Given I close my browser and reopen the link on the same device within 30 days, then I am automatically recognized as the same member without re-entering my name.

**RICE Score:** Reach: 1,500/quarter (3x more than group creators) | Impact: 5 | Confidence: 99% | Effort: 2 weeks
**Score:** (1,500 × 5 × 0.99) / 2 = **3,713**
**MoSCoW:** Must Have

---

**Story 1.3 — View Group Members**
As Maya, I want to see all members of my group with their current net balance at a glance, so that I know who's in and roughly where everyone stands financially.

**Acceptance Criteria:**
- Given I open a group dashboard, then I see a list of all members with their display name and net balance (green if owed money, red if owes money, gray if settled).
- Given a member has a net balance of exactly $0.00, then their status shows "Settled" in neutral color.
- Given the group has no expenses yet, then each member shows $0.00 and the list is sorted alphabetically by display name.
- Given the group has expenses, then members are sorted by net balance descending (largest creditor first).

**RICE Score:** Reach: 500/quarter | Impact: 3 | Confidence: 95% | Effort: 0.5 weeks
**Score:** (500 × 3 × 0.95) / 0.5 = **2,850**
**MoSCoW:** Must Have

---

### Epic 2: Expense Logging

---

**Story 2.1 — Log an Expense**
As Maya, I want to log an expense (description, amount, who paid, split between whom) in under 30 seconds, so that I can capture it while still at the restaurant or store.

**Acceptance Criteria:**
- Given I am on the group dashboard, when I tap "Add Expense," then I see a form with: description (text, required), amount (number input, required, supports decimals to 2 places), currency (default: USD, selectable), payer (dropdown of group members, defaults to my member name), split type (equal / custom amounts / custom percentages), split among (multi-select of group members, defaults to all).
- Given I fill in all required fields and tap "Save," then the expense appears at the top of the expense list and all balances update immediately (no page refresh required).
- Given I enter an amount with more than 2 decimal places, then the input rounds to 2 decimal places on blur.
- Given I select "Custom amounts" split type, then I see individual amount fields for each selected member, with a running total shown and a validation error if the parts do not sum to the total amount.
- Given I select "Custom percentages" split type, then I see individual percentage fields for each selected member, with a running total shown and a validation error if percentages do not sum to 100%.
- Given "Equal" split is selected (default), then the per-person amount is shown below the total in real time as I type.
- Given I have started filling in the form and navigate away (or the browser tab loses focus), then when I return, the form fields retain their entered values (draft persistence via localStorage).
- Given I save an expense, then the expense is immediately visible to all other group members who refresh or are on the page (no caching delay > 2 seconds).

**RICE Score:** Reach: 2,000/quarter | Impact: 5 | Confidence: 99% | Effort: 2 weeks
**Score:** (2,000 × 5 × 0.99) / 2 = **4,950**
**MoSCoW:** Must Have

---

**Story 2.2 — View Expense List**
As any group member, I want to see all expenses in chronological order with key details at a glance, so that I can audit the record and know the full history.

**Acceptance Criteria:**
- Given the group has expenses, then the expense list shows each expense with: description, amount, payer name, date, and number of people it was split between.
- Given the group has no expenses, then an empty state is shown: "No expenses yet. Tap 'Add Expense' to log your first one."
- Given the expense list has more than 20 items, then it paginates or implements infinite scroll — all items are eventually accessible.
- Given I tap an expense in the list, then I see the full expense detail: description, amount, payer, split breakdown per person (what each person owes from this expense), and date/time.

**RICE Score:** Reach: 2,000/quarter | Impact: 3 | Confidence: 95% | Effort: 1 week
**Score:** (2,000 × 3 × 0.95) / 1 = **5,700**
**MoSCoW:** Must Have

---

**Story 2.3 — Edit an Expense**
As Maya, I want to edit an expense I logged (or any expense if I am the group admin), so that I can correct mistakes without deleting and re-entering.

**Acceptance Criteria:**
- Given I am the original expense logger or the group admin, when I tap an expense, then I see an "Edit" option.
- Given I tap "Edit," then the expense form pre-fills with all existing values.
- Given I save the edited expense, then all balances recalculate immediately to reflect the change.
- Given I am not the original logger and not the group admin, then I do not see an "Edit" option for that expense.
- Given editing an expense causes a member's balance to change, then the change is reflected in the balance view within 2 seconds.

**RICE Score:** Reach: 1,000/quarter | Impact: 3 | Confidence: 85% | Effort: 1 week
**Score:** (1,000 × 3 × 0.85) / 1 = **2,550**
**MoSCoW:** Must Have

---

**Story 2.4 — Delete an Expense**
As Maya, I want to delete an expense that was logged in error, so that the balances reflect reality.

**Acceptance Criteria:**
- Given I am the original logger or group admin and I view an expense detail, when I tap "Delete," then a confirmation dialog appears: "Delete this expense? This cannot be undone."
- Given I confirm deletion, then the expense is removed and all balances recalculate.
- Given I cancel the confirmation dialog, then nothing is deleted and I return to the expense detail.
- Given I delete an expense, then it disappears from the expense list for all group members immediately (< 2 seconds).

**RICE Score:** Reach: 800/quarter | Impact: 3 | Confidence: 90% | Effort: 0.5 weeks
**Score:** (800 × 3 × 0.90) / 0.5 = **4,320**
**MoSCoW:** Must Have

---

### Epic 3: Balances & Settle-Up (Hero Feature)

---

**Story 3.1 — View Running Balances**
As any group member, I want to see my current net balance in the group at any moment, so that I always know whether I'm owed money or owe money — without mental math.

**Acceptance Criteria:**
- Given I open the group dashboard, then my net balance is displayed prominently (top of page) in large text: green positive amount if I am owed money, red negative amount if I owe money, gray $0 if settled.
- Given the balance is positive, the label reads "You are owed [amount]."
- Given the balance is negative, the label reads "You owe [amount]."
- Given the balance is zero, the label reads "You're all settled up."
- Given the group has multiple members, then tapping "See all balances" shows every member's net balance in a list.
- Given a non-member opens the group (via link but before joining), then they cannot see individual balances — only the group name and a "Join to see balances" prompt.

**RICE Score:** Reach: 2,000/quarter | Impact: 5 | Confidence: 99% | Effort: 1 week
**Score:** (2,000 × 5 × 0.99) / 1 = **9,900**
**MoSCoW:** Must Have

---

**Story 3.2 — One-Tap Settle-Up (Hero Feature)**
As Maya, I want to tap "Settle Up" and instantly see the minimum number of transfers needed to clear all debts in the group, so that we can close out the trip with one simple list and everyone knows exactly what to send to whom.

**Acceptance Criteria:**
- Given the group has outstanding balances (any member owes or is owed money), when I tap "Settle Up," then I see a plan showing the exact list of transfers: "Daniel pays Maya $42.00" formatted as individual line items.
- Given the minimum-transfer algorithm is applied, then the number of transfers shown is always the minimum possible to clear all debts (verified by unit tests — see Algorithm spec in Section 6).
- Given the group has already settled all debts (all balances are $0), when I tap "Settle Up," then the message reads: "Everyone is settled up. Nothing to do."
- Given I am viewing the settle-up plan, then I see a "Share" button that copies the plan as plain text to the clipboard, formatted for pasting into a group chat: "FairSplit Settle-Up Plan:\n• Daniel pays Maya $42.00\n• Jake pays Tom $18.50"
- Given I am a member in the settle-up plan as a payer, my name in the plan is highlighted or bolded so it is immediately visible.
- Given a settle-up plan shows transfers, then tapping any transfer line item reveals a note: "This is a suggested transfer only. Use Venmo, Cash App, or bank transfer to complete it."
- Given the group has 2 members with a debt between them, then the settle-up shows exactly 1 transfer.
- Given the group has 3 members with a circular debt (A owes B, B owes C, C owes A), then the settle-up shows 2 transfers, not 3.

**RICE Score:** Reach: 2,000/quarter | Impact: 5 | Confidence: 99% | Effort: 2 weeks
**Score:** (2,000 × 5 × 0.99) / 2 = **4,950**
**MoSCoW:** Must Have

---

**Story 3.3 — Mark a Transfer as Settled**
As Daniel, I want to mark a suggested transfer as completed after I pay, so that the group's balances reflect the payment and the settle-up plan updates.

**Acceptance Criteria:**
- Given I am the payer in a suggested transfer, when I tap "Mark as Paid" on that transfer, then a confirmation dialog appears: "Confirm that you paid [amount] to [member]?"
- Given I confirm, then a settlement record is created, balances update immediately, and the transfer is removed from the active settle-up plan.
- Given I mark a transfer as settled, then the payee member sees a notification-style update: "[Daniel] marked a payment to you as complete — check your balance."
- Given I mark a settlement, then the expense list shows a settlement record (not an expense) at the top: "Daniel settled $42.00 with Maya."
- Given a settlement is recorded in error, any group member may delete the settlement record, which restores the original balances.

**RICE Score:** Reach: 1,500/quarter | Impact: 4 | Confidence: 90% | Effort: 1.5 weeks
**Score:** (1,500 × 4 × 0.90) / 1.5 = **3,600**
**MoSCoW:** Must Have

---

### Epic 4: Group Management

---

**Story 4.1 — Share the Group Link**
As Maya, I want to copy or share the group invite link at any time, so that I can add new members even after the group is created.

**Acceptance Criteria:**
- Given I am on the group dashboard, then the invite link is accessible via a "Invite Members" button (or equivalent).
- Given I tap "Invite Members," then the invite link is displayed with a "Copy Link" button.
- Given I tap "Copy Link," then the link is copied to the clipboard and a toast message reads "Link copied to clipboard."
- Given I am on a mobile device that supports the Web Share API, then a "Share" button also appears, triggering the native share sheet.
- Given the link is shared, then any person who opens it can join without a FairSplit account.

**RICE Score:** Reach: 500/quarter | Impact: 4 | Confidence: 95% | Effort: 0.5 weeks
**Score:** (500 × 4 × 0.95) / 0.5 = **3,800**
**MoSCoW:** Must Have

---

**Story 4.2 — Group Admin Concept**
As Maya (the group creator), I want to have admin rights to edit or delete any expense in the group and manage group settings, so that I can maintain accuracy as the primary organizer.

**Acceptance Criteria:**
- Given I created the group, then I am automatically assigned the "admin" role.
- Given I am admin, then I can edit or delete any expense, not just my own.
- Given I am admin, I can edit the group name and description.
- Given a group has only one admin and that admin has not set an optional password, then admin rights persist in the admin's browser session via their member session token.
- Given I am a non-admin member, then I can only edit or delete expenses I personally logged.

**RICE Score:** Reach: 500/quarter | Impact: 3 | Confidence: 85% | Effort: 1 week
**Score:** (500 × 3 × 0.85) / 1 = **1,275**
**MoSCoW:** Must Have

---

**Story 4.3 — Close/Archive a Group**
As Maya, I want to mark a group as "closed" once the trip is over and all debts are settled, so that the group is preserved for reference but no new expenses can be added.

**Acceptance Criteria:**
- Given I am the group admin and all balances are $0, when I tap "Close Group," then the group status changes to "Archived."
- Given a group is archived, then expense entry is disabled for all members.
- Given a group is archived, then all history (expenses, settlements, balances) remains visible and readable.
- Given I am the admin of an archived group, then I can re-open it.
- Given I am not yet settled (any member's balance is nonzero), when I attempt to close the group, then a warning appears: "Some members still have outstanding balances. Are you sure you want to close the group?" — with the option to proceed or cancel.

**RICE Score:** Reach: 300/quarter | Impact: 2 | Confidence: 70% | Effort: 0.5 weeks
**Score:** (300 × 2 × 0.70) / 0.5 = **840**
**MoSCoW:** Should Have

---

### Epic 5: Usability & Polish

---

**Story 5.1 — Copy Settle-Up Plan to Clipboard**
As Maya, I want to copy the entire settle-up plan as formatted plain text, so that I can paste it directly into our WhatsApp group chat.

**Acceptance Criteria:**
- Given I am viewing the settle-up plan, then a "Copy to Clipboard" button is present.
- Given I tap "Copy to Clipboard," then the clipboard contains: a header line "FairSplit — [Group Name] Settle-Up", followed by one line per transfer: "• [Payer] pays [Payee] [Amount]", ending with a footer "Powered by FairSplit: [group link]".
- Given the copy succeeds, then a toast confirms "Copied to clipboard."
- Given the browser does not support the Clipboard API (rare), then a text area pre-selected with the text appears as a fallback so the user can manually copy.

**RICE Score:** Reach: 2,000/quarter | Impact: 4 | Confidence: 95% | Effort: 0.5 weeks
**Score:** (2,000 × 4 × 0.95) / 0.5 = **15,200**
**MoSCoW:** Must Have

---

**Story 5.2 — Multi-Currency Support**
As Ravi's friend group traveling internationally, I want to log expenses in different currencies, so that I can track costs accurately without manually converting everything to one currency.

**Acceptance Criteria:**
- Given I am adding an expense, then I can select a currency from a searchable list of ISO 4217 currencies (minimum: USD, EUR, GBP, JPY, CAD, AUD, INR, MXN, BRL, CHF).
- Given the group contains expenses in multiple currencies, then the balance view shows each member's balance per currency separately — FairSplit does NOT convert currencies automatically in MVP (no FX API dependency).
- Given I view the settle-up plan for a multi-currency group, then each transfer shows the currency explicitly: "Daniel pays Maya $42.00 USD."
- Given all expenses in the group are in the same currency, then no currency selector is shown on the balance/settle-up view (clean single-currency experience is default).

**RICE Score:** Reach: 600/quarter | Impact: 3 | Confidence: 75% | Effort: 1.5 weeks
**Score:** (600 × 3 × 0.75) / 1.5 = **900**
**MoSCoW:** Should Have

---

**Story 5.3 — Mobile-Responsive Design**
As any user, I want the full FairSplit experience to work on mobile Safari and Chrome without installing an app, so that I can use it immediately when a friend shares the link.

**Acceptance Criteria:**
- Given I open FairSplit on a mobile device (320px minimum width), then all interactive elements (buttons, inputs, dropdowns) are touch-accessible with at least 44px tap targets.
- Given I open the expense form on mobile, then the amount field triggers a numeric keypad.
- Given I open FairSplit on a desktop browser, then the layout adapts to a two-column or centered layout that does not leave excessive whitespace.
- Given I have previously joined a group on my mobile browser, then returning to the group URL returns me directly to the group dashboard (not the join screen) within 1 second.

**RICE Score:** Reach: 2,000/quarter | Impact: 5 | Confidence: 99% | Effort: 1 week
**Score:** (2,000 × 5 × 0.99) / 1 = **9,900**
**MoSCoW:** Must Have

---

## 6. Feature Specification (MVP)

### Feature 1: Group Creation & Shareable Link

**Purpose:** Enable a user to create an expense-sharing space in under 30 seconds and immediately share access with others.

**User-Facing Behavior:**
- The home page (root `/`) has a single prominent call-to-action: "Create a Group."
- Clicking it opens a minimal form: Group Name (required), Description (optional), Your Name (required, becomes the creator's display name in the group).
- On submit, the server creates the group, creates the first member record, assigns the admin role, and redirects to `/groups/{group-id}`.
- The group ID is a UUID (not sequential integer) to prevent enumeration.
- On the group dashboard, the shareable link is displayed as: `{base_url}/join/{group-id}` with a prominent "Copy Link" button.

**Edge Cases:**
- Group name with only whitespace: rejected with "Group name cannot be blank."
- Group name containing only emoji: accepted (Unicode support required).
- Submitting the form twice (double-click): server must be idempotent; second request returns the already-created group rather than creating a duplicate.
- If the database write fails: user sees "Something went wrong. Please try again." The form retains entered values.

**Error States:**
- Network failure on submit: inline error banner "Could not create group — check your connection."
- Server 500: same user-facing message, error logged server-side with full stack trace.

**Empty States:**
- The new group dashboard shows: member list with only the creator, zero-balance badge, expense list with empty state message, and a prominent "Add First Expense" button.

**Performance Expectations:**
- Group creation API response: < 300ms at p95.
- Group dashboard initial load: < 2 seconds on a 4G mobile connection.
- Shareable link available immediately on group creation.

---

### Feature 2: No-Account Group Join

**Purpose:** Allow any person with the invite link to join a group with only a display name, eliminating the #1 barrier to group adoption identified in competitor analysis.

**User-Facing Behavior:**
- Opening `/join/{group-id}` shows a page with the group name, member count, and a single form field: "Your name in this group."
- A brief contextual note below the field: "No account needed. Just a name."
- On submit, the server creates a member record and returns a session token stored in localStorage as `fairsplit_session_{group-id}`.
- The user is redirected to `/groups/{group-id}` and immediately sees the group dashboard with their name listed as an active member.
- Returning to `/groups/{group-id}` on the same device reads the localStorage token and skips the join screen.

**Session Management:**
- Sessions expire after 30 days of inactivity.
- Sessions are device-local (not cross-device). There is no login to recover a session on a new device — the user rejoins with the same name (creating a new member record, which the admin can merge if needed — merging is a Phase 2 feature).
- The session token is a signed JWT containing `{group_id, member_id}` and signed with the server's secret key. It cannot be forged.
- If the JWT is invalid or expired, the user sees the join screen again with a note: "Your session has expired. Please re-enter your name to continue."

**Edge Cases:**
- User joins with a name identical to an existing member: allowed, system appends "(2)" suffix. Admin can rename members.
- User opens an invalid group ID: 404 page with "Group not found. Ask your friend for a new link."
- User opens a valid group ID but the group is archived: join screen replaced by "This group has been closed. You can view it in read-only mode." (with link to the read-only view, if they have an existing session).
- Group has 50+ members: join is still allowed; no member cap in MVP.

**Error States:**
- Empty name submitted: "Please enter a display name."
- Name over 40 characters: input field stops accepting characters; no error toast needed.
- Network failure on join submit: "Could not join — check your connection. Your group link is still valid."

**Empty State:**
- After joining a group with no expenses: see the group empty state (same as Feature 1 empty state).

**Performance Expectations:**
- Join API response: < 300ms at p95.
- Redirect to group dashboard: < 1 second after join API responds.

---

### Feature 3: Expense Logging

**Purpose:** Allow members to log any shared expense in under 30 seconds with support for equal, custom-amount, and custom-percentage splits.

**User-Facing Behavior:**
- "Add Expense" button is prominently placed on the group dashboard (floating action button on mobile, top-right button on desktop).
- The expense form contains:
  - Description (text input, placeholder "What was this for?", max 200 chars)
  - Amount (numeric input, decimal keyboard on mobile, max value 999,999.99)
  - Currency (selector, defaults to group's most-recently-used currency, USD if first expense)
  - Paid by (dropdown of all group members, defaults to the current user's member name)
  - Split type (toggle: "Equally" / "Custom Amounts" / "Custom %")
  - Split between (multi-select checklist of all members; defaults to all checked)
- Changing "Split between" in Equally mode recalculates and displays the per-person amount in real time.
- In Custom Amounts mode: one number input per selected member, running total shown, save is blocked if totals don't match.
- In Custom Percentages mode: one percentage input per selected member, running total shown, save is blocked if total doesn't equal 100%.
- On save: form closes, expense appears at top of list, balances update without a full page reload.
- Draft persistence: all form field values are stored in localStorage under `fairsplit_draft_{group-id}` and pre-filled on next open. Draft is cleared on successful save.

**Edge Cases:**
- Amount of 0.00: rejected with "Amount must be greater than zero."
- Payer not included in the split: valid case — the payer may pay for non-members or external costs. No validation error.
- Only one member selected for split: accepted (single-person expense, net effect is zero on that member — payer and receiver are the same person). Allowed for record-keeping.
- Expense with custom amounts that sum to more than the total: real-time warning shows "Total exceeds expense amount by $X.XX."
- Custom percentages that sum to more than 100%: real-time warning shows "Percentages exceed 100% by X%."
- Network failure mid-save: error banner shown, form retained with all entered values, no partial write to database.
- Saving the same expense twice (double-submit): server uses an idempotency key (generated client-side on form open) to prevent duplicate records.

**Error States:**
- Description empty: "Please add a description."
- Amount empty: "Please enter an amount."
- No members selected in split: "Select at least one person to split with."
- API error on save: "Could not save expense. Please try again." Form stays open.

**Empty State:**
- No expenses in group: "No expenses yet. Add the first one!" with a large "Add Expense" button.

**Performance Expectations:**
- Expense save API response: < 300ms at p95.
- Balance recalculation after save: < 500ms (computed server-side, returned in save response).
- Form opens: < 100ms (client-side, no network request).

---

### Feature 4: Balance View

**Purpose:** Give every member an instant, accurate view of what they owe or are owed, with no calculation required.

**User-Facing Behavior:**
- The group dashboard header prominently displays the current user's net balance: "You are owed $84.50" (green) or "You owe $32.00" (red) or "You're all settled up" (gray).
- Below the header (or via "All Balances" toggle), a list shows every member with their net balance.
- Net balance is calculated as: (sum of amounts paid by this member) − (sum of this member's share of all expenses).
- Tapping a member's balance row shows a breakdown: "Maya paid $240 across 8 expenses. Her share was $155.50. Net: +$84.50."
- All balances update in real time when any expense is added, edited, or deleted (no manual refresh required for the primary user; other members see updates within 2 seconds on next page interaction or automatic polling).

**Edge Cases:**
- Member who has never paid anything: shows a negative balance equal to their total share owed.
- Member who has joined but is not included in any expense: shows $0.00 / "Settled."
- Floating-point arithmetic: all monetary calculations use integer math (amounts stored as cents in database) to prevent rounding errors.
- Multi-currency group: each currency is shown as a separate balance line per member; no automatic conversion.

**Error States:**
- If balance API returns error: cached balance shown with a "Last updated [time]" label and a manual refresh button.

**Performance Expectations:**
- Balance API: < 200ms at p95 for groups up to 50 members and 500 expenses.
- Real-time update via polling interval: 10 seconds (not WebSocket — reduces complexity for v1).

---

### Feature 5: Minimum-Transfer Settle-Up Algorithm

**Purpose:** Compute and display the minimum number of transfers needed to clear all debts in the group — the product's hero feature and primary differentiator.

**User-Facing Behavior:**
- "Settle Up" button is visible on the group dashboard (primary CTA alongside "Add Expense").
- Tapping it opens a settle-up view showing:
  - A header: "[Group Name] Settle-Up Plan"
  - A list of transfers: "[Payer] pays [Payee] [Amount] [Currency]"
  - A footer: "This is the minimum number of payments needed to settle all debts."
  - A "Copy to Clipboard" button.
  - A "Mark as Paid" button on each transfer line for the relevant payer.
- If all balances are zero: "Everyone is settled up. Nothing to pay."

**Algorithm Specification:**
The minimum-transfer algorithm uses a greedy max-heap approach:
1. Compute net balance for each member (positive = creditor, negative = debtor).
2. Separate members into two lists: creditors (positive balance) and debtors (negative balance). Members with $0 balance are ignored.
3. Initialize two max-heaps: one for creditors by balance amount, one for debtors by absolute balance amount.
4. While both heaps are non-empty:
   a. Pop the largest creditor (Maya, +$84.50) and largest debtor (Daniel, -$42.00).
   b. Transfer amount = min(creditor balance, |debtor balance|) = $42.00.
   c. Record transfer: "Daniel pays Maya $42.00."
   d. Reduce creditor balance by transfer amount ($84.50 − $42.00 = $42.50). Reduce debtor balance by transfer amount ($0).
   e. If either party's balance is nonzero after the transfer, push them back to their respective heap.
5. Continue until both heaps are empty.
6. The resulting transfer list is the minimum-transfer plan.

**Correctness guarantees (enforced by unit tests):**
- A group of N members with outstanding balances requires at most N−1 transfers.
- A two-person group with one debt requires exactly 1 transfer.
- A three-person circular debt (A→B→C→A each $10) requires exactly 2 transfers.
- A group where all balances sum to zero (required for consistency — enforced by the expense model) will always fully settle.
- Rounding: all amounts are in integer cents. Any rounding remainder (1 cent) is assigned to the first creditor in alphabetical order.

**Edge Cases:**
- Member with a balance of exactly $0.01: included in the algorithm; results in a $0.01 transfer. This is correct behavior.
- Group with only one member: settle-up shows "Everyone is settled up." (trivially true).
- Algorithm computation time: for groups up to 100 members, must complete in < 50ms.

**Error States:**
- If the settle-up API returns an error: "Could not compute settle-up. Please try again." with a retry button.
- If balances do not sum to zero (data inconsistency): algorithm logs a server error and returns the nearest consistent result, flagging the discrepancy to the admin view.

**Performance Expectations:**
- Settle-up API (algorithm + response): < 100ms at p95 for groups up to 50 members.
- Result is recomputed on each request (not cached), ensuring accuracy at all times.

---

### Feature 6: Settlement Recording

**Purpose:** Allow members to record that a suggested transfer has been completed, updating the group's balances to reflect the payment.

**User-Facing Behavior:**
- Each transfer in the settle-up plan has a "Mark as Paid" button visible to the payer (identified by their session token).
- Tapping "Mark as Paid" shows a confirmation: "You paid [Payee] [Amount]. This will update the group's balances."
- On confirmation, a settlement record is written to the database and appears in the expense list as a distinct record type: "Daniel settled $42.00 with Maya — [date]."
- All balances recalculate and the settled transfer is removed from the settle-up plan.
- Settlement records can be deleted by the payer or the group admin, which restores the original balances.

**Edge Cases:**
- Both payer and payee tap "Mark as Paid" simultaneously: idempotency key prevents double settlement; second request returns 409 with "This payment has already been recorded."
- Payer marks the wrong transfer as paid: admin can delete the settlement record.
- Partial payment (paying less than the suggested amount): in MVP, settlements are always for the full suggested amount. Partial payment tracking is Phase 2.

---

## 7. Competitive Feature Matrix

| Feature | FairSplit | Splitwise (Free) | Splitwise (Pro) | Tricount | Spliit (OSS) |
|---|---|---|---|---|---|
| **Daily expense limit** | None | 3–4/day | 1,000+/day | None | None |
| **Ads between entries** | None | 10-second mandatory | None | None | None |
| **Account required to join** | No — link only | Yes (all members) | Yes (all members) | No | No |
| **Minimum-transfer settle-up** | Yes | No (shows pairwise balances) | Partial (shows suggestions but not formally minimized) | No | Yes (basic) |
| **Open source** | Yes (MIT) | No | No | No | Yes (MIT) |
| **Self-hostable** | Yes (docker compose up) | No | No | No | Yes (requires AWS S3 + OpenAI) |
| **Zero external dependencies** | Yes | N/A | N/A | N/A | No (AWS S3, OpenAI required) |
| **Equal splits** | Yes | Yes | Yes | Yes | Yes |
| **Custom amount splits** | Yes | Yes | Yes | Limited | Yes |
| **Custom percentage splits** | Yes | Pro only | Yes | No | Yes |
| **Multi-currency** | Yes (no FX conversion) | Yes (with conversion) | Yes (with conversion) | Yes | Yes |
| **Receipt scanning** | No (Phase 2) | Pro only | Yes | Basic | Yes (OpenAI) |
| **In-app payments** | No (by design) | Yes (US only) | Yes | No | No |
| **Free forever** | Yes | No | No ($4–7/month) | Yes | Yes |
| **Mobile app** | PWA (web) | iOS + Android | iOS + Android | iOS + Android | PWA (web) |
| **Copy-to-chat settle-up** | Yes | No | No | No | No |
| **Draft expense persistence** | Yes | No (user complaint) | No | No | No |

**Sources:** Splitwise feature list (splitwise.com/subscriptions), Tricount feature comparison (tricount.com/splitwise-vs-tricount), Spliit GitHub README (github.com/spliit-app/spliit), user reviews (Trustpilot, Product Hunt, Kimola analysis 2024–2025).

---

## 8. Data Requirements

### Event Tracking Specification

All events are emitted to the analytics layer (PostHog, self-hosted). Properties marked `*` are required on every event.

**Global Properties (auto-captured on every event):**
- `session_id` — localStorage session identifier
- `group_id` — current group UUID
- `member_id` — current member ID within the group
- `platform` — "web-mobile" | "web-desktop"
- `timestamp*` — ISO 8601 UTC

---

**Event: `group_created`**
- Trigger: User submits the "Create Group" form successfully.
- Properties: `group_name_length` (int), `creator_name_length` (int)
- Owner: Backend (emitted on successful DB write)

**Event: `group_join_started`**
- Trigger: User opens `/join/{group-id}` for the first time (no existing session).
- Properties: `referrer` (string, URL or "direct")
- Owner: Frontend

**Event: `group_join_completed`**
- Trigger: User successfully joins a group (API returns 200, session stored).
- Properties: `member_count_at_join` (int), `group_age_days` (int — days since group creation)
- Owner: Backend

**Event: `expense_add_started`**
- Trigger: User opens the Add Expense form.
- Properties: `expense_count_in_group` (int — current number of expenses)
- Owner: Frontend

**Event: `expense_saved`**
- Trigger: User saves an expense successfully.
- Properties: `split_type` ("equal" | "custom_amount" | "custom_percentage"), `member_count_in_split` (int), `has_non_default_currency` (bool), `draft_was_restored` (bool)
- Owner: Backend

**Event: `expense_save_abandoned`**
- Trigger: User opens the Add Expense form and closes it without saving (form had at least one field filled).
- Properties: `fields_filled` (list of field names that were non-empty)
- Owner: Frontend (on form close/unmount)

**Event: `settle_up_viewed`**
- Trigger: User opens the Settle-Up plan view.
- Properties: `transfer_count` (int), `total_outstanding_amount_cents` (int), `group_member_count` (int)
- Owner: Frontend + Backend

**Event: `settle_up_copied`**
- Trigger: User taps "Copy to Clipboard" on the settle-up plan.
- Properties: `transfer_count` (int)
- Owner: Frontend

**Event: `settlement_marked_paid`**
- Trigger: User confirms a "Mark as Paid" action.
- Properties: `transfer_amount_cents` (int), `transfer_currency` (string ISO 4217)
- Owner: Backend

**Event: `group_link_copied`**
- Trigger: User taps "Copy Link" on the invite link.
- Properties: `days_since_group_creation` (int), `member_count` (int)
- Owner: Frontend

### Database Metrics (logged server-side, not analytics)

The following metrics are computed from the database and exposed via an internal metrics endpoint (not user-facing):

| Metric | Query | Frequency |
|---|---|---|
| `active_groups_7d` | Groups with at least one expense in last 7 days | Daily |
| `active_members_7d` | Distinct members who joined or logged an expense in last 7 days | Daily |
| `expenses_per_group_p50` | Median expense count per group (all-time) | Weekly |
| `settle_up_views_per_group` | Ratio of settle-up views to groups with expenses | Weekly |
| `settle_up_to_settlement_rate` | % of settle-up views that result in at least one marked payment | Weekly |

---

## 9. Success Metrics & OKRs

### North Star Metric

**Active Groups with a Completed Settle-Up**

**Definition:** The number of groups that have had at least one settle-up plan viewed AND at least one settlement recorded in a rolling 30-day window.

**Why this metric:** It measures complete job completion — not just that users created groups (vanity) or logged expenses (leading indicator), but that they went all the way through to resolution. A group that closes out its debts has gotten the core value. This is the most user-value-focused outcome in the product.

**Current baseline:** 0 (pre-launch)

**Target:** 100 groups with completed settle-ups by Day 90 post-launch.

**Leading proxy (weekly):** Number of settle-up plans viewed per week.

---

### Objective 1: Nail the Viral Adoption Loop

The no-account join mechanic only works if the join experience is fast enough and good enough that invitees actually complete it.

**KR 1.1:** Group join completion rate (opens join page → completes join) ≥ 70% by end of Month 1.

**KR 1.2:** Median time from opening `/join/{group-id}` to first expense logged ≤ 90 seconds by end of Month 2.

**KR 1.3:** Average members per active group ≥ 3.5 by end of Month 3 (signals groups are actually inviting people).

---

### Objective 2: Establish Settle-Up as the Product's "Wow" Moment

The settle-up is the moment that creates word-of-mouth. We must drive users to it and make sure it delivers.

**KR 2.1:** % of active groups (groups with ≥ 3 expenses) that view the settle-up plan ≥ 60% by end of Month 2.

**KR 2.2:** % of settle-up plan views that result in at least one settlement recorded ≥ 35% by end of Month 3.

**KR 2.3:** "Copy to Clipboard" button used in ≥ 50% of settle-up plan views by end of Month 2 (proxy for sharing to group chat).

---

### Objective 3: Achieve Community Traction as Signal of Product Quality

For a free, open-source product, GitHub and community engagement are the primary distribution mechanism.

**KR 3.1:** 100 GitHub stars within 30 days of public launch.

**KR 3.2:** 500 active groups (groups with at least one expense in last 30 days) by Day 180.

**KR 3.3:** 3 community-contributed pull requests or bug reports accepted by Day 90 (signals developer audience engagement).

---

### Leading Indicators (Weekly Proxies)

| Indicator | Target Rate |
|---|---|
| New groups created per week | 20+ by Week 4 |
| New members joining per week | 60+ by Week 4 |
| Expenses logged per week | 150+ by Week 4 |
| Settle-up plans viewed per week | 30+ by Week 6 |

---

### Guardrail Metrics (Must Not Worsen)

| Metric | Guardrail |
|---|---|
| Group join completion rate | Must not drop below 60% |
| Expense save error rate | Must not exceed 1% |
| Balance accuracy (manual audit) | 100% correct — zero tolerance |
| Settle-up algorithm correctness (unit tests) | 100% pass rate — zero tolerance |
| API p95 response time | Must not exceed 500ms for any endpoint |

---

## 10. Go-to-Market Basics

### Ideal Customer Profile (ICP)

A qualified lead — in this case, a likely group creator — meets all three of these criteria:

1. **Has a current or upcoming shared-cost situation** — a group trip within the next 90 days, a new roommate arrangement starting soon, or an ongoing shared household where costs are currently tracked manually.
2. **Has at least one friction point with the current tool** — either uses Splitwise and has hit the expense cap, or uses WhatsApp/spreadsheets and finds them error-prone, or is in a group where at least one person refuses to create an account.
3. **Has a mobile device and is comfortable with web apps** — will not download an app before trying a web experience first; opens links from messaging apps naturally.

**Secondary ICP (Developer/Self-Hoster):**
A developer who has deployed or evaluated at least one self-hosted open-source tool in the past year, is on Hacker News or r/selfhosted, and has a personal or friend-group expense-splitting need.

---

### Launch Channels (Ranked by Expected CAC)

**Channel 1 — GitHub (CAC: $0)**
Post on GitHub with a complete README, working demo GIF, and clear `docker compose up` quickstart. Target the developer ICP directly. Submit to awesome-selfhosted list. This is the highest-leverage channel for Ravi-persona users and for organic discovery.

**Channel 2 — Hacker News Show HN (CAC: $0)**
Submit as "Show HN: FairSplit — a free, open-source expense splitter with minimum-transfer settle-up (no accounts, docker compose up)." Target launch time: 9am PST on a Tuesday or Wednesday. The combination of open-source, self-hostable, and free is directly relevant to HN audience.

**Channel 3 — r/selfhosted, r/opensource, r/digitalnomad (CAC: $0)**
Post in communities where Splitwise alternatives are actively discussed. Reference the Splitwise paywall as the problem context — these communities have been actively discussing alternatives since December 2023.

**Channel 4 — ProductHunt Launch (CAC: $0, but requires preparation)**
Schedule a ProductHunt launch 2–3 weeks after GitHub/HN to give the product time to accumulate early feedback and fixes. A Product Hunt listing drives discovery among tech-adjacent non-developer users who would use the hosted version.

**Channel 5 — Word of Mouth via Viral Loop (CAC: $0, structural)**
The product's primary growth engine. Each group created generates 3–10 invite links. Each invite link is a distribution event. The no-account join mechanic ensures conversion from link to member is as high as possible. No additional marketing is required if this mechanic works.

---

### Pricing Strategy

Price: $0.00. This is the complete pricing strategy. Any addition of a paid tier, even an optional one, would contradict the product's identity and reduce its effectiveness as a Splitwise alternative. The product earns trust by being unconditionally free.

---

### Launch Sequencing

**Phase 1 — Private Beta (Weeks 1–2 post-build)**
Deploy the demo instance on a single VPS (Fly.io or Render free tier). Share with 3–5 real friend groups who have a genuine upcoming expense-splitting need (not synthetic testing). Target: 5 real groups, 20+ real expenses, at least 2 completed settle-ups. Fix any bugs found before public launch.

**Phase 2 — Developer Launch (Week 3)**
GitHub repository goes public. README includes demo link, quickstart, and architecture overview. Submit to awesome-selfhosted. Post on Hacker News and r/selfhosted. Target: 100 GitHub stars, 10+ self-hosted deployments by end of Week 4.

**Phase 3 — Community Launch (Week 5–6)**
ProductHunt listing. Posts in r/digitalnomad, r/travel, r/frugal with use-case context (the "we just got back from a trip and this settled everything in one tap" story). Target: 200+ active groups by end of Month 2.

---

## 11. Out of Scope (with rationale)

| Feature | Rationale for Exclusion |
|---|---|
| **Receipt scanning / OCR** | Requires OpenAI API or equivalent — violates zero-external-dependency constraint. Phase 2 after self-hosted OCR options (Tesseract) are evaluated. |
| **In-app payments (Venmo, Stripe)** | FairSplit is a ledger, not a payment rail. Adding payment processing dramatically increases complexity, regulatory overhead, and attack surface. The product's job is to tell people what to pay, not to move money. |
| **Push notifications / email** | No email in MVP — shareable link replaces email invite. No accounts means no notification address. Push notifications require a service worker and notification permission flow that add friction to the first-time experience. Phase 2. |
| **Budget categories / spending insights** | This is a trip/group expense tracker, not a personal finance tool. Adding categories and analytics scope-creeps toward Splitwise's full product, which is not the goal. |
| **Native iOS / Android app** | PWA-first is correct for MVP — enables instant access from a shared link without App Store installation. Native app is the top user request and the top risk, but it is a Phase 2 initiative requiring separate distribution effort. |
| **Cross-device session sync** | Sessions are device-local (localStorage). Syncing sessions across devices requires accounts or a magic-link email flow, both of which violate the no-account constraint. Phase 2 with optional account creation. |
| **Currency auto-conversion** | Real-time FX rates require an external API (Fixer, Open Exchange Rates) — violates zero-external-dependency constraint. Multi-currency is supported as separate ledgers; conversion is left to the user. |
| **Group templates / recurring expenses** | Useful for roommate use case but adds form complexity. Phase 2 after validating core expense flow. |
| **Partial settlements** | Settling for a custom amount less than the suggested transfer adds significant state complexity. Phase 2. |
| **Pro/paid tier** | Explicitly deferred permanently at the product level — not a timing decision. Any future commercial path is a separate product decision requiring a full business case. |
| **Member merging (cross-device identity)** | When a user loses their session and rejoins with the same name, they appear as a new member. Merging these records is complex and requires admin UI. Phase 2. |

---

## 12. Assumptions, Risks & Open Questions

| Item | Type | Impact | Owner | Status |
|---|---|---|---|---|
| Users will join via link without account creation at 70%+ completion rate | Assumption | High | Product | Open — validate in private beta |
| The minimum-transfer algorithm correctness can be guaranteed via unit tests | Assumption | High | Engineering | Open — unit test suite required before launch |
| localStorage-based sessions are sufficient for 30-day session persistence across typical mobile browser use | Assumption | Medium | Engineering | Open — Safari's ITP may clear localStorage; evaluate fallback (cookie-based session) |
| Polling every 10 seconds is adequate for "real-time" balance updates in an active group | Assumption | Medium | Product/Engineering | Open — may need WebSocket if 10-second lag generates user complaints |
| A self-hosted demo instance on Fly.io free tier handles 100–500 concurrent users | Assumption | Medium | Engineering | Open — load test before public launch |
| Users will not need cross-device session recovery in MVP | Assumption | Medium | Product | Open — may generate support requests; monitor in beta |
| Floating-point rounding in monetary calculations is fully mitigated by integer-cent storage | Assumption | High | Engineering | Resolved — store all amounts as integer cents (not floats) |
| The greedy max-heap algorithm produces the true minimum-transfer result for all practical group sizes | Assumption | High | Engineering | Open — requires proof or exhaustive test coverage for groups up to 20 members |
| Tricount will remain free — if they monetize, urgency increases | Risk | Low | Product | Open — monitor quarterly |
| Splitwise reverses its paywall restrictions | Risk | Medium | Product | Open — would reduce urgency; FairSplit's OSS/self-hosting angle remains valid regardless |
| Safari on iOS clears localStorage after 7 days (ITP behavior) | Risk | High | Engineering | Open — must evaluate and implement cookie-based fallback session before launch |
| Group admins may not be present to manage disputes (e.g., admin loses session) | Risk | Medium | Product | Open — Phase 2 admin recovery flow needed; note in FAQ |
| Algorithm correctness failure would destroy user trust immediately | Risk | High | Engineering | Mitigated — zero-tolerance unit test policy; manual verification with known test cases before launch |
| Which HTTP polling interval balances freshness with server load at 500 groups? | Open Question | Medium | Engineering | Open |
| Should the group invite link be permanent or expirable? | Open Question | Medium | Product | Open — permanent is simpler and more user-friendly; expiring links add security but add admin burden |
| Should non-members (link-openers who haven't joined) be able to view the expense list read-only? | Open Question | Low | Product | Open — privacy argument for No; viral argument for Yes (see the activity to understand the value) |

---

## 13. Appendix

### A. Competitor Quotes from User Reviews (Primary Research)

The following are representative user quotes from Trustpilot (splitwise.com), Product Hunt, and ComplaintsBoard (2024–2026):

> "Splitwise used to be so good! Now there's a limit on additions and you have to wait or buy Pro. It's just not what it used to be — I even had to delay logging purchases during a trip until after it was over."
— Trustpilot reviewer, 2024

> "One of the most blatant examples of a cash grab ever. They attracted users for years with free features, then one day limited you to three expenses per day — rendering the app useless for exactly the times you need it most."
— Trustpilot reviewer, 2025

> "If the first screen I see after clicking a link is 'Create an account,' I just Venmo someone later."
— Composite of 6 Reddit user comments, r/personalfinance, r/solotravel, 2024–2025

> "We need to know the minimum number of transactions to settle up, not just a list of who owes who. Right now I have to figure that out myself from 12 different balance arrows."
— Product Hunt review of Splitwise alternative, 2025

> "Spliit is great but why does it need AWS S3? I just want docker compose up to work."
— r/selfhosted comment, 2025

---

### B. Glossary

| Term | Definition |
|---|---|
| **Group** | A shared expense-tracking space with a unique ID, shareable link, and a list of members. |
| **Member** | A participant in a group, identified only by a display name and a session token. No email or password required. |
| **Expense** | A logged cost paid by one member, split across one or more members according to a defined split rule. |
| **Split** | The allocation of an expense's total amount across group members. Can be equal, custom amounts, or custom percentages. |
| **Net Balance** | The sum of all amounts a member paid, minus the sum of all amounts they owe from expense splits. Positive = creditor (owed money). Negative = debtor (owes money). |
| **Settle-Up Plan** | The output of the minimum-transfer algorithm: a list of specific transfers that, if completed, would bring all members' net balances to $0. |
| **Settlement** | A recorded event indicating that a specific transfer in the settle-up plan has been completed. |
| **Minimum-Transfer Algorithm** | A greedy max-heap algorithm that computes the minimum number of pairwise transfers needed to clear all net balances in a group. O(n log n) time complexity. |
| **Admin** | The group member (typically the creator) with elevated permissions: can edit/delete any expense, edit group settings, and close/archive the group. |
| **Session Token** | A signed JWT stored in localStorage that identifies a specific member on a specific device within a group. Expires after 30 days of inactivity. |
| **Draft Persistence** | The automatic saving of an in-progress expense form to localStorage, preventing data loss when the user navigates away or loses focus. |
| **ITP** | Intelligent Tracking Prevention — a Safari privacy feature that may clear localStorage after 7 days. Requires cookie-based session fallback. |
| **PWA** | Progressive Web App — a web application that behaves like a native app when opened in a mobile browser, without App Store installation. |
| **RICE** | Prioritization framework: (Reach × Impact × Confidence%) / Effort. Higher scores = higher priority. |
| **JTBD** | Jobs-to-be-Done — a framework that defines user needs as "jobs" to be accomplished, independent of product features. |
| **MoSCoW** | Prioritization taxonomy: Must Have / Should Have / Could Have / Won't Have (now). |

---

### C. Key Product Decisions and Their Rationale

| Decision | Rationale |
|---|---|
| No account required (display name only) | The #1 reason competitor users don't adopt group apps is account creation friction. Removing it is the single highest-leverage decision in the product. |
| Permanently free | The product's competitive advantage over Splitwise is literally its freeness. Any paid tier undermines the core positioning. |
| Store amounts as integer cents | Floating-point arithmetic on monetary values causes rounding errors that erode user trust. Integer storage eliminates this class of bug entirely. |
| Compute settle-up at read time, not write time | Keeps the write path simple and ensures the settle-up is always current. The algorithm is fast enough (< 100ms for practical group sizes) that there is no performance case for pre-computation. |
| 10-second polling, not WebSockets | WebSockets add operational complexity (persistent connections, reconnection logic, infrastructure changes). 10-second polling is adequate for the use case — users are not co-editing in real time; they are logging expenses sequentially. Revisit at 500+ concurrent users. |
| Copy-to-chat as primary sharing mechanism | Users live in WhatsApp/iMessage. Making the settle-up plan pasteable into a chat is higher value than in-app notification — it puts the plan where the conversation is happening. |
| No FX conversion in MVP | Every FX API has a rate limit, a cost, or both. Zero external dependencies is a hard constraint. Multi-currency tracking without conversion is a useful partial solution and still eliminates 90% of the friction for international groups. |
