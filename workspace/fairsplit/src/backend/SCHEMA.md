# FairSplit — Database Schema Reference

## Entity-Relationship Diagram

```
groups
  id (PK, UUID)
  name, description, invite_token (UNIQUE), status, default_currency
  created_at, updated_at
     |
     |  ON DELETE CASCADE
     +──────────────────────────────────────────< members
     |                                             id (PK, UUID)
     |                                             group_id (FK → groups)
     |                                             display_name, is_admin, joined_at
     |                                             created_at, updated_at
     |
     |  ON DELETE CASCADE
     +──────────────────────────────────────────< expenses
     |    |                                        id (PK, UUID)
     |    |                                        group_id (FK → groups)
     |    |                                        payer_member_id (FK → members, RESTRICT)
     |    |                                        logged_by_member_id (FK → members, RESTRICT)
     |    |                                        description, amount_cents, currency
     |    |                                        split_type, expense_date, deleted_at
     |    |                                        created_at, updated_at
     |    |
     |    |  ON DELETE CASCADE
     |    +────────────────────────────────────< expense_splits
     |                                            id (PK, UUID)
     |                                            expense_id (FK → expenses)
     |                                            member_id (FK → members, RESTRICT)
     |                                            amount_cents, percentage
     |                                            created_at, updated_at
     |                                            UNIQUE(expense_id, member_id)
     |
     |  ON DELETE CASCADE
     +──────────────────────────────────────────< settlements
                                                   id (PK, UUID)
                                                   group_id (FK → groups)
                                                   payer_member_id (FK → members, RESTRICT)
                                                   payee_member_id (FK → members, RESTRICT)
                                                   amount_cents, currency, deleted_at
                                                   created_at, updated_at
                                                   CHECK(payer != payee)

idempotency_keys (standalone — no FK)
  key (PK, UUID — client-supplied)
  endpoint, response_body (JSONB), status_code (SMALLINT)
  created_at, expires_at
```

---

## Index Rationale

### `idx_groups_invite_token` — UNIQUE on `groups(invite_token)`

Every group join starts with `POST /api/v1/join/{invite_token}`. The server
does `SELECT * FROM groups WHERE invite_token = $1`. Without this index, every
join is a full table scan. At 10,000 groups this would be ~200ms per join.

The UNIQUE constraint is declared on the column itself AND as a named index so
the index name appears explicitly in EXPLAIN ANALYZE output rather than as a
system-generated name, making query plan analysis unambiguous.

### `idx_members_group_id` — on `members(group_id)`

Every group dashboard load (and every authenticated request) fetches all
members of a group: `SELECT * FROM members WHERE group_id = $1`. The balance
CTE also uses this for the outer query (JOIN members WHERE group_id = $1).

Without this index, the planner must scan the entire members table for each
group. At 100,000 members across 10,000 groups, an average of 10 members per
group means a 100,000-row scan returns 10 rows — extremely inefficient.

### `idx_expenses_group_id_active` — PARTIAL on `expenses(group_id, created_at DESC) WHERE deleted_at IS NULL`

The primary read path for the expense list:
```sql
SELECT * FROM expenses
WHERE group_id = $1 AND deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 20
```

Column order is critical: `group_id` (equality predicate) goes first, then
`created_at DESC` (sort key) goes second. This ordering allows the planner to
satisfy both the filter and the ORDER BY from a single Index Scan — no sort
step needed.

The `WHERE deleted_at IS NULL` partial condition reduces index size by
excluding soft-deleted expenses. In a typical group with 10 active and 2
deleted expenses, the index contains 10 rows rather than 12 — a small gain.
At 100,000 expenses group-wide with 15% deletion rate, the index is 17,000
rows smaller than a full index, reducing both storage and write amplification
on every new expense insertion.

### `idx_expenses_group_id_not_deleted` — PARTIAL on `expenses(group_id) WHERE deleted_at IS NULL`

The balance CTE does not ORDER BY — it aggregates:
```sql
SELECT payer_member_id, SUM(amount_cents)
FROM expenses
WHERE group_id = $1 AND deleted_at IS NULL
GROUP BY payer_member_id
```

Having a separate index without `created_at` saves 8 bytes per index entry vs.
using `idx_expenses_group_id_active` for this query. The planner will correctly
choose the simpler index for the aggregation and the composite index for the
sorted list query. Both indexes use the same partial predicate so write
amplification is minimal (both are updated on every INSERT and soft-delete).

### `idx_expenses_logged_by` — on `expenses(logged_by_member_id)`

Used for permission checks in PATCH and DELETE expense endpoints:
```sql
SELECT id FROM expenses
WHERE logged_by_member_id = $1 AND id = $2 AND deleted_at IS NULL
```

The primary key lookup on `id` alone is more selective, but the planner may
use this index to early-exit if the member has no logged expenses, avoiding
the PK lookup entirely. At typical data volumes this index provides ~2-5x
speedup for the permission check.

### `idx_expense_splits_expense_id` — on `expense_splits(expense_id)`

The JOIN path in every balance CTE and expense detail query:
```sql
JOIN expense_splits es ON es.expense_id = e.id
```

Without this index, every join scans the entire expense_splits table. At
100,000 splits (1,000 groups × 100 expenses × 10 splits average), this is a
full 100K-row scan for each expense detail lookup.

This is the highest-write-frequency index after the primary key — inserted
once per split, never updated. The write cost is negligible.

### `idx_expense_splits_member_id` — on `expense_splits(member_id)`

The balance CTE aggregates splits by member:
```sql
SELECT es.member_id, SUM(es.amount_cents)
FROM expense_splits es
JOIN expenses e ON e.id = es.expense_id
WHERE e.group_id = $1 AND e.deleted_at IS NULL
GROUP BY es.member_id
```

With this index, the planner can use an Index Scan on expense_splits filtered
by member_id and then aggregate — faster than a sequential scan + HashAgg for
small member sets. The benefit is most pronounced for the individual member
balance breakdown (`GET /groups/{id}/balances/{member_id}`).

### `idx_settlements_group_id_active` — PARTIAL on `settlements(group_id) WHERE deleted_at IS NULL`

The balance CTE queries active settlements by group:
```sql
SELECT payer_member_id, SUM(amount_cents) FROM settlements
WHERE group_id = $1 AND deleted_at IS NULL
GROUP BY payer_member_id
```

The partial index excludes reversed (soft-deleted) settlements. In a typical
group where 20% of settlements are reversed, the index is 20% smaller.
The settle-up algorithm also uses this query path — it is called on every
settle-up page view, making this one of the most frequent read paths.

### `idx_idempotency_keys_expires` — PARTIAL on `idempotency_keys(expires_at) WHERE expires_at > NOW()`

Used by two operations:
1. The cleanup task: `DELETE FROM idempotency_keys WHERE expires_at < NOW()`
2. The idempotency check: the primary lookup is by PK (`key`), but the expiry
   check `AND expires_at > NOW()` can be resolved by this index.

The `WHERE expires_at > NOW()` partial predicate keeps only active (non-expired)
keys in the index. Expired keys are excluded, which means the index shrinks as
the cleanup task runs. This prevents unbounded index growth for high-volume APIs.

Note: `NOW()` in a partial index predicate is evaluated at index creation time
(it is a snapshot, not dynamic). PostgreSQL correctly handles this — the
partial predicate uses the literal expression `expires_at > NOW()` stored in
the index definition, and the index is used when the query also contains
`expires_at > NOW()` or `expires_at > $1` with a comparable timestamp literal.

---

## Critical Constraints

| Table | Column | Constraint | Reason |
|---|---|---|---|
| `groups` | `name` | `length(trim(name)) > 0` | Prevents whitespace-only group names |
| `groups` | `status` | `IN ('active', 'archived')` | Only two valid group states |
| `groups` | `invite_token` | UNIQUE | Each invite link maps to exactly one group |
| `members` | `display_name` | `length(trim(display_name)) > 0` | Prevents empty display names |
| `members` | `group_id` | FK → groups, CASCADE | Member belongs to exactly one group |
| `expenses` | `amount_cents` | `> 0` | Zero-amount expenses are not permitted |
| `expenses` | `split_type` | `IN ('equal', 'custom_amount', 'custom_percentage')` | Only three valid split strategies |
| `expenses` | `payer_member_id` | FK → members, RESTRICT | Prevents orphaned expense if member is deleted |
| `expense_splits` | `amount_cents` | `>= 0` | Zero splits allowed for tracking purposes |
| `expense_splits` | `(expense_id, member_id)` | UNIQUE | A member appears at most once per expense |
| `settlements` | `amount_cents` | `> 0` | Settlements must be positive |
| `settlements` | `payer_member_id != payee_member_id` | CHECK | Prevents self-settlements |

---

## Common Query Patterns and Expected Execution Plans

### Query 1: Net balance computation (most critical)

Called on: `GET /api/v1/groups/{id}/balances` and `GET /api/v1/groups/{id}/settle-up`
Polling interval: every 10 seconds from all active clients.

```sql
WITH paid AS (
    SELECT payer_member_id AS member_id,
           SUM(amount_cents) AS paid_total
    FROM expenses
    WHERE group_id = $1 AND deleted_at IS NULL
    GROUP BY payer_member_id
),
owed AS (
    SELECT es.member_id,
           SUM(es.amount_cents) AS owed_total
    FROM expense_splits es
    JOIN expenses e ON e.id = es.expense_id
    WHERE e.group_id = $1 AND e.deleted_at IS NULL
    GROUP BY es.member_id
),
settled_paid AS (
    SELECT payer_member_id AS member_id,
           SUM(amount_cents) AS settled_out
    FROM settlements
    WHERE group_id = $1 AND deleted_at IS NULL
    GROUP BY payer_member_id
),
settled_received AS (
    SELECT payee_member_id AS member_id,
           SUM(amount_cents) AS settled_in
    FROM settlements
    WHERE group_id = $1 AND deleted_at IS NULL
    GROUP BY payee_member_id
)
SELECT
    m.id AS member_id,
    m.display_name,
    COALESCE(p.paid_total, 0) AS paid_total_cents,
    COALESCE(o.owed_total, 0) AS owed_total_cents,
    COALESCE(sp.settled_out, 0) AS settled_out_cents,
    COALESCE(sr.settled_in, 0) AS settled_in_cents,
    COALESCE(p.paid_total, 0)
      - COALESCE(o.owed_total, 0)
      + COALESCE(sp.settled_out, 0)
      - COALESCE(sr.settled_in, 0) AS net_cents
FROM members m
LEFT JOIN paid            p  ON p.member_id  = m.id
LEFT JOIN owed            o  ON o.member_id  = m.id
LEFT JOIN settled_paid   sp  ON sp.member_id = m.id
LEFT JOIN settled_received sr ON sr.member_id = m.id
WHERE m.group_id = $1
ORDER BY net_cents DESC;
```

Expected EXPLAIN ANALYZE (group with 10 members, 100 expenses, 10 settlements):
```
Hash Join  (cost=48.20..62.50 rows=10)
  Hash Cond: (m.id = p.member_id)
  ->  Index Scan using idx_members_group_id on members  (cost=0.14..8.17 rows=10)
        Index Cond: (group_id = $1)
  ->  Hash  (cost=40.00..40.00)
        ->  Aggregate  (cost=20.00..40.00 rows=10)
              ->  Bitmap Heap Scan on expenses  (cost=0.28..15.00 rows=100)
                    Recheck Cond: ((group_id = $1) AND (deleted_at IS NULL))
                    ->  Bitmap Index Scan on idx_expenses_group_id_not_deleted
Hash Left Join (expense_splits via idx_expense_splits_member_id)
Hash Left Join (settlements via idx_settlements_group_id_active)
Planning Time: ~1ms
Execution Time: ~3-5ms (for 100 expenses, 10 members, 10 settlements)
```

### Query 2: Expense list (paginated)

Called on: `GET /api/v1/groups/{id}/expenses?page=1&per_page=20`
Polling: yes (SWR refreshInterval).

```sql
SELECT e.id, e.description, e.amount_cents, e.currency, e.split_type,
       e.expense_date, e.created_at,
       m_payer.display_name AS payer_name,
       m_logger.display_name AS logged_by_name,
       COUNT(es.id) AS split_count
FROM expenses e
JOIN members m_payer  ON m_payer.id  = e.payer_member_id
JOIN members m_logger ON m_logger.id = e.logged_by_member_id
JOIN expense_splits es ON es.expense_id = e.id
WHERE e.group_id = $1 AND e.deleted_at IS NULL
GROUP BY e.id, m_payer.display_name, m_logger.display_name
ORDER BY e.created_at DESC
LIMIT 20 OFFSET 0;
```

Expected execution plan:
```
Index Scan using idx_expenses_group_id_active on expenses
  Index Cond: (group_id = $1) [partial: deleted_at IS NULL]
  ->  Nested Loop on members (PK lookup for payer)
  ->  Nested Loop on members (PK lookup for logger)
  ->  Hash Aggregate on expense_splits (idx_expense_splits_expense_id)
Execution Time: ~8-12ms (200 expenses, 20 returned)
```

### Query 3: Expense detail with split breakdown

Called on: `GET /api/v1/groups/{id}/expenses/{expense_id}`

```sql
SELECT e.*, m_payer.id, m_payer.display_name, m_logger.display_name,
       es.member_id, m_split.display_name, es.amount_cents, es.percentage
FROM expenses e
JOIN members m_payer   ON m_payer.id   = e.payer_member_id
JOIN members m_logger  ON m_logger.id  = e.logged_by_member_id
JOIN expense_splits es ON es.expense_id = e.id
JOIN members m_split   ON m_split.id    = es.member_id
WHERE e.id = $1 AND e.deleted_at IS NULL;
```

Expected execution plan:
```
Index Scan using expenses_pkey on expenses  (cost=0.14..8.17 rows=1)
  Filter: (deleted_at IS NULL)
  ->  Nested Loop (PK scan on members for payer)
  ->  Nested Loop (PK scan on members for logger)
  ->  Index Scan on idx_expense_splits_expense_id
      ->  Nested Loop (PK scan on members for each split member)
Execution Time: <2ms
```

### Query 4: Idempotency key lookup

Called on: every mutation endpoint (POST /groups, POST /expenses, POST /settlements)

```sql
SELECT response_body, status_code
FROM idempotency_keys
WHERE key = $1 AND expires_at > NOW();
```

Expected execution plan:
```
Index Scan using idempotency_keys_pkey on idempotency_keys  (cost=0.14..8.17 rows=1)
  Index Cond: (key = $1)
  Filter: (expires_at > now())
Execution Time: <1ms
```

Note: The PK lookup on `key` (UUID) is the primary lookup. The `expires_at`
filter is applied as a post-scan filter since the PK scan returns at most 1 row.

### Query 5: Settlement list with member names

Called on: `GET /api/v1/groups/{id}/settlements`

```sql
SELECT s.id, s.payer_member_id, s.payee_member_id, s.amount_cents, s.currency,
       s.created_at,
       m_payer.display_name AS payer_name,
       m_payee.display_name AS payee_name
FROM settlements s
JOIN members m_payer ON m_payer.id = s.payer_member_id
JOIN members m_payee ON m_payee.id = s.payee_member_id
WHERE s.group_id = $1 AND s.deleted_at IS NULL
ORDER BY s.created_at DESC
LIMIT 20 OFFSET 0;
```

Expected execution plan:
```
Bitmap Heap Scan on settlements  (idx_settlements_group_id_active)
  Recheck Cond: ((group_id = $1) AND (deleted_at IS NULL))
  ->  Nested Loop on members (PK lookup for payer)
  ->  Nested Loop on members (PK lookup for payee)
  ->  Sort on created_at DESC (in-memory for typical group sizes)
Execution Time: <3ms
```

---

## Money Storage Policy

All monetary values are stored as `INTEGER` (cents). This is non-negotiable.

| Value | Stored as |
|---|---|
| $42.00 | `4200` |
| $840.00 | `84000` |
| $0.01 | `1` |
| $999,999.99 | `99999999` |

Rationale: IEEE 754 floating-point arithmetic accumulates rounding errors that
compound over expense history. A $10.00 / 3 split stored as FLOAT produces
`3.3333333...` — not `3.33`. Stored as INTEGER cents: `1000 / 3 = 333` with
1-cent remainder assigned to the first member alphabetically. Totals always
add up exactly.

NUMERIC(6,3) is used ONLY for `expense_splits.percentage` — this is a display
field only. The `amount_cents` column is authoritative for all computations.

---

## Soft Delete Pattern

`expenses.deleted_at` and `settlements.deleted_at` are nullable TIMESTAMPTZ
columns. `NULL` means the record is active. A non-null timestamp means the
record was soft-deleted at that time.

**Why soft delete instead of hard delete:**
- Maintains audit trail for expense history
- Allows balance recalculation to remain accurate after deletion
- Settlements can be "reversed" without data loss
- Partial indexes (`WHERE deleted_at IS NULL`) ensure deleted records have zero
  query performance impact on active-data queries

**Cleanup:** Soft-deleted records are never hard-deleted in MVP. A future
archival job can move old deleted records to a history table if storage becomes
a concern.

---

## Trigger: `set_updated_at()`

A single PL/pgSQL trigger function is applied to all 5 entity tables as a
`BEFORE UPDATE` trigger. This ensures `updated_at` is always correct without
requiring the application layer to remember to set it.

```sql
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

Applied to: `groups`, `members`, `expenses`, `expense_splits`, `settlements`.
Not applied to `idempotency_keys` — idempotency records are immutable after
insertion (no UPDATE operations are expected).

---

## Migration Strategy

All schema changes follow the expand-contract pattern for zero-downtime
deployments:

1. **Expand:** Add new column as nullable. Deploy new app version.
2. **Migrate:** Backfill existing rows in a background job.
3. **Contract:** Add NOT NULL constraint (if needed). Drop compatibility shim.

Never `DROP COLUMN` in the same migration that removes the column from
application code. Drop columns only after verifying no running instance reads
them.

The `alembic upgrade head` command runs before the API server starts (handled
by the `migrate` service in docker-compose and the CD pipeline).
