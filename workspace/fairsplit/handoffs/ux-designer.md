# UX Designer Handoff

## Key Facts for Downstream Agents

1. **Design system primary color:** `#047857` (Emerald-700) — Tailwind token: `brand-700`. Important: button backgrounds use `brand-700` not `brand-500` — `brand-500` (#10b981) fails WCAG AA contrast for white text on normal-size text. All prototype files implement this correction.
2. **Font:** Inter (variable) — loaded from Google Fonts CDN (`https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700`). Font stack: `'Inter', system-ui, -apple-system, sans-serif`. Enable `font-variant-numeric: tabular-nums` on all monetary amounts.
3. **Component library base:** Tailwind CSS (CDN) — no shadcn/ui dependency in prototype; production can adopt shadcn. All design tokens are configured via `tailwind.config` in each HTML file.
4. **Prototype screens:** `index.html`, `create-group.html`, `join-group.html`, `dashboard.html`, `add-expense.html`, `settle-up.html`, `expense-detail.html`, `empty.html`.
5. **Primary user flow:** Join via link → `join-group.html` → display name input → `dashboard.html`. Target: complete in under 60 seconds. No account creation at any point.
6. **Critical interaction:** The settle-up moment on `settle-up.html` — "Mark as Settled" per transfer, confetti celebration on all-settled state, "Copy Payment Plan" as a primary sticky CTA. This screen is the emotional peak of the product. The copy button writes a plain-text payment plan to the clipboard using `navigator.clipboard.writeText()`.
7. **Mobile breakpoint:** 640px (`sm:`) — primary responsive breakpoint. All layouts are mobile-first. Bottom navigation is fixed at 64px height + `env(safe-area-inset-bottom)` for iPhone safe area. Minimum touch target: 44×44px everywhere.
8. **Accessibility notes:** (a) Primary button bg must be `brand-700` (#047857) for WCAG AA — not `brand-500`. (b) All modals use `role="dialog" aria-modal="true"` with focus trap. (c) All form errors use `role="alert" aria-live="polite"`. (d) `prefers-reduced-motion` is handled via CSS media query in each file's `<style>` block — all transitions are suppressed. (e) Amount inputs use `inputmode="decimal"` (not `type="number"`) to trigger numeric keypad on iOS without triggering step validation.
9. **Design tokens:** Defined in each prototype file's `tailwind.config` script block. Full token spec in `design-spec.md` §2. Color convention enforced throughout: Green (`brand-*`) = owed money / settled / positive, Rose (`rose-*`) = owes money / negative, Slate (`slate-*`) = neutral/even.
10. **Known prototype limitations:** (a) No real API calls — all state transitions use `setTimeout()` to simulate network latency (900ms for create/join/add, 800ms for join). (b) No localStorage draft persistence is wired in prototype (the `beforeunload` handler in `add-expense.html` writes to sessionStorage for demo, not localStorage). (c) The settle-up confetti is CSS-particle-based, not a polished library. (d) The custom split percentage/amount inputs in `add-expense.html` are functional but do not wire back to a backend. (e) Dark mode not implemented in prototype — light mode only; design-spec does not specify dark mode as MVP requirement.

---

## For Frontend Engineer

- Prototype files in `workspace/fairsplit/prototype/` — use as pixel-perfect visual reference and interaction reference
- Tailwind config in each prototype file's `<script>` block is the source of truth for design tokens
- **Production stack recommendation:** Next.js 15 (App Router) + Tailwind CSS + shadcn/ui components. The prototype's pure-Tailwind components map directly to shadcn patterns:
  - `Button` → shadcn Button with custom brand variant
  - `Input` / `FormField` → shadcn Input + FormField
  - `Modal` → shadcn Dialog (add `side="bottom"` Sheet for mobile)
  - `Toast` → shadcn Sonner or react-hot-toast
  - `Dropdown` → shadcn Select
- **Critical UI patterns not to change:**
  - Green = owed, Rose = owes, Slate = even — this convention must be consistent across every balance display
  - Bottom navigation must be `position: fixed; bottom: 0` with `padding-bottom: env(safe-area-inset-bottom)` for iPhone notch
  - Amount inputs must use `inputmode="decimal"` + `type="text"` (not `type="number"`)
  - "Copy Payment Plan" button must use `navigator.clipboard.writeText()` with fallback
  - The settle-up transfer list is rendered from the minimum-transfer algorithm output — do not hardcode
- **Form draft persistence:** `add-expense.html` shows the pattern — on `beforeunload`, write form state to localStorage. On mount, check for draft and pre-fill. This is a must-have per PM requirements.
- **10-second polling:** The dashboard balance section should refresh via polling every 10 seconds using `setInterval` + SWR/React Query `refetchInterval`. Show no loading indicator for background refreshes — only show skeleton on initial load.

---

## For CTO/Architect

- **Real-time features needed:** None in MVP. 10-second polling acceptable. Balance display refreshes silently.
- **File upload/media requirements:** None. No receipt scanning, no images. Zero file storage needed in MVP.
- **External service UI integrations:** None. The only browser API used is `navigator.clipboard` (copy plan) and `navigator.share` (Web Share API for invite link). Both have graceful fallbacks in the prototype.
- **Settle-up algorithm output → UI mapping:** The frontend renders the minimum-transfer list as returned by the backend. The API should return an array of `{from: member_id, to: member_id, amount: integer_cents}`. The UI converts cents to dollars for display. The "Copy Plan" button formats this array into the plain-text format shown in `settle-up.html`.
- **Session architecture in UI:** After join/create, the JWT session token should be stored in both `localStorage` (primary) and an `httpOnly` cookie (fallback for Safari ITP). The UI should detect the absence of both and redirect to the join screen — not show an error.
- **Idempotency keys in UI:** The `add-expense.html` form should generate a UUID (`crypto.randomUUID()`) on mount and include it in the request as `X-Idempotency-Key`. Regenerate on successful submission. This prevents double-submission on slow connections.
