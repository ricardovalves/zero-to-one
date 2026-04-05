# Performance Checklist Reference

Shared reference for `backend-engineer`, `frontend-engineer`, and `architecture-reviewer`.
Measure before optimising — performance work without data is guessing.

The tools and framework references below reflect common ecosystem defaults. Projects using a
different stack should override them in `workspace/{project}/src/CLAUDE.md`.

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

- [ ] **N+1 query check:** No DB calls inside a loop. Use eager loading / batch loading for relationships, or batch with `WHERE id IN (...)`.
  ```
  # ❌ N+1:
  for each record:
      record.related = fetch_related(record.id)

  # ✅ Batch:
  records = fetch_all_with_related_preloaded()
  ```
- [ ] **Pagination:** All list endpoints are paginated. No unbounded queries on user-data tables.
- [ ] **Indexes:** Every filtered column on tables > 10K rows has an index. Every foreign key has an index.
- [ ] **Avoid `OFFSET` on large tables:** Use cursor-based pagination (filter by `created_at < last_cursor`) for tables that grow unboundedly.
- [ ] **Aggregate return types:** Aggregate functions (SUM, COUNT) may return unexpected types — cast immediately to the expected type before use.

### Async / concurrency correctness

- [ ] **No blocking I/O in async handlers:** CPU-bound or blocking operations (password hashing, file reads, heavy computation) must run in a thread pool or worker — not on the async event loop.
- [ ] **No blocking sleep:** Use the async-native sleep primitive — never a synchronous `sleep()` call.
- [ ] **Connection pool sized correctly:** Default pool sizes are fine for prototypes; increase for production load.

### API response size

- [ ] Response bodies don't include unused fields (use schema exclusion where appropriate)
- [ ] List endpoints default `per_page` ≤ 50; maximum capped at 100

---

## Frontend Performance Checklist

### Component and rendering

- [ ] **Server rendering by default:** Only opt into client-side rendering when you need browser APIs, interactivity, or component state.
- [ ] **Images:** Use the framework's image component with explicit dimensions and responsive `sizes`. Never use a raw `<img>` tag for above-the-fold content.
- [ ] **Fonts:** Preload the primary font with `font-display: swap` to avoid invisible text during load.
- [ ] **Effect dependency arrays:** Complete and correct. Missing deps cause stale closures; extra deps cause unnecessary re-fetches.
- [ ] **Expensive computations:** Memoized so they don't re-run on every render. Stable function references passed as props are also memoized.
- [ ] **List keys:** Stable, unique IDs — never array index for mutable lists.

### Bundle size

- [ ] No library imported for a single utility function — use native language/platform APIs instead.
- [ ] Heavy libraries (chart libraries, PDF generators) lazy-loaded and excluded from the initial bundle.
- [ ] Check the route size output after build — flag any route > 200KB first-load JS.

### Loading states

- [ ] Skeleton UIs instead of spinners for layout-affecting content (prevents CLS).
- [ ] Skeletons match the loaded content dimensions exactly.
- [ ] Loading state provided for every dynamic route or async data segment.

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

# Backend — enable query logging temporarily to find N+1 patterns:
# Set the ORM/database engine to echo SQL (project-specific — see src/CLAUDE.md)

# Frontend — Lighthouse via CLI:
npx lighthouse http://localhost:3000 --output=json --only-categories=performance | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print('Score:', d['categories']['performance']['score'] * 100)"

# Frontend — bundle analysis:
# Run the framework's bundle analyzer (project-specific — see src/CLAUDE.md)
```

---

## Performance Budget (CI enforcement)

Set these as CI gates in the project's CI configuration:

| Budget | Limit | Tool |
|---|---|---|
| First Load JS per route | 200KB | Build output |
| API p95 latency | 500ms | Load test (e.g. k6, locust) |
| LCP | 2.5s | Lighthouse CI |
| High-severity dependency CVEs | 0 | Dependency audit in CI |
