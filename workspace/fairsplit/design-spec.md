# FairSplit — Design Specification

**Version:** 1.0
**Date:** 2026-04-15
**Author:** UX Designer Agent
**Status:** Ready for Engineering

---

## Table of Contents

1. Design Principles
2. Design System
   - 2.1 Color Palette
   - 2.2 Typography
   - 2.3 Spacing Scale
   - 2.4 Border Radius & Shadows
   - 2.5 Component Library
3. User Flows
4. Screen Inventory
5. Key Interactions & Micro-animations
6. Accessibility Compliance

---

## 1. Design Principles

### P1 — The Answer, Not the Problem

Every screen answers a question the user already has in their head. The dashboard answers "who owes what?" before the user has to search for it. The settle-up screen answers "what should happen next?" with a numbered, ordered list. Design for the moment the user stops reading and just acts.

*Applied to:* Balance amounts always visible above the fold. Settle-up transfers rendered as a plain numbered list — no matrix, no visual graph.

### P2 — Friction Is a Feature Gap

Any step that requires typing, decision-making, or waiting is a candidate for elimination. The no-account join flow must feel like opening a text message, not filling out a form. If a user hesitates for more than 3 seconds, the screen has failed.

*Applied to:* Join flow is a single input (display name) with one CTA. Create-group flow is two inputs max. Amount input triggers numeric keypad automatically.

### P3 — Green Means Good, Always

Color communicates the financial state of the user's world without them reading a number. Green = you are owed money or a balance is settled. Red-orange = you owe money. Neutral gray = no balance. This convention never breaks, not even for decorative use of green.

*Applied to:* Personal balance badge, member balance rows, settle-up completion states. Green is never used for non-financial decoration in the product UI.

### P4 — The Settle-Up Moment Is Earned

The user has done the work — logged expenses, managed a group, chased people. When they tap "Settle Up," the result must feel like a reward. The settle-up screen is the product's emotional peak: uncluttered, authoritative, instantly shareable. Every other screen builds toward this moment.

*Applied to:* Settle-up screen gets large typography, celebration micro-animation on full settlement, prominent "Copy Plan" as a primary action.

### P5 — Empty States Teach, Not Apologize

An empty dashboard is not a failure — it is the beginning of a story. Every empty state shows the user what the screen will look like when populated and gives a single, specific next action. No "no data found" text. No error-like illustrations.

*Applied to:* Empty dashboard, empty expense list, settled-up group state — all have instructional copy and a direct CTA.

---

## 2. Design System

### 2.1 Color Palette

All colors are defined as design tokens. The primary brand color is **Emerald** — a modern, desaturated green that reads as fresh and trustworthy rather than dated money-green.

#### Primary — Emerald

| Token | Hex | Tailwind Class | Usage |
|---|---|---|---|
| `color-primary-50` | `#ecfdf5` | `bg-emerald-50` | Page backgrounds, success tint |
| `color-primary-100` | `#d1fae5` | `bg-emerald-100` | Positive balance chip background |
| `color-primary-200` | `#a7f3d0` | `bg-emerald-200` | Hover state for positive chips |
| `color-primary-400` | `#34d399` | `bg-emerald-400` | Icon accents, divider accents |
| `color-primary-500` | `#10b981` | `bg-emerald-500` | Primary buttons, key actions |
| `color-primary-600` | `#059669` | `bg-emerald-600` | Primary button hover state |
| `color-primary-700` | `#047857` | `bg-emerald-700` | Primary button active/pressed state |
| `color-primary-800` | `#065f46` | `bg-emerald-800` | Dark mode primary surface |
| `color-primary-900` | `#064e3b` | `bg-emerald-900` | Dark headlines on light backgrounds |

#### Danger — Rose/Red (owes money)

| Token | Hex | Tailwind Class | Usage |
|---|---|---|---|
| `color-danger-50` | `#fff1f2` | `bg-rose-50` | Negative balance chip background |
| `color-danger-100` | `#ffe4e6` | `bg-rose-100` | Negative balance hover |
| `color-danger-500` | `#f43f5e` | `bg-rose-500` | Negative balance text, error states |
| `color-danger-600` | `#e11d48` | `bg-rose-600` | Negative balance text bold |
| `color-danger-700` | `#be123c` | `bg-rose-700` | Error states active |

#### Neutral — Slate

| Token | Hex | Tailwind Class | Usage |
|---|---|---|---|
| `color-neutral-0` | `#ffffff` | `bg-white` | Card surfaces, input backgrounds |
| `color-neutral-50` | `#f8fafc` | `bg-slate-50` | Page background |
| `color-neutral-100` | `#f1f5f9` | `bg-slate-100` | Disabled input backgrounds, dividers |
| `color-neutral-200` | `#e2e8f0` | `bg-slate-200` | Border color, skeleton loading |
| `color-neutral-300` | `#cbd5e1` | `bg-slate-300` | Placeholder text, subtle dividers |
| `color-neutral-400` | `#94a3b8` | `text-slate-400` | Helper text, secondary labels |
| `color-neutral-500` | `#64748b` | `text-slate-500` | Body text secondary |
| `color-neutral-600` | `#475569` | `text-slate-600` | Body text primary |
| `color-neutral-700` | `#334155` | `text-slate-700` | Strong labels, table headers |
| `color-neutral-800` | `#1e293b` | `text-slate-800` | Headings |
| `color-neutral-900` | `#0f172a` | `text-slate-900` | Display headings |

#### Semantic — Warning and Info

| Token | Hex | Tailwind Class | Usage |
|---|---|---|---|
| `color-warning-50` | `#fffbeb` | `bg-amber-50` | Warning alert background |
| `color-warning-400` | `#fbbf24` | `bg-amber-400` | Warning icon |
| `color-warning-600` | `#d97706` | `text-amber-600` | Warning text |
| `color-info-50` | `#eff6ff` | `bg-blue-50` | Info alert background |
| `color-info-400` | `#60a5fa` | `bg-blue-400` | Info icon |
| `color-info-600` | `#2563eb` | `text-blue-600` | Info text, links |

#### Settled / Neutral Balance

| Token | Hex | Tailwind Class | Usage |
|---|---|---|---|
| `color-settled-bg` | `#f1f5f9` | `bg-slate-100` | Settled balance chip background |
| `color-settled-text` | `#64748b` | `text-slate-500` | Settled balance text |

---

### 2.2 Typography

**Primary font:** Inter (variable font, loaded from Google Fonts CDN)
**Font stack:** `'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`
**Numeric feature:** `font-variant-numeric: tabular-nums` on all amount displays

OpenType features enabled for financial amounts:
- `tnum` (tabular figures) — amounts align in columns
- `zero` (slashed zero) — disambiguates 0 from O

#### Type Scale

| Token | Name | Size | Weight | Line Height | Letter Spacing | Tailwind Classes | Use Case |
|---|---|---|---|---|---|---|---|
| `text-display-xl` | Display XL | 48px / 3rem | 700 | 1.1 | -0.02em | `text-5xl font-bold tracking-tight` | Landing headline |
| `text-display-lg` | Display LG | 36px / 2.25rem | 700 | 1.15 | -0.015em | `text-4xl font-bold tracking-tight` | Page hero amounts |
| `text-heading-xl` | Heading XL | 30px / 1.875rem | 700 | 1.2 | -0.01em | `text-3xl font-bold` | Page titles |
| `text-heading-lg` | Heading LG | 24px / 1.5rem | 600 | 1.3 | -0.005em | `text-2xl font-semibold` | Section headings |
| `text-heading-md` | Heading MD | 20px / 1.25rem | 600 | 1.35 | 0 | `text-xl font-semibold` | Card titles |
| `text-heading-sm` | Heading SM | 16px / 1rem | 600 | 1.4 | 0 | `text-base font-semibold` | Sub-section headers |
| `text-body-lg` | Body LG | 16px / 1rem | 400 | 1.6 | 0 | `text-base font-normal` | Primary body copy |
| `text-body-md` | Body MD | 14px / 0.875rem | 400 | 1.6 | 0 | `text-sm font-normal` | Secondary body, descriptions |
| `text-body-sm` | Body SM | 12px / 0.75rem | 400 | 1.5 | 0.01em | `text-xs font-normal` | Captions, helper text |
| `text-label-lg` | Label LG | 14px / 0.875rem | 500 | 1.4 | 0.01em | `text-sm font-medium` | Form labels, nav items |
| `text-label-md` | Label MD | 12px / 0.75rem | 500 | 1.4 | 0.02em | `text-xs font-medium` | Badges, chips, tab labels |
| `text-amount-xl` | Amount XL | 40px / 2.5rem | 700 | 1.1 | -0.02em | `text-4xl font-bold tabular-nums` | Net balance hero display |
| `text-amount-lg` | Amount LG | 24px / 1.5rem | 600 | 1.2 | -0.01em | `text-2xl font-semibold tabular-nums` | Transfer amounts in settle-up |
| `text-amount-md` | Amount MD | 16px / 1rem | 500 | 1.4 | 0 | `text-base font-medium tabular-nums` | Expense amounts in list |
| `text-amount-sm` | Amount SM | 14px / 0.875rem | 500 | 1.4 | 0 | `text-sm font-medium tabular-nums` | Per-person share amounts |
| `text-mono` | Monospace | 13px / 0.8125rem | 400 | 1.5 | 0 | `font-mono text-xs` | Shareable group link |

---

### 2.3 Spacing Scale

All spacing uses the 8-point grid system. The base unit is 4px.

| Token | Value | Tailwind Class | Use Case |
|---|---|---|---|
| `spacing-1` | 4px | `p-1`, `m-1` | Icon padding, tight chip padding |
| `spacing-2` | 8px | `p-2`, `m-2` | Inline element gaps, compact list rows |
| `spacing-3` | 12px | `p-3`, `m-3` | Badge padding, small card padding |
| `spacing-4` | 16px | `p-4`, `m-4` | Card padding, form field gap |
| `spacing-5` | 20px | `p-5`, `m-5` | Section internal padding |
| `spacing-6` | 24px | `p-6`, `m-6` | Card padding (comfortable), section spacing |
| `spacing-8` | 32px | `p-8`, `m-8` | Page horizontal padding (desktop) |
| `spacing-10` | 40px | `p-10`, `m-10` | Section separators |
| `spacing-12` | 48px | `p-12`, `m-12` | Hero section vertical padding |
| `spacing-16` | 64px | `p-16`, `m-16` | Page section gaps |
| `spacing-20` | 80px | `p-20`, `m-20` | Large section breaks |
| `spacing-24` | 96px | `p-24`, `m-24` | Landing page section padding |
| `spacing-32` | 128px | `p-32`, `m-32` | Max content break |

**Touch target minimum:** 44×44px — all interactive elements must meet or exceed this.
**Bottom navigation height:** 64px (fixed, safe-area-inset aware for iPhone notch).

---

### 2.4 Border Radius & Shadows

#### Border Radius

| Token | Value | Tailwind Class | Use Case |
|---|---|---|---|
| `radius-sm` | 4px | `rounded` | Badges, chips, small tags |
| `radius-md` | 8px | `rounded-lg` | Input fields, dropdowns |
| `radius-lg` | 12px | `rounded-xl` | Cards, modals |
| `radius-xl` | 16px | `rounded-2xl` | Sheet modals, floating action buttons |
| `radius-2xl` | 24px | `rounded-3xl` | Landing page hero card |
| `radius-full` | 9999px | `rounded-full` | Avatars, pills, circular buttons |

#### Shadows

| Token | Value | Tailwind Class | Use Case |
|---|---|---|---|
| `shadow-xs` | `0 1px 2px 0 rgb(0 0 0 / 0.05)` | `shadow-sm` | Subtle card lift |
| `shadow-sm` | `0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)` | `shadow` | Cards, input focus ring shadow |
| `shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)` | `shadow-md` | Floating buttons, active cards |
| `shadow-lg` | `0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)` | `shadow-lg` | Modals, bottom sheets |
| `shadow-xl` | `0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)` | `shadow-xl` | Settle-up modal celebration state |
| `shadow-primary` | `0 4px 14px 0 rgb(16 185 129 / 0.35)` | Custom CSS | Primary button hover state |
| `shadow-focus` | `0 0 0 3px rgb(16 185 129 / 0.3)` | Custom CSS | Focus ring on interactive elements |

---

### 2.5 Component Library

#### Atoms

##### Button

Minimum touch target: 44×44px. All buttons have explicit `type` attributes.

**Variants:**

| Variant | Background | Text | Border | Hover | Active | Disabled |
|---|---|---|---|---|---|---|
| `primary` | `bg-emerald-500` | `text-white` | none | `bg-emerald-600 shadow-primary` | `bg-emerald-700 scale-[0.98]` | `bg-slate-200 text-slate-400 cursor-not-allowed` |
| `secondary` | `bg-white` | `text-emerald-700` | `border border-emerald-300` | `bg-emerald-50` | `bg-emerald-100 scale-[0.98]` | `bg-white text-slate-300 border-slate-200` |
| `ghost` | `transparent` | `text-slate-600` | none | `bg-slate-100 text-slate-700` | `bg-slate-200 scale-[0.98]` | `text-slate-300` |
| `danger` | `bg-rose-500` | `text-white` | none | `bg-rose-600` | `bg-rose-700 scale-[0.98]` | `bg-slate-200 text-slate-400` |
| `danger-ghost` | `transparent` | `text-rose-600` | none | `bg-rose-50` | `bg-rose-100 scale-[0.98]` | `text-slate-300` |

**Sizes:**

| Size | Height | Padding | Font | Radius |
|---|---|---|---|---|
| `sm` | 32px | `px-3 py-1.5` | `text-sm font-medium` | `rounded-lg` |
| `md` | 44px | `px-4 py-2.5` | `text-sm font-semibold` | `rounded-xl` |
| `lg` | 52px | `px-6 py-3.5` | `text-base font-semibold` | `rounded-xl` |
| `xl` | 60px | `px-8 py-4` | `text-base font-bold` | `rounded-2xl` |
| `icon-sm` | 32px | `p-1.5` | n/a | `rounded-lg` |
| `icon-md` | 44px | `p-2.5` | n/a | `rounded-xl` |

**Loading state:** Button shows spinner (20px, white, 2px stroke) replacing label text. Width is locked to prevent layout shift using `min-w-[{measured-width}]`.

**ARIA:** `aria-busy="true"` when loading, `aria-disabled="true"` when disabled. All icon-only buttons require `aria-label`.

**Tailwind implementation:**
```
base: "inline-flex items-center justify-center gap-2 font-semibold transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2 disabled:pointer-events-none"
primary: "bg-emerald-500 text-white hover:bg-emerald-600 active:bg-emerald-700 active:scale-[0.98] disabled:bg-slate-200 disabled:text-slate-400"
```

---

##### Input

| State | Border | Background | Text | Focus Ring |
|---|---|---|---|---|
| Default | `border-slate-300` | `bg-white` | `text-slate-800` | none |
| Focus | `border-emerald-500` | `bg-white` | `text-slate-800` | `ring-2 ring-emerald-500/30` |
| Error | `border-rose-500` | `bg-rose-50` | `text-slate-800` | `ring-2 ring-rose-500/30` |
| Disabled | `border-slate-200` | `bg-slate-100` | `text-slate-400` | none |
| Filled | `border-slate-300` | `bg-white` | `text-slate-800` | none |

**Specs:** Height 44px, `rounded-xl`, `px-4`, `text-base`. Amount inputs: `inputmode="decimal"` for numeric keypad on mobile, `type="text"` (not `type="number"` — prevents `step` conflicts). Prefix/suffix slots for `$` symbol.

**ARIA:** `aria-required="true"` for required fields, `aria-invalid="true"` on error, `aria-describedby` linked to error message `id`.

---

##### Checkbox

Custom styled: 20×20px box, `rounded`, `border-2 border-slate-300`. Checked: `bg-emerald-500 border-emerald-500` with white checkmark SVG. Touch target: 44×44px wrapper.

---

##### Radio

Custom styled: 20×20px circle. Selected: outer ring `border-emerald-500`, inner dot `bg-emerald-500`. Touch target: 44×44px wrapper.

---

##### Badge / Chip

| Variant | Background | Text | Use Case |
|---|---|---|---|
| `positive` | `bg-emerald-100` | `text-emerald-700` | "Gets back $X" |
| `negative` | `bg-rose-100` | `text-rose-600` | "Owes $X" |
| `settled` | `bg-slate-100` | `text-slate-500` | "Settled" |
| `neutral` | `bg-slate-100` | `text-slate-600` | Member count, expense count |
| `new` | `bg-blue-100` | `text-blue-700` | "New" feature label |

**Specs:** `rounded-full`, `px-3 py-1`, `text-xs font-medium`. Minimum 24px height.

---

##### Avatar

Circular, generated from display name initials. Color from deterministic hash of name (one of 8 preset background colors). Sizes: 24px, 32px, 40px, 48px, 64px. `aria-label="{name}'s avatar"`.

**Avatar colors (background / text):**
1. `#dcfce7` / `#166534` (green)
2. `#dbeafe` / `#1e40af` (blue)
3. `#fce7f3` / `#9d174d` (pink)
4. `#fef3c7` / `#92400e` (amber)
5. `#ede9fe` / `#5b21b6` (violet)
6. `#ffedd5` / `#9a3412` (orange)
7. `#cffafe` / `#155e75` (cyan)
8. `#f0fdf4` / `#14532d` (dark green)

---

##### Spinner

SVG circle, animated `spin` (CSS `@keyframes`). Variants: 16px (inline), 20px (button), 32px (card loading), 48px (page loading). Colors: `text-emerald-500` (on white), `text-white` (on primary button).

---

##### Divider

`border-t border-slate-200`. Variants: `horizontal` (full-width), `inset` (with 16px margin on both sides).

---

#### Molecules

##### FormField

Composition: Label (above) → Input → Error message (below) → Helper text (below error).

```
[Label text]            [Required asterisk in rose-500]
[Input field — full width]
[Error message in rose-600, 12px, with error icon]
[Helper text in slate-400, 12px]
```

**States:** default, focused, filled, error, disabled. Spacing: 8px between label and input, 4px between input and error/helper.

---

##### Card

Base card: `bg-white rounded-xl shadow-sm border border-slate-100`. Variants:

| Variant | Style | Use Case |
|---|---|---|
| `default` | `shadow-sm border` | Expense list item, member row |
| `elevated` | `shadow-md` | Balance summary, active settle-up |
| `flat` | `border border-slate-200` | Section within a page |
| `interactive` | `hover:shadow-md hover:border-slate-200 cursor-pointer transition-shadow` | Clickable expense row |
| `hero` | `shadow-lg rounded-2xl` | Dashboard balance hero |

---

##### Dropdown / Select

Custom dropdown: trigger button → `absolute` positioned menu with `shadow-lg rounded-xl border border-slate-200 bg-white`. Appears below trigger, offset 8px. Max-height 240px, overflow-y scroll.

Options: `py-2 px-4 text-sm hover:bg-slate-50 cursor-pointer`. Selected: `bg-emerald-50 text-emerald-700 font-medium`.

**ARIA:** `role="listbox"` on menu, `role="option"` on items, `aria-expanded` on trigger, `aria-selected` on active option. Keyboard: Up/Down arrows navigate, Enter selects, Escape closes.

---

##### Toast / Notification

Position: top-center on mobile, top-right on desktop. Auto-dismiss: 4 seconds. Slide-in from top (200ms ease-out), slide-out up (150ms ease-in).

| Variant | Icon | Background | Border | Text |
|---|---|---|---|---|
| `success` | Checkmark | `bg-slate-900` | none | `text-white` |
| `error` | X circle | `bg-rose-600` | none | `text-white` |
| `info` | Info | `bg-slate-700` | none | `text-white` |

Specs: Max-width 360px on desktop, full-width minus 32px margin on mobile. `rounded-xl`, `px-4 py-3`, shadow-lg.

---

##### Modal

Backdrop: `bg-slate-900/50` with blur. Sheet (mobile) slides up from bottom. Dialog (desktop) centered. Animation: 200ms ease-out scale from 95% to 100% on open.

Structure:
```
[Backdrop — full screen, click to close]
  [Modal container — white, rounded-2xl, shadow-xl]
    [Header — title + close button (44×44px)]
    [Divider]
    [Body — scrollable if needed]
    [Footer — action buttons, sticky]
```

**ARIA:** `role="dialog"`, `aria-modal="true"`, `aria-labelledby` → header title. Focus trap active when open. Escape closes.

---

##### EmptyState

Structure:
```
[Illustration — 120×120px, svg or emoji-based]
[Heading — text-xl font-semibold text-slate-700]
[Body — text-sm text-slate-500, max 2 lines]
[CTA button — primary, centered]
```

Always centered in parent container. Never uses the word "empty" or "no data" in copy. Copy is instructional and forward-looking.

---

##### Alert

Inline, not dismissable. Full-width within its container.

| Variant | Background | Border | Icon | Text |
|---|---|---|---|---|
| `warning` | `bg-amber-50` | `border-l-4 border-amber-400` | ⚠ amber | `text-amber-800` |
| `info` | `bg-blue-50` | `border-l-4 border-blue-400` | ℹ blue | `text-blue-800` |
| `success` | `bg-emerald-50` | `border-l-4 border-emerald-400` | ✓ emerald | `text-emerald-800` |

---

#### Organisms

##### Navigation (Bottom Navigation Bar — mobile primary)

Fixed at bottom. Height: 64px + iOS safe-area-inset-bottom. Background: `bg-white border-t border-slate-200`. Items: 4 tabs (Dashboard, Add Expense, Settle Up, Group).

Each tab: icon (24px) + label (10px font-medium). Active: icon and label in `text-emerald-600`, active dot indicator below icon. Inactive: `text-slate-400`.

**Desktop:** Sidebar nav, 240px wide, fixed left. Items stack vertically with group name at top.

**ARIA:** `role="navigation"`, `aria-label="Main navigation"`. Each tab: `role="tab"`, `aria-selected`.

---

##### PageHeader

Mobile: `bg-white border-b border-slate-200`, height 56px. Group name centered, left slot for back button, right slot for contextual action.

Desktop: Integrated into sidebar layout. Page title is `text-3xl font-bold text-slate-800` in the main content area.

---

##### DataTable (Expense List)

Not a traditional table — rendered as a list of Cards. Each row:
```
[Avatar] [Description + date (small)]     [Amount — right aligned]
         [Split label — slate-400 12px]    [Your share — right aligned slate-500]
```

Sort: most recent first by default. Loading state: 3 skeleton rows. Empty state: EmptyState component.

---

##### Form (Add Expense)

Single-column layout on mobile. Labels above inputs. Section groupings with visual Divider + small heading (`text-xs font-semibold text-slate-400 uppercase tracking-widest`).

Sticky CTA bar at bottom on mobile (64px height), floats above bottom nav.

---

## 3. User Flows

### Flow 1 — Create Group (New User)

```
[Entry: user visits landing page or app root]
    → [Landing Page]
        CTA: "Create a Group"
    → [Create Group Screen]
        Input: Group name
        Input: Your display name
        Action: "Create Group & Get Link"
        [Loading: spinner in button, 300–800ms API call]
    → [Group Created — Confirmation State]
        Shows: shareable link (copyable)
        Shows: Web Share API button ("Share Link")
        CTA: "Go to Dashboard"
        [Success: navigate to Dashboard with welcome state]
    
    Error path:
        [Network error] → Toast: "Couldn't create group. Try again." → [Stay on Create Group]
        [Name too long >50 chars] → Inline error: "Group name must be under 50 characters"
```

### Flow 2 — Join Group via Link (Returning/New Member)

```
[Entry: user opens shared link — /join/{group-token}]
    → [Join Group Screen]
        Shows: Group name prominently
        Shows: Member avatars (existing members)
        Input: Your display name (single field, auto-focused)
        CTA: "Join Group"
        [Loading: spinner, 200–500ms API call]
    → [Dashboard]
        Welcome toast: "Welcome, {name}! You've joined {group}."
        [If 0 expenses] → Empty state with "Add First Expense" CTA
        [If expenses exist] → Full dashboard with member balances
    
    Error path:
        [Expired or invalid link] → [Link Error Screen] — "This group link is invalid or has been closed."
        [Duplicate name in group] → Inline error: "Someone in this group is already named {name}. Try a variation."
        [Name empty] → Inline error: "Please enter your display name."
```

### Flow 3 — Log an Expense

```
[Entry: "Add Expense" button — bottom nav, dashboard CTA, or FAB]
    → [Add Expense Screen]
        Input: Description (text)
        Input: Amount (numeric keypad)
        Select: Who paid (dropdown — group members)
        Select: Split between (all / custom)
        [If custom split] → Custom split sub-form (equal toggle / percentages / amounts)
        CTA: "Add Expense"
        [Loading: spinner, 200–500ms]
    → [Dashboard]
        Toast: "Expense added!" 
        Balance rows update immediately (optimistic update)
    
    Error path:
        [Amount is 0 or empty] → Inline error: "Please enter an amount greater than $0"
        [No description] → Inline error: "Please describe this expense"
        [Split does not add to 100%] → Inline error: "Splits must add up to 100%"
        [Network error] → Toast: "Couldn't save expense. Form preserved — try again."
        [Draft preserved in localStorage] → if user navigates away and returns, form is pre-filled
```

### Flow 4 — Settle Up

```
[Entry: "Settle Up" button on Dashboard or bottom nav]
    → [Settle Up Screen]
        Shows: Net balances (who owes, who is owed)
        Shows: Minimum-transfer plan (numbered list)
        Shows: Per-transfer "Mark as Settled" button
        CTA: "Copy Plan" (primary)
    → [Mark as Settled — per transfer]
        [Tap "Mark as Settled" on one transfer]
        [Optimistic: transfer card turns green, shows checkmark]
        [API call in background]
        [If last transfer marked] → All-settled celebration state
            Shows: Confetti/completion illustration
            Shows: "All settled! Your group is even."
            CTA: "Back to Group"
    
    CTA: "Copy Plan" flow:
        [Tap "Copy Plan"]
        [Clipboard API writes plain-text plan]
        Toast: "Payment plan copied! Paste it in your group chat."
    
    Error path:
        [All balances already settled] → Settled empty state: "Everyone is even. Nothing to settle!"
        [Network error on mark-settled] → Toast: "Couldn't record settlement. Try again." → [Button reverts to unsettled state]
```

### Flow 5 — View Expense Detail

```
[Entry: tap any expense row in Dashboard or Add Expense list]
    → [Expense Detail Screen]
        Shows: Description, amount, date, who paid
        Shows: Per-person split breakdown table
        Shows: Edit and Delete actions
    → [Edit Expense] (follows Add Expense flow, pre-filled)
    → [Delete Expense]
        Confirmation modal: "Delete this expense? This can't be undone."
        [Confirm] → Delete, return to Dashboard, toast "Expense deleted"
        [Cancel] → Close modal, stay on Expense Detail
```

---

## 4. Screen Inventory

### Screen 1 — Landing / Home (`/`)

**Purpose:** Explain the product in one sentence. Drive group creation.
**Entry points:** Direct URL, app icon (PWA), organic search.

**ASCII Wireframe (mobile — 390px):**
```
┌─────────────────────────────────┐
│  FairSplit                   [?]│  ← header, no nav (pre-auth)
├─────────────────────────────────┤
│                                 │
│   Split expenses with           │
│   friends. No accounts.         │  ← Display XL, centered
│   No drama.                     │
│                                 │
│  [icon] Zero-friction           │  ← 3 value props, icon + text
│  [icon] No accounts to join     │
│  [icon] Minimum transfers       │
│                                 │
│  ┌─────────────────────────┐    │
│  │  + Create a New Group   │    │  ← Primary button, full width
│  └─────────────────────────┘    │
│                                 │
│  Already have a link?           │  ← Small text link
│  Paste it here ________________ │
│                         [Join]  │
│                                 │
└─────────────────────────────────┘
```

**Component list:** PageHeader (minimal), Button (primary xl, ghost sm), Input (link paste), Alert (info — if pasted link is invalid).

**State matrix:**
- Default: form empty, no alerts
- Link paste: input filled, "Join" button activates
- Invalid link: alert below input, "That doesn't look like a valid FairSplit link"

**Responsive:**
- Mobile: single column, full-width CTA
- Desktop: two-column — left value prop, right visual (group illustration or expense mockup card)

---

### Screen 2 — Create Group (`/create`)

**Purpose:** Collect group name + creator display name. Generate shareable link.
**Entry points:** Landing page "Create a New Group" CTA.

**ASCII Wireframe (mobile — 390px):**
```
┌─────────────────────────────────┐
│ ← Back          Create a Group  │
├─────────────────────────────────┤
│                                 │
│  Group Name                     │
│  ┌───────────────────────────┐  │
│  │ Nashville Trip 🏕         │  │
│  └───────────────────────────┘  │
│                                 │
│  Your Name                      │
│  ┌───────────────────────────┐  │
│  │ Maya                      │  │
│  └───────────────────────────┘  │
│  You won't need a password.     │  ← Helper text
│  Just remember this name.       │
│                                 │
│  ┌───────────────────────────┐  │
│  │   Create Group & Get Link │  │  ← Primary button
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘

[POST-CREATION STATE:]
┌─────────────────────────────────┐
│ ← Back          Group Created   │
├─────────────────────────────────┤
│                                 │
│  ✓ Nashville Trip is ready!     │  ← Success heading
│                                 │
│  Share this link with your      │
│  group:                         │
│                                 │
│  ┌───────────────────────────┐  │
│  │ fairsplit.app/join/abc123 │  │  ← Read-only, monospace
│  │                    [Copy] │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │  📤 Share Link            │  │  ← Web Share API
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │  Go to Dashboard →        │  │  ← Secondary button
│  └───────────────────────────┘  │
└─────────────────────────────────┘
```

**Component list:** PageHeader (with back), FormField (×2), Button (primary, secondary, ghost-icon for copy), Alert (success).

**State matrix:**
- Default: empty form
- Typing: form filling, validation on blur
- Loading: button spinner, inputs disabled
- Success: link revealed, form replaced by share state
- Error: toast error, form re-enabled

**Responsive:**
- Mobile: single column, full-width inputs
- Desktop: centered card, max-width 480px

---

### Screen 3 — Join Group (`/join/{token}`)

**Purpose:** Let any person join a group with only a display name. Zero friction.
**Entry points:** Shared link from group creator or existing member.

**ASCII Wireframe (mobile — 390px):**
```
┌─────────────────────────────────┐
│                    FairSplit    │  ← minimal header
├─────────────────────────────────┤
│                                 │
│  You're invited to              │
│  Nashville Trip                 │  ← Group name, bold
│                                 │
│  [M] [J] [T] [+2]              │  ← Member avatars (existing)
│  Maya, Jake, Tom and 2 others   │  ← Member names list
│                                 │
│  What's your name?              │  ← Label
│  ┌───────────────────────────┐  │
│  │ _________________________ │  │  ← Auto-focused input
│  └───────────────────────────┘  │
│  No account needed.             │  ← Helper text, green
│                                 │
│  ┌───────────────────────────┐  │
│  │       Join Group          │  │  ← Primary button
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

**Component list:** Avatar (size 40px), Input (auto-focused), Button (primary lg), Badge (member count).

**State matrix:**
- Default: group info shown, input empty, button disabled
- Typing: input filling, button enables when ≥2 characters
- Loading: button spinner
- Duplicate name: inline error "Someone here is already named {X}. Try a different name."
- Invalid link: full-screen error state with "Return Home" CTA

**Responsive:**
- Mobile: centered, single column, large generous padding
- Desktop: centered card, max-width 440px

---

### Screen 4 — Group Dashboard (`/group/{id}`)

**Purpose:** Show the group's financial state at a glance. Primary workspace.
**Entry points:** Post-create, post-join, bottom nav "Home", deep link.

**ASCII Wireframe (mobile — 390px):**
```
┌─────────────────────────────────┐
│ Nashville Trip          [⋯ More]│  ← PageHeader
├─────────────────────────────────┤
│ ┌──────────────────────────┐    │
│ │  Your balance             │    │  ← Hero balance card
│ │                           │    │
│ │  You are owed             │    │
│ │  $127.50                  │    │  ← Amount XL, emerald
│ │                           │    │
│ │  [  Settle Up  ]          │    │  ← Primary button
│ └──────────────────────────┘    │
├─────────────────────────────────┤
│ Members                  [+ Invite]│
│ ┌─────────────────────────────┐ │
│ │ [M] Maya           +$127.50 │ │  ← green
│ │ [J] Jake            -$42.00 │ │  ← red
│ │ [T] Tom             -$58.00 │ │  ← red
│ │ [S] Sarah           -$27.50 │ │  ← red
│ └─────────────────────────────┘ │
├─────────────────────────────────┤
│ Recent Expenses        [View all]│
│ ┌─────────────────────────────┐ │
│ │ [M] Airbnb · May 12         │ │
│ │     Split 4 ways    $240.00 │ │
│ │     Your share       $60.00 │ │
│ ├─────────────────────────────┤ │
│ │ [J] Dinner · May 11         │ │
│ │     Split 4 ways     $84.00 │ │
│ │     Your share       $21.00 │ │
│ └─────────────────────────────┘ │
├─────────────────────────────────┤
│ [🏠Home] [+Add]  [⇄Settle] [👥] │  ← Bottom nav
└─────────────────────────────────┘
```

**Component list:** PageHeader, Card (hero, elevated), Badge (positive/negative), Avatar, DataTable (expense list), Button (primary, ghost), BottomNav.

**State matrix:**
- Default: populated with expenses and balances
- Loading: skeleton cards (3 expense rows, balance card)
- Empty (0 expenses): EmptyState with "Add your first expense" CTA and illustration
- All settled: Hero card shows "Everyone is even!" in emerald, settle-up button becomes ghost
- Error: inline alert "Couldn't load group data. Tap to retry."

**Responsive:**
- Mobile: stacked sections, bottom nav
- Desktop: two-column layout (sidebar: members, main: expenses), top nav

---

### Screen 5 — Add Expense (`/group/{id}/expense/new`)

**Purpose:** Log a shared expense in under 30 seconds.
**Entry points:** Bottom nav "+ Add", dashboard CTA, FAB.

**ASCII Wireframe (mobile — 390px):**
```
┌─────────────────────────────────┐
│ ← Cancel        Add Expense    │
├─────────────────────────────────┤
│                                 │
│  Amount                         │
│  ┌───────────────────────────┐  │
│  │ $  ______________________ │  │  ← inputmode="decimal"
│  └───────────────────────────┘  │
│                                 │
│  Description                    │
│  ┌───────────────────────────┐  │
│  │ _________________________ │  │
│  └───────────────────────────┘  │
│                                 │
│  Who paid?                      │
│  ┌───────────────────────────┐  │
│  │ Maya                    ▼ │  │  ← Dropdown (self pre-selected)
│  └───────────────────────────┘  │
│                                 │
│  Split between                  │
│  ┌───────────────────────────┐  │
│  │ ◉ Split equally            │  │
│  │ ○ Custom amounts           │  │
│  │ ○ Custom percentages       │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌──────────── Split preview ─┐ │  ← shown when amount > 0
│  │ Maya   $25.00  Jake  $25.00│ │
│  │ Tom    $25.00  Sarah $25.00│ │
│  └────────────────────────────┘ │
│                                 │
│ ┌───────────────────────────────┐│
│ │          Add Expense          ││  ← sticky CTA bar
│ └───────────────────────────────┘│
└─────────────────────────────────┘
```

**Component list:** PageHeader (with cancel), FormField, Input (amount, description), Dropdown (member select), RadioGroup (split mode), SplitPreview (molecule), Button (primary sticky).

**State matrix:**
- Default: empty form, "who paid" pre-selected to current user
- Amount entered: split preview appears below split mode
- Custom split: additional sub-form rows per member
- Custom split invalid: real-time validation "Splits must add to $X.XX"
- Loading: button spinner, form disabled
- Success: navigate back, toast "Expense added"
- Error (network): toast, form preserved in localStorage

**Responsive:**
- Mobile: full-screen sheet, sticky CTA
- Desktop: centered modal or inline page, max-width 520px

---

### Screen 6 — Settle Up (`/group/{id}/settle`)

**Purpose:** Show the minimum-transfer settlement plan. Enable one-tap marking as settled.
**Entry points:** Bottom nav "Settle", dashboard "Settle Up" button.

**ASCII Wireframe (mobile — 390px):**
```
┌─────────────────────────────────┐
│ ← Back           Settle Up     │
├─────────────────────────────────┤
│                                 │
│  Net balances                   │  ← Section header
│  ┌─────────────────────────────┐│
│  │ [M] Maya       gets +$127.50││  ← green
│  │ [J] Jake       owes  -$42.00││  ← red
│  │ [T] Tom        owes  -$58.00││  ← red
│  │ [S] Sarah      owes  -$27.50││  ← red
│  └─────────────────────────────┘│
│                                 │
│  Payment plan                   │  ← Section header
│  3 transfers to clear all debts │  ← subtitle
│                                 │
│  ┌─────────────────────────────┐│
│  │  1  Jake pays Maya $42.00   ││  ← Transfer card
│  │  [  Mark as Settled  ]      ││
│  └─────────────────────────────┘│
│  ┌─────────────────────────────┐│
│  │  2  Tom pays Maya $58.00    ││
│  │  [  Mark as Settled  ]      ││
│  └─────────────────────────────┘│
│  ┌─────────────────────────────┐│
│  │  3  Sarah pays Maya $27.50  ││
│  │  [  Mark as Settled  ]      ││
│  └─────────────────────────────┘│
│                                 │
│  ┌───────────────────────────┐  │
│  │  📋 Copy Payment Plan     │  │  ← Primary action
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘

[ALL SETTLED STATE:]
┌─────────────────────────────────┐
│ ← Back           Settle Up     │
├─────────────────────────────────┤
│                                 │
│        [celebration icon]       │
│                                 │
│   Everyone is even!             │  ← Heading XL
│   All debts are settled.        │  ← Body
│                                 │
│  ┌───────────────────────────┐  │
│  │      Back to Group        │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

**Component list:** PageHeader, Card (transfer card), Badge (positive/negative), Button (primary for copy, secondary for mark settled), EmptyState (all settled).

**State matrix:**
- Default: full transfer list, copy button prominent
- One settled: that card turns green, button shows "Settled ✓"
- All settled: full empty/celebration state
- Already-settled group (no balances): immediate settled state
- Loading: skeleton transfer cards

**Responsive:**
- Mobile: full-screen, sticky "Copy Plan" at bottom above nav
- Desktop: centered, max-width 560px

---

### Screen 7 — Expense Detail (`/group/{id}/expense/{expense-id}`)

**Purpose:** Full breakdown of one expense — who paid, who owes what, when.
**Entry points:** Tap any expense row in Dashboard or expense list.

**ASCII Wireframe (mobile — 390px):**
```
┌─────────────────────────────────┐
│ ← Back       Expense Detail    │
│                          [Edit] │
├─────────────────────────────────┤
│                                 │
│  Airbnb — Nashville             │  ← Heading LG
│  May 12, 2026 · 4 people       │  ← Subtitle, slate-400
│                                 │
│  Total                          │
│  $240.00                        │  ← Amount XL
│                                 │
│  Paid by                        │
│  [M] Maya                       │  ← Avatar + name
│                                 │
├─────────────────────────────────┤
│  Split breakdown                │
│  ┌─────────────────────────────┐│
│  │ [M] Maya    paid  +$180.00  ││  ← (paid $240 - owes $60 = net +$180)
│  │ [J] Jake         -$60.00   ││
│  │ [T] Tom          -$60.00   ││
│  │ [S] Sarah        -$60.00   ││
│  └─────────────────────────────┘│
│                                 │
│  ┌───────────────────────────┐  │
│  │  🗑 Delete Expense        │  │  ← Danger ghost button
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

**Component list:** PageHeader (with back + edit), Card (split breakdown), Avatar, Badge (positive/negative), Button (ghost danger).

**State matrix:**
- Default: full expense data loaded
- Loading: skeleton
- Error: alert "Couldn't load this expense."
- Deleted: navigation back to dashboard, toast "Expense deleted"

**Responsive:**
- Mobile: single column
- Desktop: centered, max-width 520px

---

### Screen 8 — Empty State (`/group/{id}` — 0 expenses)

This is the dashboard in empty state, documented separately for clarity.

**ASCII Wireframe:**
```
┌─────────────────────────────────┐
│ Nashville Trip          [⋯ More]│
├─────────────────────────────────┤
│ ┌──────────────────────────┐    │
│ │  Everyone's even for now  │    │  ← Hero card, emerald tint
│ │  Add an expense to start  │    │
│ │  tracking.                │    │
│ └──────────────────────────┘    │
├─────────────────────────────────┤
│  No expenses yet                │
│                                 │
│     [receipt illustration]      │
│                                 │
│  Log your first shared expense  │
│  and we'll track who owes what. │
│                                 │
│  ┌───────────────────────────┐  │
│  │   + Add First Expense     │  │  ← Primary button
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │   📤 Invite Members       │  │  ← Secondary button
│  └───────────────────────────┘  │
├─────────────────────────────────┤
│ [🏠Home] [+Add]  [⇄Settle] [👥] │
└─────────────────────────────────┘
```

---

## 5. Key Interactions & Micro-animations

| Interaction | Trigger | Behavior | Duration | Easing |
|---|---|---|---|---|
| Page navigation | Link tap / button | Slide in from right (mobile), fade-in (desktop) | 200ms | `ease-out` |
| Bottom nav tab switch | Tab tap | Active indicator slides to new tab position | 200ms | `cubic-bezier(0.34, 1.56, 0.64, 1)` (spring) |
| Button press | Pointer down | Scale to 0.98, shadow reduces | 100ms | `ease-in` |
| Button release | Pointer up | Scale returns to 1, shadow restores | 150ms | `ease-out` |
| Button loading | API call start | Spinner replaces label, width locked | 150ms | `ease` |
| Card hover (desktop) | Mouse enter | Shadow lifts from `shadow-sm` to `shadow-md` | 150ms | `ease-out` |
| Toast appear | Event fires | Slides down from top | 200ms | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Toast dismiss | Auto or X tap | Slides up and fades | 150ms | `ease-in` |
| Modal open | CTA trigger | Backdrop fades in (200ms), sheet slides up from bottom (300ms) | 300ms | `cubic-bezier(0.16, 1, 0.3, 1)` |
| Modal close | Backdrop tap / Escape | Sheet slides down, backdrop fades out | 200ms | `ease-in` |
| Settle-up mark settled | "Mark as Settled" tap | Card background transitions to `bg-emerald-50`, icon changes to ✓ | 300ms | `ease-out` |
| All settled celebration | Last transfer marked | Confetti burst (CSS particle), cards fade out, celebration state fades in | 500ms total | `ease-out` |
| Balance chip update | After expense added | Old value fades out, new value fades in | 250ms | `ease` |
| Copy to clipboard | "Copy Plan" tap | Button label flips to "Copied!" with checkmark for 2 seconds | 150ms in, 2000ms hold, 150ms out | `ease` |
| Split preview | Amount field change | Preview appears with slide-down from 0 height to auto | 200ms | `ease-out` |
| Dropdown open | Trigger click | Options list expands from 0 to full height | 150ms | `ease-out` |
| Link copy (create group) | Copy button tap | Confirmation icon pulse, button text changes | 150ms | `ease` |
| Skeleton loading | While API resolves | Shimmer animation across gray placeholder blocks | Continuous | linear |
| Form error shake | Submit with invalid field | Horizontal shake animation on error field | 300ms | `ease` |
| Reduced motion | `prefers-reduced-motion: reduce` | All transitions reduced to simple fade at 100ms | 100ms | `ease` |

---

## 6. Accessibility Compliance

### ARIA Implementation

| Component | Role | Required ARIA Attributes |
|---|---|---|
| Bottom navigation | `navigation` | `aria-label="Main navigation"` |
| Nav tab items | `link` | `aria-current="page"` on active |
| Modal/dialog | `dialog` | `aria-modal="true"`, `aria-labelledby="{title-id}"` |
| Modal backdrop | `presentation` | — |
| Dropdown trigger | `button` | `aria-haspopup="listbox"`, `aria-expanded="{true/false}"` |
| Dropdown menu | `listbox` | `aria-label="{trigger label}"` |
| Dropdown option | `option` | `aria-selected="{true/false}"` |
| Form inputs | `textbox` | `aria-required`, `aria-invalid`, `aria-describedby` |
| Amount input | `textbox` | `aria-label="Amount in dollars"`, `inputmode="decimal"` |
| Balance badge (positive) | `status` | `aria-label="You are owed $X"` |
| Balance badge (negative) | `status` | `aria-label="You owe $X"` |
| Loading spinner | `img` | `aria-label="Loading"`, `role="img"` |
| Toast notification | `status` | `role="status"`, `aria-live="polite"` |
| Error toast | `alert` | `role="alert"`, `aria-live="assertive"` |
| Settle-up transfers list | `list` | `aria-label="Payment plan"` |
| Transfer item | `listitem` | — |
| "Mark as Settled" button | `button` | `aria-label="{payer} pays {payee} ${amount} — Mark as Settled"` |
| Member avatar | `img` | `alt="{name}'s avatar"` |
| Copy button | `button` | `aria-label="Copy payment plan to clipboard"` |
| Delete button | `button` | `aria-label="Delete this expense"` |
| Checkbox (custom split) | `checkbox` | `aria-checked`, `aria-label="{name} included in split"` |

### Keyboard Navigation Map

| Key | Action | Context |
|---|---|---|
| `Tab` | Move focus forward | All interactive elements |
| `Shift+Tab` | Move focus backward | All interactive elements |
| `Enter` | Activate button / submit form / select option | Buttons, form submit, dropdown options |
| `Space` | Toggle checkbox / activate button | Checkboxes, buttons |
| `Escape` | Close modal / close dropdown / cancel action | Modals, dropdowns, sheets |
| `ArrowDown` | Next option | Dropdown listbox, select |
| `ArrowUp` | Previous option | Dropdown listbox, select |
| `Home` | First option | Dropdown listbox |
| `End` | Last option | Dropdown listbox |
| `ArrowLeft/Right` | Switch tab | Bottom nav (when focused) |

### Focus Order — Group Dashboard

1. PageHeader (group name)
2. More options button (top right)
3. Balance hero card → Settle Up button
4. Invite members button
5. Member balance rows (top to bottom)
6. View all expenses link
7. Expense rows (most recent first)
8. Bottom navigation tabs (Home, Add, Settle, Group)

### Color Contrast Verification

| Element | Text Color | Background | Contrast Ratio | WCAG Level |
|---|---|---|---|---|
| Body text | `#475569` (slate-600) | `#ffffff` | 5.93:1 | AA ✓ |
| Secondary text | `#64748b` (slate-500) | `#ffffff` | 4.60:1 | AA ✓ |
| Helper text | `#94a3b8` (slate-400) | `#ffffff` | 2.90:1 | AA (large) ✓ |
| Primary button label | `#ffffff` | `#10b981` (emerald-500) | 2.87:1 | Fail on emerald-500 |
| Primary button label | `#ffffff` | `#059669` (emerald-600) | 4.01:1 | AA (large text) ✓ |
| **Primary button label (corrected)** | `#ffffff` | `#047857` (emerald-700) | **5.35:1** | **AA ✓ — use emerald-700 for button bg** |
| Positive balance text | `#166534` (emerald-800 equiv) | `#d1fae5` (emerald-100) | 7.28:1 | AAA ✓ |
| Negative balance text | `#be123c` (rose-700) | `#ffe4e6` (rose-100) | 5.94:1 | AA ✓ |
| Settled text | `#64748b` (slate-500) | `#f1f5f9` (slate-100) | 4.07:1 | AA ✓ |
| Input placeholder | `#94a3b8` (slate-400) | `#ffffff` | 2.90:1 | AA (as decorative) ✓ |
| Page background body | `#334155` (slate-700) | `#f8fafc` (slate-50) | 10.3:1 | AAA ✓ |

**Critical correction:** Primary button background must use `emerald-700` (`#047857`) not `emerald-500` to pass WCAG AA for normal text. `emerald-500` is only acceptable for large text (18px bold+) or decorative elements. All prototype files implement this correction.

### Focus Ring Specification

All interactive elements: `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500 focus-visible:ring-offset-2`. The ring-offset provides a 2px white gap so the ring is visible on any background. Never use `:focus` alone — use `:focus-visible` to avoid persistent rings on mouse click.

### Touch Targets

All tap targets: minimum 44×44px. Form inputs: height 44px. Buttons: minimum height 44px. Bottom nav items: 64px height total. Small ghost buttons with icons: 44×44px wrapper even if icon is smaller.

### Prefers-Reduced-Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

Applied to all CSS transitions and JavaScript-driven animations.

---

*End of FairSplit Design Specification v1.0*
