# Design Specification: {Project Name}

**Version:** 1.0
**Date:** {YYYY-MM-DD}
**Author:** UX Designer Agent
**Status:** Draft / Review / Approved
**Referenced PRD:** workspace/{project}/prd.md

---

## 1. Design Principles

{3-5 opinionated principles that guide every design decision. Not generic ("keep it simple") but specific to this product and its users.}

1. **{Principle Name}** — {1-2 sentence explanation with a concrete implication}
2. **{Principle Name}** — {1-2 sentence explanation}
3. **{Principle Name}** — {1-2 sentence explanation}

---

## 2. Design System

### Color Palette

| Token Name | Hex | Usage |
|---|---|---|
| `color-primary-500` | `#XXXXXX` | Primary actions, links, active states |
| `color-primary-600` | `#XXXXXX` | Primary hover states |
| `color-neutral-50` | `#XXXXXX` | Page background |
| `color-neutral-900` | `#XXXXXX` | Primary text |
| `color-success-500` | `#XXXXXX` | Success states |
| `color-error-500` | `#XXXXXX` | Error states |
| `color-warning-500` | `#XXXXXX` | Warning states |

### Typography

| Token Name | Font | Size | Weight | Line Height | Usage |
|---|---|---|---|---|---|
| `text-display-lg` | {font} | 48px | 700 | 1.1 | Hero headings |
| `text-heading-xl` | {font} | 32px | 700 | 1.2 | Page titles |
| `text-heading-lg` | {font} | 24px | 600 | 1.3 | Section headings |
| `text-heading-md` | {font} | 20px | 600 | 1.4 | Card headings |
| `text-body-lg` | {font} | 16px | 400 | 1.6 | Body copy |
| `text-body-sm` | {font} | 14px | 400 | 1.6 | Secondary text, captions |
| `text-label` | {font} | 12px | 500 | 1.4 | Labels, badges |

### Spacing Scale (8pt grid)

| Token | Value | Usage |
|---|---|---|
| `space-1` | 4px | Micro spacing (icon gaps) |
| `space-2` | 8px | Tight spacing (within components) |
| `space-3` | 12px | Component internal padding |
| `space-4` | 16px | Standard spacing |
| `space-6` | 24px | Component separation |
| `space-8` | 32px | Section spacing |
| `space-12` | 48px | Large section separation |
| `space-16` | 64px | Page-level spacing |

### Border Radius

| Token | Value | Usage |
|---|---|---|
| `radius-sm` | 4px | Inputs, small elements |
| `radius-md` | 8px | Cards, modals |
| `radius-lg` | 12px | Large containers |
| `radius-full` | 9999px | Pills, avatars |

### Shadows

| Token | Value | Usage |
|---|---|---|
| `shadow-sm` | `0 1px 3px rgba(0,0,0,0.1)` | Cards, dropdowns |
| `shadow-md` | `0 4px 12px rgba(0,0,0,0.12)` | Modals, popovers |
| `shadow-lg` | `0 8px 32px rgba(0,0,0,0.16)` | Full-page overlays |

### Component Library (Atomic Design)

#### Atoms
| Component | Variants | Notes |
|---|---|---|
| Button | primary, secondary, ghost, destructive; sm/md/lg | Loading state required |
| Input | default, error, disabled | Always has label + error message slot |
| Checkbox | default, indeterminate | Accessible: keyboard navigable |
| Badge | success, warning, error, neutral | |
| Avatar | xs/sm/md/lg, with/without image | Fallback to initials |
| Spinner | sm/md/lg | ARIA `role="status"` |

#### Molecules
| Component | Composition | Notes |
|---|---|---|
| Form Field | Label + Input + HelperText + ErrorMessage | |
| Card | Header + Body + Footer slots | |
| Dropdown Menu | Trigger + Menu + MenuItem | Keyboard: arrow keys, Escape |
| Toast | Icon + Message + Dismiss | Auto-dismiss after 5s |
| Modal | Overlay + Dialog + Header + Body + Footer | Focus trap required |
| Empty State | Illustration + Heading + Body + CTA | |

#### Organisms
| Component | Composition | Notes |
|---|---|---|
| Navigation | Logo + NavLinks + UserMenu | Responsive: collapses to hamburger on mobile |
| Data Table | Header + Rows + Pagination + Filters | Sortable columns, bulk actions |
| Sidebar | Logo + NavItems + CollapseToggle | |

---

## 3. User Flows

### Flow 1: {Flow Name} (e.g., Onboarding)

**Trigger:** {what initiates this flow}
**Success End State:** {what the user achieves}
**Error Paths:** {what can go wrong and how it's handled}

```
[Entry Point: {screen/trigger}]
        │
        ▼
[Screen: {name}]
  ├─ [Action: {action}] ──► [Screen: {name}]
  └─ [Action: {action}] ──► [Screen: {name}]
        │
        ▼
[Screen: {name}]
  ├─ [Error State: {condition}] ──► [Error handling: {approach}]
  └─ [Success] ──► [Screen: {name}]
        │
        ▼
[End State: {outcome}]
```

### Flow 2: {Flow Name}

{same structure}

---

## 4. Screen Inventory

### {Screen Name} — {Route: /path}

**Purpose:** {what this screen does and why}
**Persona(s):** {who uses it}
**Entry Points:** {how users arrive here}

**Layout:**
```
┌─────────────────────────────────────────────┐
│  NAVIGATION                                 │
│  Logo          Nav Links        User Menu   │
├─────────────────────────────────────────────┤
│                                             │
│  PAGE HEADER                                │
│  {Title}                    [Primary CTA]   │
│  {Subtitle/description}                     │
│                                             │
├─────────────────────────────────────────────┤
│                                             │
│  MAIN CONTENT                               │
│  ┌──────────────┐  ┌──────────────────────┐ │
│  │ {Component}  │  │ {Component}          │ │
│  │              │  │                      │ │
│  └──────────────┘  └──────────────────────┘ │
│                                             │
└─────────────────────────────────────────────┘
```

**Components Used:** {list of component library components}
**States:** Default | Loading | Empty | Error
**Responsive Behavior:** {how layout changes at mobile/tablet breakpoints}

---

## 5. Key Interactions & Micro-animations

| Interaction | Trigger | Behavior | Duration | Easing |
|---|---|---|---|---|
| Page transition | Route change | Fade in + slide up 8px | 200ms | ease-out |
| Button press | Click/tap | Scale 0.98 | 100ms | ease-in-out |
| Modal open | Trigger click | Backdrop fade + dialog scale from 0.95 | 200ms | ease-out |
| Toast appear | Event | Slide in from bottom-right | 300ms | spring |
| Form error | Validation fail | Input border turns `color-error-500` + shake 4px | 400ms | ease-in-out |
| {interaction} | {trigger} | {behavior} | {duration} | {easing} |

---

## 6. Accessibility (WCAG 2.2 AA)

### Compliance Requirements
- **Color Contrast:** All text meets 4.5:1 ratio (7:1 for small text under 18px)
- **Focus Indicators:** All interactive elements have visible `outline` (min 3px) in keyboard focus state
- **Keyboard Navigation:** All flows completable with keyboard only (Tab, Enter, Escape, arrow keys)
- **Screen Reader:** All interactive elements have `aria-label` or visible label; images have `alt` text
- **Touch Targets:** Minimum 44×44px for all interactive elements on mobile

### Specific Accessibility Decisions
| Element | ARIA Implementation | Notes |
|---|---|---|
| Modal | `role="dialog"`, `aria-modal="true"`, focus trap | |
| Navigation | `<nav aria-label="Main">` | |
| Form errors | `aria-describedby` linking input to error message | |
| Loading states | `aria-busy="true"`, `aria-live="polite"` | |
| Icons | `aria-hidden="true"` on decorative; `aria-label` on functional | |

---

## 7. Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|---|---|---|
| Mobile | < 640px | Single column, bottom nav, full-width components |
| Tablet | 640px–1024px | Two columns, sidebar collapses to top nav |
| Desktop | > 1024px | Full layout as designed |
| Wide | > 1440px | Max-width container centered |
