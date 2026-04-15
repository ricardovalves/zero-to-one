"""initial schema

Creates all 6 FairSplit tables, indexes, and the set_updated_at() trigger.

Migration order follows FK dependency:
  groups → members → expenses → expense_splits → settlements → idempotency_keys
  → set_updated_at() trigger function → apply triggers to 5 entity tables

All monetary amounts are stored as INTEGER cents. FLOAT and NUMERIC are never
used for monetary values; NUMERIC(6,3) is used only for display-only percentage
storage in expense_splits.

Revision ID: 0001
Revises: (none — this is the initial migration)
Create Date: 2026-04-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enable pgcrypto for gen_random_uuid()
    # ------------------------------------------------------------------
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ------------------------------------------------------------------
    # Table: groups
    # ------------------------------------------------------------------
    # Root entity. Has no foreign key dependencies.
    # invite_token is a separate UUID from the PK so it can be regenerated
    # by an admin without changing the group's identity URL.
    op.execute("""
        CREATE TABLE groups (
            id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            name             VARCHAR(80)  NOT NULL CHECK (length(trim(name)) > 0),
            description      VARCHAR(200),
            invite_token     UUID         NOT NULL DEFAULT gen_random_uuid() UNIQUE,
            status           VARCHAR(20)  NOT NULL DEFAULT 'active'
                             CHECK (status IN ('active', 'archived')),
            default_currency CHAR(3)      NOT NULL DEFAULT 'USD',
            created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """)

    # Unique index on invite_token — used on every join flow.
    # Marked UNIQUE in the column definition but we also create the explicit
    # named index so we can reference it precisely in EXPLAIN ANALYZE output.
    op.execute("""
        CREATE UNIQUE INDEX idx_groups_invite_token
            ON groups (invite_token)
    """)

    # ------------------------------------------------------------------
    # Table: members
    # ------------------------------------------------------------------
    # FK → groups.id. ON DELETE CASCADE: removing a group removes all members.
    # is_admin defaults FALSE — only the group creator is promoted to TRUE at
    # join time inside the application layer.
    op.execute("""
        CREATE TABLE members (
            id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            group_id     UUID        NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
            display_name VARCHAR(40) NOT NULL CHECK (length(trim(display_name)) > 0),
            is_admin     BOOLEAN     NOT NULL DEFAULT FALSE,
            joined_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    # Non-unique index on group_id — scans all members for a group on every
    # dashboard load and balance computation.
    op.execute("""
        CREATE INDEX idx_members_group_id
            ON members (group_id)
    """)

    # ------------------------------------------------------------------
    # Table: expenses
    # ------------------------------------------------------------------
    # FK → groups.id (cascade), payer_member_id → members.id (restrict),
    # logged_by_member_id → members.id (restrict).
    # RESTRICT on member FKs: prevents deleting a member who has expenses,
    # which would corrupt the expense history. Use soft-delete on members
    # instead if member removal is ever needed.
    # deleted_at is the soft-delete sentinel (NULL = active).
    op.execute("""
        CREATE TABLE expenses (
            id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            group_id            UUID         NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
            payer_member_id     UUID         NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
            logged_by_member_id UUID         NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
            description         VARCHAR(200) NOT NULL CHECK (length(trim(description)) > 0),
            amount_cents        INTEGER      NOT NULL CHECK (amount_cents > 0),
            currency            CHAR(3)      NOT NULL DEFAULT 'USD',
            split_type          VARCHAR(20)  NOT NULL
                                CHECK (split_type IN ('equal', 'custom_amount', 'custom_percentage')),
            expense_date        DATE         NOT NULL DEFAULT CURRENT_DATE,
            deleted_at          TIMESTAMPTZ,
            created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW()
        )
    """)

    # Composite partial index: the primary read path.
    # Covers: WHERE group_id = $1 AND deleted_at IS NULL ORDER BY created_at DESC.
    # Column order — group_id (equality filter) first, created_at DESC (sort) second.
    # The WHERE clause filters out soft-deleted rows before the index is even
    # examined, making this index both smaller and faster than a full index.
    op.execute("""
        CREATE INDEX idx_expenses_group_id_active
            ON expenses (group_id, created_at DESC)
            WHERE deleted_at IS NULL
    """)

    # Partial index for balance CTE: GROUP BY payer_member_id on active expenses.
    # No ORDER BY needed for the aggregation, so omitting created_at reduces
    # index size and write amplification.
    op.execute("""
        CREATE INDEX idx_expenses_group_id_not_deleted
            ON expenses (group_id)
            WHERE deleted_at IS NULL
    """)

    # Index for permission check: "did this member log this expense?"
    # Used in PATCH /expenses/{id} and DELETE /expenses/{id} before applying
    # the mutation.
    op.execute("""
        CREATE INDEX idx_expenses_logged_by
            ON expenses (logged_by_member_id)
    """)

    # ------------------------------------------------------------------
    # Table: expense_splits
    # ------------------------------------------------------------------
    # FK → expenses.id (cascade), member_id → members.id (restrict).
    # CASCADE on expense FK: deleting an expense (hard) removes its splits.
    # Soft-deletes on expenses set deleted_at; the splits row is kept for
    # historical accuracy and re-activation support.
    # UNIQUE (expense_id, member_id): a member can only appear once per expense.
    # amount_cents CHECK >= 0: allows 0 for record-keeping edge cases
    # (e.g., a member is listed but owes nothing this round).
    # percentage NUMERIC(6,3): stored for display only; amount_cents is
    # authoritative for all financial computations.
    op.execute("""
        CREATE TABLE expense_splits (
            id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
            expense_id   UUID         NOT NULL REFERENCES expenses(id) ON DELETE CASCADE,
            member_id    UUID         NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
            amount_cents INTEGER      NOT NULL CHECK (amount_cents >= 0),
            percentage   NUMERIC(6,3),
            created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            UNIQUE (expense_id, member_id)
        )
    """)

    # Index on expense_id: the JOIN path from expenses → expense_splits.
    # Used in every detail view and in the balance CTE inner join.
    op.execute("""
        CREATE INDEX idx_expense_splits_expense_id
            ON expense_splits (expense_id)
    """)

    # Index on member_id: the balance CTE aggregates splits by member.
    # SELECT member_id, SUM(amount_cents) ... GROUP BY member_id.
    op.execute("""
        CREATE INDEX idx_expense_splits_member_id
            ON expense_splits (member_id)
    """)

    # ------------------------------------------------------------------
    # Table: settlements
    # ------------------------------------------------------------------
    # FK → groups.id (cascade), payer_member_id → members.id (restrict),
    # payee_member_id → members.id (restrict).
    # CHECK (payer_member_id != payee_member_id): prevents self-settlements
    # at the database level — these would produce no balance change and
    # confuse the settle-up algorithm.
    # deleted_at soft-delete: settlements can be reversed (the payer or admin
    # can undo a settlement to restore the original balances).
    op.execute("""
        CREATE TABLE settlements (
            id               UUID     PRIMARY KEY DEFAULT gen_random_uuid(),
            group_id         UUID     NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
            payer_member_id  UUID     NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
            payee_member_id  UUID     NOT NULL REFERENCES members(id) ON DELETE RESTRICT,
            amount_cents     INTEGER  NOT NULL CHECK (amount_cents > 0),
            currency         CHAR(3)  NOT NULL DEFAULT 'USD',
            deleted_at       TIMESTAMPTZ,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CHECK (payer_member_id != payee_member_id)
        )
    """)

    # Partial index on group_id: balance CTE queries active settlements by
    # group. WHERE deleted_at IS NULL excludes reversed settlements.
    op.execute("""
        CREATE INDEX idx_settlements_group_id_active
            ON settlements (group_id)
            WHERE deleted_at IS NULL
    """)

    # ------------------------------------------------------------------
    # Table: idempotency_keys
    # ------------------------------------------------------------------
    # Standalone table — no FK dependencies. The PK is the client-supplied
    # UUID key itself (not a surrogate). expires_at is set to NOW() + 24h
    # on insert; a periodic cleanup job or startup task removes expired rows
    # via DELETE FROM idempotency_keys WHERE expires_at < NOW().
    # response_body is JSONB: efficient storage and allows the server to
    # return the exact original response on a duplicate request.
    op.execute("""
        CREATE TABLE idempotency_keys (
            key            UUID         PRIMARY KEY,
            endpoint       VARCHAR(100) NOT NULL,
            response_body  JSONB        NOT NULL,
            status_code    SMALLINT     NOT NULL,
            created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            expires_at     TIMESTAMPTZ  NOT NULL DEFAULT (NOW() + INTERVAL '24 hours')
        )
    """)

    # Index on expires_at for efficient cleanup queries.
    # NOTE: WHERE expires_at > NOW() is invalid in PostgreSQL — NOW() is VOLATILE
    # and index predicates require IMMUTABLE functions. A plain index is sufficient;
    # the planner uses it for the periodic DELETE WHERE expires_at < NOW() cleanup.
    op.execute("""
        CREATE INDEX idx_idempotency_keys_expires
            ON idempotency_keys (expires_at)
    """)

    # ------------------------------------------------------------------
    # Trigger function: set_updated_at()
    # ------------------------------------------------------------------
    # Applied as a BEFORE UPDATE trigger on all 5 entity tables.
    # Ensures updated_at always reflects the last modification time
    # without requiring the application layer to remember to set it.
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)

    # Apply trigger to groups
    op.execute("""
        CREATE TRIGGER set_groups_updated_at
            BEFORE UPDATE ON groups
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # Apply trigger to members
    op.execute("""
        CREATE TRIGGER set_members_updated_at
            BEFORE UPDATE ON members
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # Apply trigger to expenses
    op.execute("""
        CREATE TRIGGER set_expenses_updated_at
            BEFORE UPDATE ON expenses
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # Apply trigger to expense_splits
    op.execute("""
        CREATE TRIGGER set_expense_splits_updated_at
            BEFORE UPDATE ON expense_splits
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)

    # Apply trigger to settlements
    op.execute("""
        CREATE TRIGGER set_settlements_updated_at
            BEFORE UPDATE ON settlements
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)


def downgrade() -> None:
    # Drop in reverse dependency order: triggers first, then tables that have
    # foreign key dependencies, then the extension last.

    # Drop triggers before dropping the function they reference
    op.execute("DROP TRIGGER IF EXISTS set_settlements_updated_at ON settlements")
    op.execute("DROP TRIGGER IF EXISTS set_expense_splits_updated_at ON expense_splits")
    op.execute("DROP TRIGGER IF EXISTS set_expenses_updated_at ON expenses")
    op.execute("DROP TRIGGER IF EXISTS set_members_updated_at ON members")
    op.execute("DROP TRIGGER IF EXISTS set_groups_updated_at ON groups")

    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")

    # Drop tables in reverse FK dependency order
    op.execute("DROP TABLE IF EXISTS idempotency_keys")
    op.execute("DROP TABLE IF EXISTS settlements")
    op.execute("DROP TABLE IF EXISTS expense_splits")
    op.execute("DROP TABLE IF EXISTS expenses")
    op.execute("DROP TABLE IF EXISTS members")
    op.execute("DROP TABLE IF EXISTS groups")

    # Drop the extension last — only if no other objects depend on it
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
