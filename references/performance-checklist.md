# Performance Checklist Reference

Shared reference for `backend-engineer`, `frontend-engineer`, and `architecture-reviewer`.
Measure before optimising — performance work without data is guessing.

---

## Web Vitals Targets

| Metric | Good | Needs Work | Poor |
|---|---|---|---|
| LCP (Largest Contentful Paint) | ≤ 2.5s | 2.5–4s | > 4s |
| INP (Interaction to Next Paint) | ≤ 200ms | 200–500ms | > 500ms |
| CLS (Cumulative Layout Shift) | ≤ 0.1 | 0.1–0.25 | > 0.25 |
| TTFB (Time to First Byte) | ≤ 800ms | 800ms–1.8s | > 1.8s |

---

## Backend Performance Checklist

### Database queries

- [ ] **N+1 query check:** No DB calls inside a loop. Use `selectinload` / `joinedload` for relationships, or batch with `WHERE id IN (...)`.
  ```python
  # ❌ N+1:
  for user in users:
      user.subscription = await repo.get_subscription(user.id)

  # ✅ Batch:
  users = await db.execute(
      select(User).options(selectinload(User.subscription))
  )
  ```
- [ ] **Pagination:** All list endpoints are paginated. No unbounded `SELECT *` on user-data tables.
- [ ] **Indexes:** Every `WHERE` column on tables > 10K rows has an index. Every FK has an index.
- [ ] **Avoid `OFFSET` on large tables:** Use cursor-based pagination (filter by `created_at < last_cursor`) for tables that grow unboundedly.
- [ ] **`func.sum()` returns Decimal:** Cast immediately — `int((await db.execute(...)).scalar() or 0)`.

### Async correctness

- [ ] **No sync I/O in async handlers:** bcrypt, file reads, and any CPU-bound work run in `asyncio.run_in_executor(None, ...)`.
- [ ] **No blocking sleep:** Use `asyncio.sleep()`, never `time.sleep()`.
- [ ] **Connection pool sized correctly:** Default asyncpg pool of 5 is fine for prototypes; set `pool_size=20` for production.

### API response size

- [ ] Response bodies don't include unused fields (Pydantic `exclude_none=True` where appropriate)
- [ ] List endpoints default `per_page` ≤ 50; maximum capped at 100

---

## Frontend Performance Checklist

### Next.js / React

- [ ] **Server Components by default:** Only add `'use client'` when you need hooks, browser APIs, or event handlers.
- [ ] **Images:** Use `next/image` with explicit `width`, `height`, and `sizes`. Never `<img>` for above-the-fold content.
- [ ] **Fonts:** Use `next/font` with `display: 'swap'`. Preload the primary font.
- [ ] **`useEffect` dependency arrays:** Complete and correct. Missing deps cause stale closures; extra deps cause unnecessary re-fetches.
- [ ] **Expensive computations:** Wrapped in `useMemo`. Stable function references passed as props wrapped in `useCallback`.
- [ ] **List keys:** Stable, unique IDs — never array index for mutable lists.

### Bundle size

- [ ] No library imported for a single utility function (e.g., lodash for one `_.debounce` call — use native `setTimeout`).
- [ ] Heavy libraries (chart libraries, PDF generators) lazy-loaded with `dynamic(() => import(...), { ssr: false })`.
- [ ] Run `npm run build` and check the route size output — flag any route > 200KB first load JS.

### Loading states

- [ ] Skeleton UIs instead of spinners for layout-affecting content (prevents CLS).
- [ ] Skeletons match the loaded content dimensions exactly.
- [ ] `loading.tsx` provided for every dynamic route segment.

---

## Measurement Commands

```bash
# Backend — check slow queries (PostgreSQL):
docker compose exec db psql -U postgres -d {db_name} -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
"

# Backend — check for N+1 patterns (SQLAlchemy echo):
# Add to database.py temporarily:
engine = create_async_engine(settings.DATABASE_URL, echo=True)

# Frontend — Lighthouse via CLI:
npx lighthouse http://localhost:3000 --output=json --only-categories=performance | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('Score:', d['categories']['performance']['score'] * 100)"

# Frontend — bundle analysis:
cd workspace/{project}/src/frontend && ANALYZE=true npm run build
```

---

## Performance Budget (CI enforcement)

Set these as CI gates in `.github/workflows/ci.yml`:

| Budget | Limit | Tool |
|---|---|---|
| First Load JS per route | 200KB | `next build` output |
| API p95 latency | 500ms | Load test with `k6` or `locust` |
| LCP | 2.5s | Lighthouse CI |
| npm audit high severity | 0 | `npm audit --audit-level=high` |
