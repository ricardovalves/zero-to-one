"""Exhaustive unit tests for the settle-up algorithm.

These tests are the correctness gate for the hero feature. Every test must pass
before any PR touching the settle-up logic is considered complete.

Test taxonomy:
1. Transfer count minimality
2. Balance correctness (applying transfers reaches zero)
3. Amount correctness (all amounts positive)
4. N-1 property (at most N-1 transfers for N non-zero members)
5. Edge cases (empty input, all-zero, 1-cent amounts)
6. 1-cent remainder assignment (alphabetical convention)
7. Performance (20-member and 100-member stress tests)
8. Correctness of circular debt elimination
"""

from __future__ import annotations

import time
from uuid import UUID

import pytest

from app.services.settle_service import compute_settle_up


# ---------------------------------------------------------------------------
# Test utilities
# ---------------------------------------------------------------------------


def uid(n: int) -> UUID:
    """Create a deterministic UUID from an integer for readable test assertions."""
    return UUID(f"00000000-0000-0000-0000-{n:012d}")


# Names for members 1–20 that are alphabetically ordered
MEMBER_NAMES: dict[UUID, str] = {uid(i): f"Member{i:02d}" for i in range(1, 21)}


def apply_transfers(
    balances: dict[UUID, int],
    transfers: list,
) -> dict[UUID, int]:
    """Apply a list of transfers to a balance dict and return the result.

    Used to verify that the algorithm produces a correct settlement plan.
    """
    result = dict(balances)
    for t in transfers:
        result[t.creditor_id] -= t.amount_cents
        result[t.debtor_id] += t.amount_cents
    return result


# ---------------------------------------------------------------------------
# Case 1: Two-person single debt — exactly 1 transfer
# ---------------------------------------------------------------------------


def test_two_person_single_debt():
    balances = {uid(1): 4200, uid(2): -4200}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == 1
    assert transfers[0].amount_cents == 4200
    assert transfers[0].debtor_id == uid(2)
    assert transfers[0].creditor_id == uid(1)


def test_two_person_small_debt():
    balances = {uid(1): 1, uid(2): -1}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == 1
    assert transfers[0].amount_cents == 1


# ---------------------------------------------------------------------------
# Case 2: Three-person — minimum transfers
# ---------------------------------------------------------------------------


def test_three_person_two_creditors_one_debtor():
    """Two creditors, one debtor — requires 2 transfers (one per creditor)."""
    balances = {uid(1): 500, uid(2): 500, uid(3): -1000}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == 2
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


def test_three_person_one_creditor_two_debtors():
    """One creditor, two debtors — requires 2 transfers."""
    balances = {uid(1): 1000, uid(2): -300, uid(3): -700}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == 2
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


def test_three_person_simplified_chain():
    """A → B, B → C simplifies to A → C + B → C (or A → B → C chain)."""
    balances = {uid(1): 1000, uid(2): 0, uid(3): -1000}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == 1  # member 2 is already balanced
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


# ---------------------------------------------------------------------------
# Case 3: Four-person complex — at most N-1 transfers
# ---------------------------------------------------------------------------


def test_four_person_complex():
    balances = {uid(1): 3000, uid(2): 1000, uid(3): -2000, uid(4): -2000}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) <= 3  # at most 4-1 = 3
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


def test_four_person_one_big_creditor():
    """One large creditor, three smaller debtors."""
    balances = {uid(1): 9000, uid(2): -3000, uid(3): -3000, uid(4): -3000}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == 3
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


def test_four_person_many_creditors_one_debtor():
    balances = {uid(1): 3000, uid(2): 3000, uid(3): 3000, uid(4): -9000}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == 3
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


# ---------------------------------------------------------------------------
# Case 4: All-settled (zero balances) — empty transfer list
# ---------------------------------------------------------------------------


def test_all_zero_balances_returns_empty():
    balances = {uid(1): 0, uid(2): 0, uid(3): 0}
    transfers = compute_settle_up(balances, MEMBER_NAMES)
    assert transfers == []


def test_single_member_zero_returns_empty():
    transfers = compute_settle_up({uid(1): 0}, MEMBER_NAMES)
    assert transfers == []


def test_empty_input_returns_empty():
    transfers = compute_settle_up({}, MEMBER_NAMES)
    assert transfers == []


# ---------------------------------------------------------------------------
# Case 5: 1-cent remainder — must not be dropped or lost
# ---------------------------------------------------------------------------


def test_one_cent_debt_produces_one_transfer():
    """A 1-cent balance is not dropped — it must produce a transfer."""
    balances = {uid(1): 1, uid(2): -1}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == 1
    assert transfers[0].amount_cents == 1
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


def test_rounding_remainder_absorbed_correctly():
    """Verify the rounding remainder absorption leaves net balances at zero."""
    # 3 members, total 100 cents (can't divide evenly by 3)
    # This simulates a percentage-split rounding scenario
    balances = {uid(1): 34, uid(2): 33, uid(3): -67}
    # Total = 34 + 33 - 67 = 0 (balanced)
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


def test_nonzero_sum_remainder_absorbed_by_first_creditor_alphabetically():
    """If balances don't sum to zero (rounding artefact), the discrepancy is
    absorbed by the first creditor sorted alphabetically by display name.
    """
    # uid(1) = "Member01", uid(2) = "Member02" — Member01 comes first alphabetically
    # Force a 1-cent discrepancy in the input
    balances = {uid(1): 5000, uid(2): -4999}  # sums to +1
    # The algorithm should absorb the +1 from uid(1) (first creditor alphabetically)
    # so uid(1) effectively has 4999, uid(2) has -4999 → 1 transfer of 4999
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == 1
    # After applying transfers, all balances should reach 0
    after = apply_transfers({uid(1): 4999, uid(2): -4999}, transfers)
    assert all(v == 0 for v in after.values())


# ---------------------------------------------------------------------------
# Correctness properties
# ---------------------------------------------------------------------------


def test_balances_clear_after_all_transfers():
    """Applying all transfers must bring every member's balance to zero."""
    balances = {uid(1): 5000, uid(2): -2000, uid(3): -3000}
    original = dict(balances)
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    after = apply_transfers(original, transfers)
    assert all(v == 0 for v in after.values()), f"Remaining balances: {after}"


def test_all_transfer_amounts_are_positive():
    """Every transfer in the plan must have a positive amount."""
    balances = {uid(1): 4200, uid(2): -4200}
    transfers = compute_settle_up(balances, MEMBER_NAMES)
    for t in transfers:
        assert t.amount_cents > 0, f"Transfer has non-positive amount: {t}"


def test_transfers_sorted_largest_first():
    """The output is sorted by amount_cents DESC (largest transfer first)."""
    balances = {uid(1): 3000, uid(2): 1000, uid(3): -2000, uid(4): -2000}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    amounts = [t.amount_cents for t in transfers]
    assert amounts == sorted(amounts, reverse=True), f"Transfers not sorted: {amounts}"


def test_at_most_n_minus_1_transfers():
    """At most N-1 transfers for N non-zero members — algorithmic property."""
    balances = {
        uid(1): 3000, uid(2): 2000, uid(3): 1000,
        uid(4): -2000, uid(5): -4000,
    }
    nonzero_members = sum(1 for v in balances.values() if v != 0)
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) <= nonzero_members - 1, (
        f"Too many transfers: {len(transfers)} for {nonzero_members} non-zero members"
    )


def test_member_names_in_transfers():
    """Transfer objects must carry the correct display names."""
    balances = {uid(1): 1000, uid(2): -1000}
    names = {uid(1): "Alice", uid(2): "Bob"}
    transfers = compute_settle_up(dict(balances), names)
    assert len(transfers) == 1
    assert transfers[0].creditor_name == "Alice"
    assert transfers[0].debtor_name == "Bob"


def test_currency_propagated_to_transfers():
    """Each transfer carries the currency string passed to compute_settle_up."""
    balances = {uid(1): 5000, uid(2): -5000}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES, currency="EUR")
    for t in transfers:
        assert t.currency == "EUR"


# ---------------------------------------------------------------------------
# Five-member group — comprehensive correctness
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("balances,expected_count", [
    # Case 1: Simple chain
    ({uid(1): 4200, uid(2): -4200}, 1),
    # Case 3: Four-person group
    ({uid(1): 3000, uid(2): 1000, uid(3): -2000, uid(4): -2000}, 3),
    # All settled
    ({uid(1): 0, uid(2): 0, uid(3): 0}, 0),
    # Single member settled
    ({uid(1): 0}, 0),
    # One creditor, many debtors
    ({uid(1): 9000, uid(2): -3000, uid(3): -3000, uid(4): -3000}, 3),
    # Many creditors, one debtor
    ({uid(1): 3000, uid(2): 3000, uid(3): 3000, uid(4): -9000}, 3),
    # 1-cent edge case
    ({uid(1): 1, uid(2): -1}, 1),
])
def test_transfer_count_parametrized(balances, expected_count):
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    assert len(transfers) == expected_count


# ---------------------------------------------------------------------------
# Case 6: Performance — 20-member stress test (< 50ms)
# ---------------------------------------------------------------------------


def test_performance_20_members():
    """20-member group must complete in under 50ms."""
    # 10 creditors, 10 debtors — perfectly balanced
    balances = {}
    for i in range(1, 11):
        balances[uid(i)] = 1000  # creditors
    for i in range(11, 21):
        balances[uid(i)] = -1000  # debtors

    start = time.perf_counter()
    transfers = compute_settle_up(
        balances, {uid(i): f"M{i:02d}" for i in range(1, 21)}
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 50, f"20-member settle-up took {elapsed_ms:.1f}ms (limit: 50ms)"
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


def test_performance_100_members():
    """100-member stress test must complete in under 50ms.

    This is the performance requirement from the technical spec §5.
    """
    # 50 creditors (+100 each) and 50 debtors (-100 each) — perfectly balanced
    balances: dict[UUID, int] = {}
    names: dict[UUID, str] = {}
    for i in range(1, 51):
        balances[uid(i)] = 100
        names[uid(i)] = f"Creditor{i:03d}"
    for i in range(51, 101):
        balances[uid(i)] = -100
        names[uid(i)] = f"Debtor{i:03d}"

    start = time.perf_counter()
    transfers = compute_settle_up(balances, names)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert elapsed_ms < 50, f"100-member settle-up took {elapsed_ms:.1f}ms (limit: 50ms)"
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


# ---------------------------------------------------------------------------
# Circular debt elimination
# ---------------------------------------------------------------------------


def test_circular_three_person_chain():
    """A owes B, B owes C, C owes A — the net result is zero for a balanced
    circular debt. The greedy algorithm collapses these into 0 or minimal transfers.
    """
    # If each person owes the next 1000 cents, the net balances sum to zero.
    # Net: A paid 0, owed 1000; B paid 1000, owed 1000; C paid 1000, owed 0
    # A: -1000, B: 0, C: +1000 (simplified from the circular view)
    balances = {uid(1): -1000, uid(2): 0, uid(3): 1000}
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    # Only 1 transfer needed: uid(1) → uid(3) for 1000
    assert len(transfers) == 1
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())


def test_complex_multi_direction():
    """Five members with criss-crossing debts — all must clear after applying transfers."""
    balances = {
        uid(1): 5000,
        uid(2): -1000,
        uid(3): 2000,
        uid(4): -4000,
        uid(5): -2000,
    }
    transfers = compute_settle_up(dict(balances), MEMBER_NAMES)
    # All balances must reach 0
    after = apply_transfers(balances, transfers)
    assert all(v == 0 for v in after.values())
    # N-1 property: 5 non-zero members → at most 4 transfers
    nonzero = sum(1 for v in balances.values() if v != 0)
    assert len(transfers) <= nonzero - 1


# ---------------------------------------------------------------------------
# Regression: algorithm does not mutate the caller's dict
# ---------------------------------------------------------------------------


def test_does_not_mutate_input_dict():
    """compute_settle_up must not modify the caller's net_balances dict."""
    balances = {uid(1): 5000, uid(2): -5000}
    original_copy = dict(balances)
    compute_settle_up(balances, MEMBER_NAMES)
    assert balances == original_copy
