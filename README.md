# Zero-to-One

**A personal experiment in multi-agent AI orchestration.**

I built this for fun — to explore what Claude Code can do when you push it beyond single tasks and into a full pipeline of coordinated agents. The idea: simulate a complete startup organization, from idea validation to working codebase, with each agent playing a specific role and handing off to the next through files.

It's not a finished product and it won't work perfectly out of the box. Output quality varies by idea, by agent, and by how much you guide it. Think of it as a starting point to fork, adapt, and improve — not something you run once and ship.

> **What it does:** takes an idea through market validation → product definition → UX + architecture → MVP codebase, with two human approval gates to keep things from going sideways.
> 
> **What it doesn't do:** guarantee quality output, replace real product thinking, or build production-ready code without iteration.

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
              ┌──────────┴───────────┐   (parallel, every PR)
              ▼                     ▼
          security             architect
          engineer              reviewer
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

## Example

Here's a real prompt that was run through the full pipeline:

```
/startup "A shared expense tracker for friend groups, couples, and roommates
who are tired of the mental overhead of 'who owes who what'. You create a
group, add members, log expenses as you go — who paid, how much, and who
it's split between — and the app keeps a running balance for everyone.
One-tap settle-up suggestions show the minimum number of transfers needed
to clear all debts. Free to use. No sign-up friction — create a group with
a shareable link, members join without an account. B2C. Zero external
dependencies."
```

What came out: business analysis (GO verdict, Splitwise as primary competitor), a full PRD with minimum-transfer algorithm as the hero feature, 8 HTML prototype screens, a complete technical spec with OpenAPI, Alembic migrations, a FastAPI backend, a Next.js 16 frontend, Docker Compose stack, and GitHub Actions CI/CD — all in one pipeline run with zero external accounts or API keys.

Output lives in `workspace/fairsplit/`. Open `workspace/fairsplit/prototype/index.html` to see the prototype, or `cd workspace/fairsplit/src && docker compose up` to run the full stack.

---

## How to Use

There are two entry points depending on where you are:

**Want to validate before committing?**
```
/prototype "your idea"       # idea → working demo in hours, no specs, no reviews
                             # show it to 5 real users — if they want it, run /startup
```

**Ready to build properly?**
```
/startup "your idea here"    # idea → business analysis → PRD → design + arch → roadmap
/build <project>             # foundation → features → billing → email
```

**Want the strategic analysis first, without building?**
```
/ideate "your idea"          # Business analysis + PRD — clear GO / NO-GO before committing
```

Once you have a validated idea (from `/prototype`) or a strategic analysis (from `/ideate`), continue with:

### Individual Phases
```
/design <project>            # UX design spec + HTML prototype
/architect <project>         # Technical architecture + API spec
/build <project> [feature]   # Engineering pipeline
/sprint <project>            # Plan next Linear sprint
/refine <project> <doc>      # Improve a specific document based on feedback
```

### Quality Reviews
```
/review-pr <PR-url>          # Full 2-agent PR review (security + architecture)
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

**First-iteration rule:** Everything runs with `docker compose up` — zero external accounts, zero credit cards, zero cloud setup required. Mailpit catches all email locally. Stripe test mode charges nothing.

---

## Pipeline Gates

Two mandatory approval gates prevent building the wrong thing:

1. **Viability Gate** (after business analysis) — Presents TAM, LTV:CAC, top risks. If NO-GO, stops entirely. If GO/CONDITIONAL GO, waits for explicit user approval before continuing.

2. **Plan & Milestones Gate** (before any code is written) — Presents the full execution plan with epics, tasks, sprint breakdown, and Linear issue count. Waits for explicit user approval before launching engineering agents.

---

## Setup

**Option 1 — npx (recommended)**
```bash
npx idea-to-app ~/projects/my-app
```
This copies the framework into your target directory and runs `git init`. Then open the directory in Claude Code and you're ready to go.

**Option 2 — Clone**
```bash
git clone https://github.com/ricardovalves/zero-to-one.git
node bin/cli.js ~/projects/my-app
```

Then optionally set environment variables for integrations:
```bash
export LINEAR_API_KEY=your_linear_key      # for Linear issue creation
export ANTHROPIC_API_KEY=your_key          # if not already set by Claude Code
```

Open the project directory in Claude Code and run `/prototype "your idea"` or `/startup "your idea"` to begin.

No other setup required. The full stack runs locally via Docker.

---

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- Docker + Docker Compose (for local development)
- Python 3.11+ (for integration tools)
- Linear account (optional, for sprint management)

---

## What's in here

### Currently built

| What | Notes |
|---|---|
| `/prototype` — rapid validation mode | idea → working demo (login + core feature + seeded data) in hours, no specs or reviews. Show to 5 users. If validated → `/startup` |
| Business analysis → PRD → Design → Architecture pipeline | The strategic phase — generally the most reliable part |
| Parallel agent execution (UX + CTO, backend + frontend + infra) | Agents run concurrently where possible |
| Viability Gate + Plan & Milestones Gate | Two human checkpoints before work progresses |
| Project CLAUDE.md + src/CLAUDE.md auto-generation | Context files that carry decisions between phases |
| Stripe billing agent | Checkout, webhooks, plan gating |
| Transactional email agent | Mailpit locally, Resend in production |
| Smoke test loop with agent self-improvement | Catches the most common build failures before handoff |
| Idea sharpening pre-step | 4 targeted questions before any agent runs — improves output quality across the board |
| Contradiction detection | Scans agent handoffs for misaligned assumptions before build starts |
| Assumption tracking | Every agent logs its assumptions to a shared file; surfaced at each human gate |
| `/refine` command | Improve a specific document based on feedback without re-running the whole pipeline |
| HTTP security headers + global rate limiting | Baked into the backend skeleton |
| OWASP Top 10 (2025) + API Security Top 10 + LLM Top 10 | Security engineer runs all three checklists; LLM checklist applies only when AI features are present |

### Things I'd like to explore next

- `/deploy` — one-command deploy to Fly.io
- Landing page agent — static marketing site generated from the PRD
- Social login / OAuth support
- A feedback loop where real user feedback feeds back into the sprint planner
