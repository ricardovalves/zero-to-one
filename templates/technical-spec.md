# Technical Specification: {Project Name}

**Version:** 1.0
**Date:** {YYYY-MM-DD}
**Author:** CTO/Architect Agent
**Status:** Draft / Review / Approved
**Referenced PRD:** workspace/{project}/prd.md
**Referenced Design Spec:** workspace/{project}/design-spec.md

---

## 1. Architecture Overview (C4 Model)

### Level 1 — System Context

```
                    ┌─────────────────────┐
                    │   {Product Name}    │
                    │   System            │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
   [End Users]          [Admin Users]         [External Systems]
   (via Web/Mobile)    (via Dashboard)        ({list integrations})
```

### Level 2 — Container Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  {Product Name}                                             │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Web App     │    │  API Server  │    │  Database    │  │
│  │  (Next.js)   │───►│  (FastAPI)   │───►│  (PostgreSQL)│  │
│  │  Vercel      │    │  Railway     │    │  NeonDB      │  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘  │
│                             │                               │
│                    ┌────────▼────────┐                      │
│                    │  External APIs  │                      │
│                    │  {list them}    │                      │
│                    └─────────────────┘                      │
└─────────────────────────────────────────────────────────────┘
```

### Level 3 — Component Diagram (API Server)

```
API Server (FastAPI)
│
├── /api/v1/auth           → AuthRouter
│   ├── POST /register     → AuthService → UserRepository
│   ├── POST /login        → AuthService → JWTService
│   └── POST /refresh      → JWTService
│
├── /api/v1/{resource}     → {Resource}Router
│   ├── GET /              → {Resource}Service → {Resource}Repository
│   ├── POST /             → {Resource}Service → {Resource}Repository
│   ├── GET /{id}          → {Resource}Service → {Resource}Repository
│   ├── PUT /{id}          → {Resource}Service → {Resource}Repository
│   └── DELETE /{id}       → {Resource}Service → {Resource}Repository
│
└── Middleware
    ├── AuthMiddleware (JWT validation)
    ├── RateLimitMiddleware
    └── RequestLoggingMiddleware
```

---

## 2. Technology Stack

### Prototype (Free Tier)

| Layer | Technology | Version | Rationale |
|---|---|---|---|
| Frontend Framework | Next.js | 15.x (App Router) | {reason} |
| UI Library | shadcn/ui + Tailwind CSS | latest | {reason} |
| Backend Framework | FastAPI | 0.115.x | {reason} |
| Database | PostgreSQL 16 via NeonDB | free tier | {reason} |
| ORM / Query Builder | Drizzle ORM or SQLAlchemy | latest | {reason} |
| Auth | Clerk or NextAuth.js | latest | {reason} |
| Frontend Hosting | Vercel | free tier | {reason} |
| Backend Hosting | Railway | free tier | {reason} |
| CI/CD | GitHub Actions | — | {reason} |
| Error Tracking | Sentry | free tier | {reason} |

### Production (Scale)

| Layer | Technology | Change from Prototype |
|---|---|---|
| Frontend Hosting | AWS CloudFront + S3 | Cost at scale, global CDN |
| Backend Hosting | AWS ECS Fargate | Container orchestration, auto-scale |
| Database | AWS RDS Aurora Serverless v2 | Managed, multi-AZ, auto-scale |
| Cache | Redis via Upstash or AWS ElastiCache | Session cache, rate limiting |
| Storage | AWS S3 | File/media storage |
| Monitoring | Datadog | Full observability |

---

## 3. API Design

**Standard:** OpenAPI 3.1 (see `api-spec.yaml` for full spec)
**Base URL (prototype):** `https://api.{project}.railway.app/api/v1`
**Authentication:** Bearer JWT in `Authorization` header

### Endpoint Summary

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | None | Create account |
| POST | `/auth/login` | None | Authenticate, receive JWT |
| POST | `/auth/refresh` | Refresh token | Refresh access token |
| GET | `/{resource}` | Required | List resources (paginated) |
| POST | `/{resource}` | Required | Create resource |
| GET | `/{resource}/{id}` | Required | Get single resource |
| PUT | `/{resource}/{id}` | Required | Update resource |
| DELETE | `/{resource}/{id}` | Required | Delete resource |

### Standard Response Format

```json
{
  "data": {},
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  },
  "error": null
}
```

### Error Format

```json
{
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  }
}
```

---

## 4. Database Schema

**Database:** PostgreSQL 16
**Naming convention:** `snake_case` for all tables and columns
**Timestamps:** All tables have `created_at TIMESTAMPTZ DEFAULT now()` and `updated_at TIMESTAMPTZ DEFAULT now()`
**IDs:** UUID v4 primary keys

```sql
-- Users
CREATE TABLE users (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email       TEXT NOT NULL UNIQUE,
  name        TEXT NOT NULL,
  avatar_url  TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- {Additional tables based on product requirements}
CREATE TABLE {table_name} (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  -- {columns}
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_{table}_{column} ON {table}({column});
```

---

## 5. Non-Functional Requirements (NFRs)

### Performance
| Requirement | Target | Measurement |
|---|---|---|
| API p50 latency | < 100ms | Datadog APM |
| API p99 latency | < 500ms | Datadog APM |
| Page load (LCP) | < 2.5s | Core Web Vitals |
| Database query p99 | < 50ms | NeonDB metrics |

### Scalability
| Concern | Approach |
|---|---|
| Horizontal scaling | Stateless API servers; sessions in Redis |
| Database scaling | Read replicas for read-heavy queries; connection pooling (PgBouncer) |
| Cache strategy | {cache-aside / write-through} — Redis for {what} |

### Availability
| Requirement | Target | Approach |
|---|---|---|
| Uptime | 99.9% (8.7h downtime/year) | Multi-AZ database, health checks, auto-restart |
| Graceful degradation | Core flows work if non-critical services fail | Circuit breakers on external API calls |
| Backup | Daily automated DB snapshots | NeonDB built-in / pg_dump to S3 |

### Security
| Control | Implementation |
|---|---|
| Authentication | JWT (15min access token, 7d refresh token, httpOnly cookie) |
| Authorization | RBAC — roles defined in DB, checked in service layer |
| Input validation | Pydantic (backend) + Zod (frontend) |
| SQL injection | ORM parameterized queries only; no raw SQL with user input |
| Rate limiting | 100 req/min per IP on public endpoints; 1000 req/min per user |
| CORS | Allowlist of origins only |
| Secrets | Environment variables only; never in code or logs |
| HTTPS | Enforced; HSTS header |

### Observability
| Signal | Tool | What's Captured |
|---|---|---|
| Logs | Structured JSON to stdout → Vercel/Railway log drain | Request/response, errors, slow queries |
| Metrics | Prometheus-compatible | Request rate, error rate, latency, DB connections |
| Traces | OpenTelemetry | Distributed traces across frontend → API → DB |
| Errors | Sentry | Frontend + backend exceptions with stack traces |
| Alerts | Sentry alerts | Error rate spike, p99 latency > 1s |

---

## 6. Deployment Architecture

### Prototype Pipeline

```
Developer → GitHub PR
    │
    ▼
GitHub Actions CI
  ├── lint + typecheck
  ├── unit tests
  └── integration tests
    │
    ▼ (merge to main)
GitHub Actions CD
  ├── Build + push Docker image
  ├── Deploy backend → Railway
  └── Deploy frontend → Vercel (automatic)
```

### Environment Strategy

| Environment | Purpose | Database | URL |
|---|---|---|---|
| Development | Local dev | Local PostgreSQL or NeonDB dev branch | localhost |
| Preview | PR previews | NeonDB dev branch | Vercel preview URL |
| Production | Live | NeonDB production | {domain}.com |

### Infrastructure as Code
{Terraform / Pulumi for AWS production; Railway/Vercel configured via CLI and config files for prototype}

---

## 7. Architecture Decision Records (ADRs)

### ADR-001: {Decision Title}
- **Status:** Accepted
- **Context:** {why this decision was needed}
- **Decision:** {what was decided}
- **Consequences:** {trade-offs, what becomes easier/harder}

### ADR-002: {Decision Title}
{same structure}
