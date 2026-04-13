# AI-Startup

**A full software organization, powered by AI agents.**

AI-Startup is a multi-agent framework built on [Claude Code](https://claude.ai/code) that mimics a complete software company. Given any idea, it orchestrates expert agents across strategy, design, engineering, and quality to deliver a working product — end-to-end.

---

## The Team

### Strategic Layer
- **Business Expert** — Market sizing (TAM/SAM/SOM), competitive analysis, Porter's 5 Forces, unit economics, go/no-go
- **Product Manager** — Personas, user stories, PRD, RICE prioritization, OKRs
- **UX Designer** — Design system, user flows, high-fidelity mockup specs, WCAG 2.2 AA accessibility, working HTML prototype
- **CTO / Architect** — C4 architecture, OpenAPI specs, DB schema, NFRs, technology selection

### Execution Layer
- **Project Manager** — Roadmap, epics, Linear issue creation, sprint planning
- **Backend Engineer** — FastAPI API routes, business logic, JWT auth, security headers, rate limiting, tests
- **Frontend Engineer** — Next.js 15 (App Router), Tailwind CSS, TypeScript strict, PostHog analytics
- **Infrastructure Engineer** — GitHub Actions CI/CD, Docker Compose, Fly.io deployment, Mailpit email preview
- **Database Engineer** — PostgreSQL 16, SQLAlchemy 2.0 async, Alembic migrations, query optimization
- **Stripe Engineer** — Checkout, subscriptions, webhooks, plan gating middleware, billing portal, pricing UI
- **Email Engineer** — Transactional email (verification, reset, welcome, billing), Mailpit local dev, Resend production
- **AI Engineer** — LLM integration, RAG pipelines, embeddings, prompt engineering

### Quality Gates (every PR)
- **Security Engineer** — OWASP Top 10, STRIDE threat modeling, dependency scanning
- **Architecture Reviewer** — C4 compliance, NFR checks, best practices
- **PR Reviewer** — SOLID principles, test coverage, code quality
- **QA Engineer** — Regression tests for bugs found, integration test coverage, smoke tests

---

## Pipeline Flow

Every idea moves through the same stages. Agents communicate exclusively through files — no direct calls between agents.

```
[Your Idea]
     │
     ▼
┌─────────────────┐
│ business-expert │  WebSearch + analysis
└────────┬────────┘
         │ business-analysis.md
         ▼
  ╔═════════════╗
  ║  GATE 1     ║  Viability report — GO / CONDITIONAL GO / NO-GO
  ║  (you)      ║  NO-GO stops here. GO waits for your approval.
  ╚══════╤══════╝
         │
         ▼
┌─────────────────┐
│ product-manager │  Personas, user stories, RICE scoring
└────────┬────────┘
         │ prd.md
         │
   ┌─────┴──────┐   (parallel)
   ▼            ▼
┌──────────┐  ┌───────────────┐
│ux-       │  │ cto-architect │
│designer  │  │               │
└────┬─────┘  └───────┬───────┘
     │                │
design-spec.md    technical-spec.md
prototype/*.html  api-spec.yaml
     │                │
     └────────┬────────┘
              │
              ▼
     ┌─────────────────┐
     │ project-manager │  Roadmap, epics, Linear issues
     └────────┬────────┘
              │ roadmap.md
              ▼
  ╔═════════════════════╗
  ║  GATE 2  (you)      ║  Full execution plan — sprints, tasks, agents
  ╚══════════╤══════════╝
             │
   ┌─────────┼──────────┬────────────┬──────────┬──────────┐
   ▼         ▼          ▼            ▼          ▼          ▼
backend  frontend    infra         db-      stripe-    email-
engineer  engineer   engineer    engineer   engineer   engineer
   │         │          │            │          │          │
   └─────────┴──────────┴────────────┴──────────┴──────────┘
                         │
                    workspace/{project}/src/
                         │
              ┌──────────┼───────────┐   (parallel, every PR)
              ▼          ▼           ▼
          security   architect    pr-
          engineer   reviewer    reviewer
```

### How information flows between agents

Every agent reads only from `workspace/{project}/` — it never calls another agent directly. Handoff notes act as compressed summaries so downstream agents don't re-read full documents.

```
Agent produces:
  workspace/{project}/{output}.md        ← primary artifact
  workspace/{project}/handoffs/{name}.md ← 10-bullet summary for downstream agents

Next agent reads:
  workspace/{project}/handoffs/*.md      ← first (compressed, fast)
  workspace/{project}/{spec}.md          ← only if more detail needed
```

The two auto-generated `CLAUDE.md` files propagate decisions without repeating them:

| File | Generated after | Contains |
|---|---|---|
| `workspace/{project}/CLAUDE.md` | Strategic phase | Product brief, personas, key entities, stack decisions |
| `workspace/{project}/src/CLAUDE.md` | Build phase | Run commands, seed accounts, file layout, critical patterns |

---

## How to Use

### Full Pipeline (idea → production)
```
/startup "your idea here"   # idea → business analysis → PRD → design + arch → roadmap
/build <project>            # foundation → features → billing → email
/deploy <project>           # GitHub → Fly.io → domain → live URL
```

### Individual Phases
```
/ideate "your idea"          # Business analysis + PRD only
/design <project>            # UX design spec + HTML prototype
/architect <project>         # Technical architecture + API spec
/build <project> [feature]   # Engineering pipeline
/deploy <project>            # Production deployment (Fly.io)
/sprint <project>            # Plan next Linear sprint
```

### Quality Reviews
```
/review-pr <PR-url>          # Full 3-agent PR review (security + architecture + code)
/security-scan <project>     # Full security audit of workspace/src
```

### Individual Agents
Invoke any agent directly in Claude Code with `@agent-name`:
```
@business-expert analyze the ride-sharing market in Southeast Asia
@ux-designer design the onboarding flow for workspace/myapp/prd.md
@stripe-engineer add billing to workspace/myapp with a free + pro tier
@security-engineer audit workspace/myapp/src for auth vulnerabilities
```

---

## Project Outputs

All artifacts are saved to `workspace/{project-name}/`:

| File | Produced By |
|---|---|
| `CLAUDE.md` | orchestrator (synthesized from all docs) |
| `business-analysis.md` | business-expert |
| `prd.md` | product-manager |
| `design-spec.md` | ux-designer |
| `prototype/*.html` | ux-designer |
| `technical-spec.md` | cto-architect |
| `api-spec.yaml` | cto-architect |
| `roadmap.md` | project-manager |
| `src/` | engineering team |
| `src/CLAUDE.md` | orchestrator (developer context) |
| `deployment.md` | deploy command |
| `execution-report.md` | orchestrator |

---

## Technology Stack

| Concern | Local / Prototype | Production |
|---|---|---|
| Frontend | Next.js 15 (App Router) in Docker | Fly.io or Vercel |
| Backend | FastAPI in Docker | Fly.io |
| Database | PostgreSQL 16 in Docker | Fly Postgres / Supabase free |
| Auth | Custom JWT (bcrypt + httpOnly cookie) | Same |
| Email (local) | Mailpit in Docker (SMTP catcher) | Resend or Postmark |
| Email (prod) | — | Resend (3K/mo free) |
| Billing | Stripe test mode | Stripe production |
| Analytics | PostHog (cloud free or self-hosted) | Same |
| Storage | MinIO in Docker | MinIO self-hosted or AWS S3 |
| CI/CD | GitHub Actions | GitHub Actions |
| Monitoring | Sentry free tier | Sentry / Grafana |
| Project mgmt | Linear | Linear |

**First-iteration rule:** Everything runs with `docker compose up` — zero external accounts, zero credit cards, zero cloud setup required. Mailpit catches all email locally. Stripe test mode charges nothing. Deploy to a real URL with `/deploy` when you're ready for customers.

---

## Pipeline Gates

Two mandatory approval gates prevent building the wrong thing:

1. **Viability Gate** (after business analysis) — Presents TAM, LTV:CAC, top risks. If NO-GO, stops entirely. If GO/CONDITIONAL GO, waits for explicit user approval before continuing.

2. **Plan & Milestones Gate** (before any code is written) — Presents the full execution plan with epics, tasks, sprint breakdown, and Linear issue count. Waits for explicit user approval before launching engineering agents.

---

## Setup

1. Clone this repo and open in Claude Code
2. Optionally set environment variables for integrations:
   ```bash
   export LINEAR_API_KEY=your_linear_key      # for Linear issue creation
   export GITHUB_TOKEN=your_github_token      # for GitHub repo creation in /deploy
   export ANTHROPIC_API_KEY=your_key          # if not already set by Claude Code
   ```
3. Run `/startup "your idea"` to begin

No other setup required. The full stack runs locally via Docker.

---

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- Docker + Docker Compose (for local development)
- Python 3.11+ (for integration tools)
- GitHub account (for `/deploy`)
- Linear account (optional, for sprint management)

---

## Roadmap

### Implemented

| Item | Status |
|---|---|
| Business analysis → PRD → Design → Architecture pipeline | ✓ |
| Parallel agent execution (UX + CTO, backend + frontend + infra) | ✓ |
| Viability Gate + Plan & Milestones Gate | ✓ |
| Project CLAUDE.md + src/CLAUDE.md auto-generation | ✓ |
| Stripe billing agent (checkout, webhooks, plan gating) | ✓ |
| Transactional email agent (Mailpit local, Resend prod) | ✓ |
| `/deploy` command (Fly.io, secrets, smoke tests) | ✓ |
| PostHog analytics in frontend skeleton | ✓ |
| HTTP security headers + global rate limiting | ✓ |

### Planned

| Priority | Item | Notes |
|---|---|---|
| High | Social login / OAuth (Google) | Major B2B conversion driver; auth table restructure needed |
| High | Landing page agent `/launch` | Static marketing site with pricing; pre-launch validation |
| Medium | Customer feedback (Chatwoot) | Open-source Intercom; in-app widget + Docker service |
| Medium | Feature flags (Unleash) | Open-source; controlled rollout and experiments |
| Medium | Feedback-to-sprint loop | `/sprint` reads `workspace/{project}/feedback.md` from users |
| Low | Mobile app path | React Native or Expo agent for consumer products |
| Low | Multi-region deployment | Fly.io multi-region; only when customer data requires it |
| Low | SSO / SAML | For enterprise sales; Boxyhq (open-source) |
