# DB Engineer Handoff — FairSplit

**Date:** 2026-04-15
**Authored by:** DB Engineer Agent

---

## Key Decisions

1. **Single Base in `app/database.py`** — The canonical `DeclarativeBase` lives in `app/database.py`. All individual model files in `app/models/` import from there. `app/models.py` is a re-export shim only. `env.py` imports `Base` from `app.database` and explicitly imports all 6 model classes to ensure their tables register against `Base.metadata` before Alembic accesses it.

2. **Alembic migration uses raw SQL via `op.execute()`** — The initial migration (`0001_initial_schema.py`) issues all DDL as raw SQL strings rather than `op.create_table()`. This is intentional: partial index predicates with `WHERE deleted_at IS NULL` and `WHERE expires_at > NOW()` are PostgreSQL-specific expressions that do not translate cleanly through SQLAlchemy's dialect-agnostic `CreateIndex`. Raw SQL is the only safe approach for partial indexes with server-evaluated predicates.

3. **All 5 critical indexes implemented exactly as specified** — `idx_expenses_group_id_active` (partial composite), `idx_expenses_group_id_not_deleted` (partial simple), `idx_settlements_group_id_active` (partial), `idx_groups_invite_token` (unique), `idx_members_group_id` (non-unique). Indexes are defined in both the migration (creates them in PostgreSQL) and the ORM model `__table_args__` (registers them in SQLAlchemy metadata for autogenerate).

4. **Money is INTEGER cents everywhere** — `amount_cents: INTEGER`. `percentage: NUMERIC(6,3)` is the only Numeric type in the schema, and it is display-only. This is enforced by CHECK constraints and ORM column types.

5. **Soft delete via `deleted_at TIMESTAMPTZ` nullable** — On `expenses` and `settlements` only. Partial indexes exclude soft-deleted rows from the active-data query paths. Hard delete is never used on these tables.

6. **Trigger `set_updated_at()` applied to 5 entity tables** — Defined in the migration and applied before any data insert. Not applied to `idempotency_keys` (immutable after INSERT).

7. **`check_db_connection()` added to `app/database.py`** — Used by `GET /api/v1/health`. Returns `True` if `SELECT 1` succeeds, `False` on any exception.

8. **Seed script is display-name-only** — FairSplit has no user accounts, no emails, no passwords. The seed script creates groups and members directly via raw SQL inserts and prints invite token join links for developer access. No bcrypt or hashing of any kind.

9. **Idempotent seed** — Checks for `groups.name = 'Nashville Trip 2026'` before any insert. Safe to re-run.

10. **`SCHEMA.md` documents index rationale and 5 critical query execution plans** — Located at `src/backend/SCHEMA.md`.

---

## Files Written / Modified

| File | Action | Notes |
|---|---|---|
| `src/backend/alembic.ini` | Created | `script_location = migrations`, no hardcoded DB URL |
| `src/backend/migrations/env.py` | Created | Async pattern, imports Base from `app.database`, imports all 6 models |
| `src/backend/migrations/script.py.mako` | Created | Standard Alembic template |
| `src/backend/migrations/versions/0001_initial_schema.py` | Created | All 6 tables + 9 indexes + trigger function + 5 trigger attachments, reversible |
| `src/backend/app/models.py` | Replaced | Now a re-export shim only — no model definitions |
| `src/backend/app/models/group.py` | Modified | Added `idx_groups_invite_token` to `__table_args__` |
| `src/backend/app/models/member.py` | Modified | Added `idx_members_group_id` to `__table_args__` |
| `src/backend/app/models/expense.py` | Modified | Added 3 indexes (group_id_active, group_id_not_deleted, logged_by) |
| `src/backend/app/models/expense_split.py` | Modified | Added 2 indexes (expense_id, member_id) |
| `src/backend/app/models/settlement.py` | Modified | Added partial index `idx_settlements_group_id_active` |
| `src/backend/app/models/idempotency_key.py` | Modified | Added partial index, fixed `expires_at` server_default |
| `src/backend/app/database.py` | Modified | Added `check_db_connection()` helper |
| `src/backend/seed.py` | Created | 2 groups, 8 members, 14 expenses (all 3 split types), 3 settlements |
| `src/backend/SCHEMA.md` | Created | ERD, index rationale, 5 query EXPLAIN ANALYZE plans |
