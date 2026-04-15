# Infra Engineer Handoff — FairSplit

**Date:** 2026-04-15
**Authored by:** Infra Engineer Agent

---

## Key Facts for Downstream Agents

1. **Local stack:** `docker compose up` from `workspace/fairsplit/src/` starts all 7 services (db, migrate, backend, frontend, prometheus, grafana, mailpit) with zero external dependencies. All ports documented in README.
2. **Startup order:** db (healthcheck: pg_isready) → migrate (alembic upgrade head, restart: no) → backend (healthcheck: /health) → frontend. Prometheus/Grafana/Mailpit start in parallel with no app dependency.
3. **Frontend Dockerfile ARG:** `NEXT_PUBLIC_SHOW_DEV_PANEL` is passed as a Docker build arg (not an environment variable) so it is baked into the Next.js bundle at build time. The docker-compose passes `NEXT_PUBLIC_SHOW_DEV_PANEL=true`. Production CD builds pass `false`. Never gate this on `NODE_ENV`.
4. **Multi-stage Dockerfiles created:** `src/backend/Dockerfile` (python:3.12-slim builder using uv → python:3.12-slim runner) and `src/frontend/Dockerfile` (node:20-alpine deps → node:20-alpine builder with Next.js standalone output → node:20-alpine runner). Both run as non-root user `app`/`nextjs` (uid 1001).
5. **CI workflow:** 5 parallel jobs on every PR — `lint-backend` (ruff), `lint-frontend` (ESLint + tsc), `test-backend` (pytest + postgres service container + coverage), `build-docker` (validates both Dockerfiles), `security-scan` (pip-audit + npm audit + Trivy). Target: under 5 minutes.
6. **CD workflow:** Sequential — CI gate → build+push to GHCR → migrate (fly ssh console) → deploy backend → deploy frontend → smoke test → rollback on failure. `DEPLOY_TARGET` repo variable selects `fly`/`vercel`/`vps`. Default is Fly.io backend + Vercel frontend.
7. **Smoke test:** `src/smoke_test.py` covers 12 checks — health endpoint, group creation, idempotency re-submission, join via invite, authenticated group fetch, member list, empty-state balances/settle-up, expense logging, non-zero balances after expense, settle-up with transfers, frontend availability. Uses stdlib only (no httpx required locally).
8. **Grafana dashboard:** Auto-provisioned at `src/infra/grafana/provisioning/`. Dashboard uid `fairsplit-main` with 4 stat panels (request rate, 5xx error rate, p95 latency, active groups) and 8 time-series panels covering throughput, error breakdown, latency percentiles, and business metrics. No manual setup after `docker compose up`.
9. **Secrets:** All documented in `src/.env.local.example`. Backend secrets for staging/production: `FLY_API_TOKEN`, `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `PRODUCTION_API_URL`, `PRODUCTION_FRONTEND_URL`. Never committed to code.
10. **Rollback:** Fly.io — `flyctl releases rollback --app fairsplit-backend`. VPS — re-pull previous image tag and restart container. CD workflow triggers rollback automatically on smoke test failure.

---

## Files Written

- `workspace/fairsplit/src/docker-compose.yml` — full local stack, 7 services, named volumes, shared network
- `workspace/fairsplit/src/backend/Dockerfile` — multi-stage, uv install, non-root, health check
- `workspace/fairsplit/src/backend/.dockerignore`
- `workspace/fairsplit/src/backend/requirements.txt` — pinned versions (FastAPI 0.115.6, SQLAlchemy 2.0.36, etc.)
- `workspace/fairsplit/src/frontend/Dockerfile` — multi-stage Next.js standalone, non-root, health check
- `workspace/fairsplit/src/frontend/.dockerignore`
- `workspace/fairsplit/src/infra/prometheus/prometheus.yml` — scrapes backend:8000/metrics every 15s
- `workspace/fairsplit/src/infra/grafana/provisioning/datasources/prometheus.yml` — auto-provision datasource
- `workspace/fairsplit/src/infra/grafana/provisioning/dashboards/dashboard.yml` — dashboard provider config
- `workspace/fairsplit/src/infra/grafana/provisioning/dashboards/fairsplit.json` — complete dashboard JSON (uid: fairsplit-main)
- `workspace/fairsplit/src/.github/workflows/ci.yml` — 5-job parallel CI pipeline
- `workspace/fairsplit/src/.github/workflows/cd.yml` — full CD with migrate, deploy, smoke test, rollback
- `workspace/fairsplit/src/smoke_test.py` — 12-check post-deploy validation script
- `workspace/fairsplit/src/.env.local.example` — all required env vars documented
- `workspace/fairsplit/src/README.md` — full developer guide (run locally, seed data, dev panel, ports, CI/CD, observability)

---

## For Backend Engineer

- The backend Dockerfile expects `app/main.py` to export the FastAPI app as `app.main:app`
- The backend Dockerfile builds from `requirements.txt` — keep this file updated as new dependencies are added
- The health endpoint `GET /health` must return `{"status": "ok", "version": "x.y.z", "db": "ok"}` — it is hit by Docker healthcheck every 10s
- Prometheus metrics are at `GET /metrics` — enable via `prometheus-fastapi-instrumentator` in `main.py`
- The migrate service uses the `builder` stage of the backend Dockerfile to run `alembic upgrade head` — ensure alembic.ini and migrations/ are present at the root of the backend build context

## For Frontend Engineer

- The frontend Dockerfile uses Next.js standalone output — `next.config.js` must set `output: "standalone"`
- `NEXT_PUBLIC_SHOW_DEV_PANEL` is a Dockerfile build ARG baked in at build time — access it as `process.env.NEXT_PUBLIC_SHOW_DEV_PANEL === "true"` (string comparison, not boolean)
- The dev panel receives `NEXT_PUBLIC_SHOW_DEV_PANEL=true` from docker-compose automatically
- Frontend health check in Docker uses wget (available in node:20-alpine) — ensure the root route (`/`) returns 200
