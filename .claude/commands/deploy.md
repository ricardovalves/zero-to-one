Take a locally working project and deploy it to a real, publicly accessible URL.

Guides the full production deployment: GitHub repo setup, cloud hosting (Fly.io default), secrets configuration, domain + SSL, smoke tests, and a live URL the user can share with customers.

Usage: /deploy <project-name> [--provider fly|coolify|vps]

Arguments: $ARGUMENTS

---

## Orchestration Rules

- This command is run AFTER `/build` has completed and `docker compose up` works locally
- Default provider: **Fly.io** (free tier, 3 shared VMs + 3GB Postgres, no credit card required)
- Alternative: **Coolify** (open-source Heroku, self-hosted on a $6/mo Hetzner VPS)
- All steps are interactive — pause and verify with the user before irreversible actions

---

## Pipeline

### STEP 1: Verify build is ready

Check that these files exist — if any are missing, stop and tell the user what to run first:
- `workspace/{project}/src/docker-compose.yml`
- `workspace/{project}/src/backend/Dockerfile`
- `workspace/{project}/src/frontend/Dockerfile`
- `workspace/{project}/src/.env.local.example`

Read `workspace/{project}/handoffs/cto-architect.md` for stack decisions.

Ask the user:
```
Before deploying — confirm:
1. Does `docker compose up` work locally? (yes / no)
2. Have you run `seed.py` and confirmed logins work? (yes / no)
3. Do you have a domain name? (yes: {domain} / no: we'll use fly.dev subdomain)

Provider: Fly.io (free tier, no credit card for hobby plan)
Proceed? (yes / no)
```

Wait for confirmation.

---

### STEP 2: GitHub repository

Check if the project already has a GitHub remote:
```bash
cd workspace/{project}/src && git remote -v
```

If no remote exists:
```bash
# Create GitHub repo and push:
gh repo create {project} --private --source=workspace/{project}/src --push
```

If it already exists — skip this step.

Print the repo URL. Ask the user to confirm before proceeding to secrets setup.

---

### STEP 3: Environment secrets inventory

Read `workspace/{project}/src/.env.local.example` to list all required secrets.

Present the secrets checklist to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SECRETS REQUIRED FOR PRODUCTION — {project}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
These must be set before deployment. Never commit these to git.

Required:
  DATABASE_URL          → auto-configured by Fly Postgres
  SECRET_KEY            → generate: openssl rand -hex 32
  JWT_SECRET            → generate: openssl rand -hex 32
  FRONTEND_URL          → https://{project}.fly.dev (or your domain)

Email (choose one):
  RESEND_API_KEY        → from resend.com (free tier: 3K emails/month)
  — or —
  SMTP_HOST/PORT/USER/PASSWORD  → from your SMTP provider

Stripe (skip if not yet implemented):
  STRIPE_SECRET_KEY     → from dashboard.stripe.com (test key for now)
  STRIPE_WEBHOOK_SECRET → generated after deploy (Step 6)
  STRIPE_PUBLISHABLE_KEY → from dashboard.stripe.com

Optional:
  POSTHOG_KEY           → from posthog.com or your self-hosted instance
  SENTRY_DSN            → from sentry.io (free tier)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Have these values ready? (yes / not all — I'll skip the ones I don't have)
```

Wait for user. They can proceed without some secrets (e.g., Stripe) and add them later.

---

### STEP 4: Fly.io deployment

#### 4a — Install Fly CLI (if needed)
```bash
which fly || curl -L https://fly.io/install.sh | sh
fly auth whoami || fly auth login
```

#### 4b — Launch backend on Fly.io
```bash
cd workspace/{project}/src/backend

# Initialize Fly app (only first time):
fly launch --name {project}-backend --region {closest region} --no-deploy

# Provision Postgres (free tier):
fly postgres create --name {project}-db --region {region} --vm-size shared-cpu-1x --volume-size 1
fly postgres attach {project}-db --app {project}-backend
```

#### 4c — Set secrets on Fly.io
```bash
fly secrets set \
  SECRET_KEY="$(openssl rand -hex 32)" \
  JWT_SECRET="$(openssl rand -hex 32)" \
  FRONTEND_URL="https://{project}-frontend.fly.dev" \
  EMAIL_PROVIDER="resend" \
  RESEND_API_KEY="{from user}" \
  --app {project}-backend
```

Only set secrets the user has provided. For missing ones (Stripe, etc.) — note them as TODO and continue.

#### 4d — Deploy backend
```bash
cd workspace/{project}/src/backend
fly deploy --app {project}-backend
```

Wait for deployment. Check health:
```bash
fly status --app {project}-backend
curl https://{project}-backend.fly.dev/health
```

Must return `{"status": "ok"}`. If not, run `fly logs --app {project}-backend` and diagnose.

#### 4e — Run database migrations + seed
```bash
fly ssh console --app {project}-backend --command "alembic upgrade head"
fly ssh console --app {project}-backend --command "python seed.py"
```

Print the seed output (emails + passwords) for the user to save.

#### 4f — Deploy frontend
```bash
cd workspace/{project}/src/frontend

fly launch --name {project}-frontend --region {region} --no-deploy

fly secrets set \
  NEXT_PUBLIC_API_URL="https://{project}-backend.fly.dev/api/v1" \
  NEXT_PUBLIC_SHOW_DEV_PANEL="true" \
  --app {project}-frontend

fly deploy --app {project}-frontend
```

---

### STEP 5: Domain setup (optional)

If the user provided a domain name:

```bash
# Backend:
fly certs add api.{domain} --app {project}-backend

# Frontend:
fly certs add {domain} --app {project}-frontend
fly certs add www.{domain} --app {project}-frontend
```

Print the DNS records they need to add to their domain registrar:
```
DNS Records to add:
  {domain}      A/CNAME → {fly IP}
  www.{domain}  CNAME   → {project}-frontend.fly.dev
  api.{domain}  CNAME   → {project}-backend.fly.dev
```

Ask: "Have you added the DNS records? SSL certificates will provision automatically. (yes / skip for now)"

---

### STEP 6: Stripe webhook (if Stripe is configured)

After the backend is live, register the production webhook endpoint:
```bash
# In Stripe Dashboard → Developers → Webhooks → Add endpoint:
# URL: https://{project}-backend.fly.dev/api/v1/billing/webhook
# Events: checkout.session.completed, customer.subscription.updated,
#          customer.subscription.deleted, invoice.payment_failed, invoice.payment_succeeded
```

Print the webhook signing secret, then set it:
```bash
fly secrets set STRIPE_WEBHOOK_SECRET="whsec_..." --app {project}-backend
```

---

### STEP 7: Production smoke tests

Run these against the live URL:
```bash
BASE="https://{project}-backend.fly.dev/api/v1"

# 1. Health check
curl "$BASE/../health"  # → {"status": "ok"}

# 2. Login with seeded admin account
TOKEN=$(curl -s -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"{admin email}","password":"{admin password}"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['data']['access_token'])")
echo "Login token: ${TOKEN:0:20}..."  # must not be empty

# 3. Primary resource endpoints
for EP in $(grep -E "^  /api/v1/" workspace/{project}/api-spec.yaml | grep "get:" -B1 | grep "^  /api" | awk '{print $1}'); do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE$EP" -H "Authorization: Bearer $TOKEN")
  echo "GET $EP → $STATUS"  # must be 200 (never 422 or 500)
done

# 4. Frontend responds
curl -s -o /dev/null -w "%{http_code}" "https://{project}-frontend.fly.dev"  # → 200
```

If any check fails — diagnose before declaring done:
- `401` → JWT secret mismatch between environments
- `422` → Missing required env var in production
- `500` → Run `fly logs --app {project}-backend` to find the error

---

### STEP 8: GitHub Actions secrets

For automated CI/CD on push-to-main, set these in GitHub:
```bash
gh secret set FLY_API_TOKEN --body "$(fly auth token)"
gh secret set STRIPE_SECRET_KEY --body "{value}"
# ... all other production secrets
```

Print the secrets list so the user knows what to configure in the GitHub repo settings.

---

### STEP 9: Summary

```
/deploy complete ✓
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Project:   {project}
Frontend:  https://{domain or project-frontend.fly.dev}
Backend:   https://{domain or project-backend.fly.dev}
API docs:  https://{project}-backend.fly.dev/docs

Seed accounts:
  {email} / {password}  ({role})
  ...

What's live:
  ✓ Database (Fly Postgres)
  ✓ Backend API
  ✓ Frontend app
  {✓/✗} Email ({provider})
  {✓/✗} Stripe webhooks
  {✓/✗} Custom domain

Pending (set secrets and redeploy):
  {list of skipped secrets}

CI/CD: every push to main auto-deploys (once GitHub secrets are set).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Write a deploy summary to `workspace/{project}/deployment.md` with all URLs, secrets checklist status, and DNS records.
