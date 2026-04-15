"""FairSplit backend smoke test.

Verifies that the running backend is functional end-to-end:
1. Waits for the backend to become healthy (GET /health).
2. Creates a new group as the admin.
3. Joins the group as a second member.
4. Logs an expense with an equal split.
5. Fetches the balance list.
6. Fetches the settle-up plan.
7. Asserts all responses are 200/201 and the settle-up returns >= 1 transfer.

Exit codes:
  0 — all assertions passed
  1 — any assertion failed or the backend did not become healthy in time

Usage:
    python smoke_test.py                         # uses http://localhost:8000
    BACKEND_URL=http://backend:8000 python smoke_test.py  # inside docker network
"""

from __future__ import annotations

import json
import os
import sys
import time
import uuid
from datetime import date

# Use urllib instead of httpx so this script has zero extra dependencies
import urllib.error
import urllib.request


BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
MAX_WAIT_SECONDS = 60
HEALTH_INTERVAL = 2


def request(
    method: str,
    path: str,
    body: dict | None = None,
    headers: dict | None = None,
) -> tuple[int, dict]:
    """Make an HTTP request and return (status_code, parsed_body)."""
    url = f"{BACKEND_URL}{path}"
    data = json.dumps(body).encode() if body else None
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def wait_for_health() -> None:
    """Poll GET /health until the backend is healthy or timeout is reached."""
    start = time.monotonic()
    print(f"[smoke] Waiting for backend at {BACKEND_URL}/health ...")
    while True:
        elapsed = time.monotonic() - start
        if elapsed > MAX_WAIT_SECONDS:
            print(f"[smoke] FAILED: backend did not become healthy after {MAX_WAIT_SECONDS}s")
            sys.exit(1)

        try:
            status, body = request("GET", "/health")
            if status == 200 and body.get("status") == "healthy":
                print(f"[smoke] Backend healthy after {elapsed:.1f}s")
                return
        except Exception as exc:
            pass  # Connection refused — backend not up yet

        time.sleep(HEALTH_INTERVAL)


def assert_status(actual: int, expected: int, context: str) -> None:
    if actual != expected:
        print(f"[smoke] FAILED [{context}]: expected {expected}, got {actual}")
        sys.exit(1)


def run_smoke_test() -> None:
    wait_for_health()

    idem_key_group = str(uuid.uuid4())
    idem_key_expense = str(uuid.uuid4())

    # -------------------------------------------------------------------------
    # Step 1: Create a group as admin (Maya)
    # -------------------------------------------------------------------------
    print("[smoke] Creating group ...")
    status, body = request(
        "POST",
        "/api/v1/groups",
        body={
            "name": "Smoke Test Trip",
            "admin_display_name": "Maya",
            "default_currency": "USD",
        },
        headers={"X-Idempotency-Key": idem_key_group},
    )
    assert_status(status, 201, "POST /groups")

    group_id = body["group"]["id"]
    admin_token = body["token"]
    admin_member_id = body["member"]["id"]
    print(f"[smoke]   group_id={group_id}")
    print(f"[smoke]   admin_member_id={admin_member_id}")

    invite_token = body["group"]["invite_token"]

    # -------------------------------------------------------------------------
    # Step 2: Join the group as a second member (Daniel)
    # -------------------------------------------------------------------------
    print("[smoke] Joining group as Daniel ...")
    status, join_body = request(
        "POST",
        f"/api/v1/join/{invite_token}",
        body={"display_name": "Daniel"},
        headers={"X-Idempotency-Key": str(uuid.uuid4())},
    )
    assert_status(status, 201, f"POST /join/{invite_token}")

    daniel_token = join_body["token"]
    daniel_member_id = join_body["member"]["id"]
    print(f"[smoke]   daniel_member_id={daniel_member_id}")

    # -------------------------------------------------------------------------
    # Step 3: Log an expense — equal split between Maya and Daniel
    # Maya paid $50.00 (5000 cents), split equally
    # -------------------------------------------------------------------------
    print("[smoke] Logging expense ...")
    expense_date = date.today().isoformat()
    status, exp_body = request(
        "POST",
        f"/api/v1/groups/{group_id}/expenses",
        body={
            "description": "Smoke test dinner",
            "amount_cents": 5000,
            "currency": "USD",
            "payer_member_id": admin_member_id,
            "split_type": "equal",
            "expense_date": expense_date,
            "splits": [
                {"member_id": admin_member_id},
                {"member_id": daniel_member_id},
            ],
        },
        headers={
            "Authorization": f"Bearer {admin_token}",
            "X-Idempotency-Key": idem_key_expense,
        },
    )
    assert_status(status, 201, f"POST /groups/{group_id}/expenses")

    expense_id = exp_body["id"]
    print(f"[smoke]   expense_id={expense_id}")
    print(f"[smoke]   amount_cents={exp_body['amount_cents']}")

    # -------------------------------------------------------------------------
    # Step 4: Fetch balances
    # -------------------------------------------------------------------------
    print("[smoke] Fetching balances ...")
    status, bal_body = request(
        "GET",
        f"/api/v1/groups/{group_id}/balances",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert_status(status, 200, f"GET /groups/{group_id}/balances")

    members = bal_body.get("members", [])
    print(f"[smoke]   balance members: {len(members)}")
    for m in members:
        print(f"[smoke]     {m['display_name']}: {m['net_display']} ({m['status']})")

    # Verify non-empty members list
    if not members:
        print("[smoke] FAILED: balances response has empty members list")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Step 5: Fetch settle-up plan
    # -------------------------------------------------------------------------
    print("[smoke] Fetching settle-up plan ...")
    status, settle_body = request(
        "GET",
        f"/api/v1/groups/{group_id}/settle-up",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert_status(status, 200, f"GET /groups/{group_id}/settle-up")

    transfers = settle_body.get("transfers", [])
    transfer_count = settle_body.get("transfer_count", 0)
    all_settled = settle_body.get("all_settled", True)

    print(f"[smoke]   all_settled={all_settled}")
    print(f"[smoke]   transfer_count={transfer_count}")
    for t in transfers:
        print(f"[smoke]     {t['debtor_name']} pays {t['creditor_name']} {t['amount_display']}")

    # With Maya paying $50 split equally, Daniel owes Maya $25 → 1 transfer
    if len(transfers) < 1:
        print(f"[smoke] FAILED: expected >= 1 transfer, got {len(transfers)}")
        sys.exit(1)

    # -------------------------------------------------------------------------
    # Step 6: Fetch group details
    # -------------------------------------------------------------------------
    print("[smoke] Fetching group details ...")
    status, grp_body = request(
        "GET",
        f"/api/v1/groups/{group_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert_status(status, 200, f"GET /groups/{group_id}")
    print(f"[smoke]   group name: {grp_body['name']}")
    print(f"[smoke]   member_count: {grp_body['member_count']}")
    print(f"[smoke]   expense_count: {grp_body['expense_count']}")

    # -------------------------------------------------------------------------
    # Step 7: Fetch members list
    # -------------------------------------------------------------------------
    print("[smoke] Fetching members list ...")
    status, mem_body = request(
        "GET",
        f"/api/v1/groups/{group_id}/members",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert_status(status, 200, f"GET /groups/{group_id}/members")
    print(f"[smoke]   total members: {mem_body['total']}")

    print()
    print("[smoke] All assertions passed.")
    sys.exit(0)


if __name__ == "__main__":
    run_smoke_test()
