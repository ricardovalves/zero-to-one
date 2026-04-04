# Execution Report: {project}

**Pipeline:** {/startup | /ideate | /design | /architect | /build | /review-pr}
**Completed:** {YYYY-MM-DD HH:MM}
**Status:** COMPLETE | PARTIAL | FAILED

---

## Summary

{2-3 sentences: what was run, what it produced, what the key outcome is.}

---

## Business Case

| Metric | Value |
|---|---|
| Verdict | {GO / NO-GO / CONDITIONAL GO / N/A} |
| TAM | ${X}B |
| SOM Year 1 | ${X}M |
| Revenue Model | {model} |
| LTV:CAC | {X}x |
| Payback Period | {X} months |

---

## Product Scope

| Item | Value |
|---|---|
| North Star Metric | {metric name and definition} |
| Primary Persona | {name} — {role} |
| MVP Must-Have Features | {N} features |
| Top Feature (RICE) | {feature} — score {X} |
| Key Differentiator | {one sentence} |
| Deferred (Phase 2) | {top 3} |

---

## Design

| Item | Value |
|---|---|
| Primary Color | {hex} |
| Font | {name} |
| Prototype Screens | {list: index, login, dashboard, ...} |
| Open Prototype | `workspace/{project}/prototype/index.html` |
| Accessibility | WCAG 2.2 AA {compliant / issues noted} |

---

## Architecture

| Layer | Technology | Platform |
|---|---|---|
| Frontend | {framework} | {platform} |
| Backend | {framework} | {platform} |
| Database | {DB} | {platform} |
| Auth | {strategy} | — |
| CI/CD | {platform} | — |

**API Endpoints:** {N} defined in api-spec.yaml
**DB Tables:** {N} tables with full DDL
**ADRs:** {N} decisions documented

---

## Cost Analysis

| Stage | Monthly Cost |
|---|---|
| Prototype (free tier) | ~${X}/month |
| 1,000 users | ~${X}/month |
| 10,000 users | ~${X}/month |

---

## Delivery Plan

| Sprint | Goal | Points | Start | End |
|---|---|---|---|---|
| 0 | Foundation | {N} | {date} | {date} |
| 1 | Core features | {N} | {date} | {date} |
| 2 | {feature set} | {N} | {date} | {date} |
| ... | | | | |

---

## Artifacts Produced

| File | Agent | Status | Notes |
|---|---|---|---|
| `business-analysis.md` | business-expert | {✓ / ✗} | |
| `prd.md` | product-manager | {✓ / ✗} | |
| `design-spec.md` | ux-designer | {✓ / ✗} | |
| `prototype/index.html` | ux-designer | {✓ / ✗} | |
| `prototype/*.html` | ux-designer | {N} screens | |
| `technical-spec.md` | cto-architect | {✓ / ✗} | |
| `api-spec.yaml` | cto-architect | {✓ / ✗} | |
| `roadmap.md` | project-manager | {✓ / ✗} | |
| `handoffs/*.md` | all agents | {N} files | |

---

## Key Decisions

| # | Decision | Made By | Rationale |
|---|---|---|---|
| 1 | {e.g., FastAPI over Next.js API routes} | cto-architect | {reason} |
| 2 | {e.g., JWT auth instead of Clerk} | cto-architect | {reason} |
| 3 | {e.g., polling instead of WebSockets for MVP} | cto-architect | {reason} |
| ... | | | |

---

## Warnings / Issues

{List any NO-GO flags, low-confidence decisions, missing data, or items requiring human review.}

- {warning 1}
- {warning 2}

---

## Open Questions

| Question | Impact | Owner |
|---|---|---|
| {question} | High/Med/Low | {who} |

---

## Next Steps

1. {immediate action} — {command or action}
2. {next phase} — {command}
3. {validation step} — {what to check}
