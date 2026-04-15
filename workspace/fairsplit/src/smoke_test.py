"""
Post-deploy smoke test for FairSplit.

Validates that the backend health endpoint responds, that the core group
creation and join flows work end-to-end, and that the frontend loads.

Run locally:
    BACKEND_URL=http://localhost:8000 FRONTEND_URL=http://localhost:3000 python smoke_test.py

Run in CI (set BACKEND_URL and FRONTEND_URL env vars):
    python smoke_test.py

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed (details printed to stdout).
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000").rstrip("/")
TIMEOUT = int(os.environ.get("SMOKE_TIMEOUT", "10"))

# Health endpoint acceptable status values (backend returns "healthy" or "ok")
_HEALTHY_STATUS = {"ok", "healthy"}
# Health endpoint acceptable db values
_HEALTHY_DB = {"ok", "connected"}

failures: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {name}" + (f" — {detail}" if detail else ""))
    if not ok:
        failures.append(f"{name}: {detail}")


def get(path: str, headers: dict | None = None) -> tuple[int, dict | None]:
    url = f"{BACKEND_URL}{path}"
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = None
        return e.code, body
    except Exception as exc:
        return 0, {"error": str(exc)}


def post(path: str, data: dict, headers: dict | None = None) -> tuple[int, dict | None]:
    url = f"{BACKEND_URL}{path}"
    payload = json.dumps(data).encode()
    base_headers = {"Content-Type": "application/json"}
    if headers:
        base_headers.update(headers)
    req = urllib.request.Request(url, data=payload, headers=base_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = json.loads(resp.read().decode())
            return resp.status, body
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            body = None
        return e.code, body
    except Exception as exc:
        return 0, {"error": str(exc)}


def frontend_get(path: str = "/") -> int:
    url = f"{FRONTEND_URL}{path}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def main() -> None:
    print(f"\nFairSplit smoke test — {BACKEND_URL}")
    print("=" * 60)

    # ── 1. Health endpoint ─────────────────────────────────────────────────
    print("\n1. Health endpoint")
    status, body = get("/health")
    check("GET /health returns 200", status == 200, f"status={status}")
    check(
        "status field indicates healthy",
        body is not None and body.get("status") in _HEALTHY_STATUS,
        str(body),
    )
    check(
        "db field indicates connected",
        body is not None and body.get("db") in _HEALTHY_DB,
        str(body),
    )

    # ── 2. Create a group ──────────────────────────────────────────────────
    print("\n2. Group creation")
    idempotency_key = str(uuid.uuid4())
    status, body = post(
        "/api/v1/groups",
        {"name": "Smoke Test Group", "currency": "USD", "creator_display_name": "Smokey"},
        {"X-Idempotency-Key": idempotency_key},
    )
    check("POST /api/v1/groups returns 201", status == 201, f"status={status}, body={body}")
    group_id = None
    invite_token = None
    member_token = None
    if body:
        group_id = body.get("group", {}).get("id")
        invite_token = body.get("group", {}).get("invite_token")
        member_token = body.get("token")
        check("group.id present in response", bool(group_id), str(body))
        check("group.invite_token present", bool(invite_token), str(body))
        check("token present in response", bool(member_token), str(body))
        check("member.is_admin = true", body.get("member", {}).get("is_admin") is True, str(body))

    # ── 3. Idempotency re-submission ───────────────────────────────────────
    print("\n3. Idempotency re-submission")
    if idempotency_key:
        status2, body2 = post(
            "/api/v1/groups",
            {"name": "Duplicate Group", "currency": "USD", "creator_display_name": "Dupe"},
            {"X-Idempotency-Key": idempotency_key},
        )
        check(
            "Re-submission with same key returns 201 (cached)",
            status2 == 201,
            f"status={status2}",
        )
        if body and body2:
            check(
                "Re-submission returns same group id",
                body.get("group", {}).get("id") == body2.get("group", {}).get("id"),
                f"id1={body.get('group', {}).get('id')}, id2={body2.get('group', {}).get('id')}",
            )

    # ── 4. Join via invite link ────────────────────────────────────────────
    print("\n4. Join via invite link")
    join_token = None
    if invite_token:
        status, join_body = post(
            f"/api/v1/join/{invite_token}",
            {"display_name": "Joiner"},
        )
        check("POST /api/v1/join/{token} returns 200 or 201", status in (200, 201), f"status={status}")
        if join_body:
            join_token = join_body.get("token")
            check("join response includes token", bool(join_token), str(join_body))
            check("join response includes group", bool(join_body.get("group")), str(join_body))
            check(
                "join member.is_admin = false",
                join_body.get("member", {}).get("is_admin") is False,
                str(join_body),
            )

    # ── 5. Get group details (authenticated) ───────────────────────────────
    print("\n5. Authenticated group fetch")
    if group_id and member_token:
        status, body = get(
            f"/api/v1/groups/{group_id}",
            {"Authorization": f"Bearer {member_token}"},
        )
        check("GET /api/v1/groups/{id} returns 200", status == 200, f"status={status}")
        check(
            "Response contains group name",
            body is not None and body.get("name") == "Smoke Test Group",
            str(body),
        )

    # ── 6. Get members list ────────────────────────────────────────────────
    print("\n6. Members list")
    if group_id and member_token:
        status, body = get(
            f"/api/v1/groups/{group_id}/members",
            {"Authorization": f"Bearer {member_token}"},
        )
        check("GET /groups/{id}/members returns 200", status == 200, f"status={status}")
        if body:
            members = body.get("data", [])
            check("Member list has at least 2 members", len(members) >= 2, f"count={len(members)}")

    # ── 7. Get balances (empty — no expenses yet) ──────────────────────────
    print("\n7. Balances endpoint (empty state)")
    if group_id and member_token:
        status, body = get(
            f"/api/v1/groups/{group_id}/balances",
            {"Authorization": f"Bearer {member_token}"},
        )
        check("GET /groups/{id}/balances returns 200", status == 200, f"status={status}")

    # ── 8. Get settle-up (empty) ───────────────────────────────────────────
    print("\n8. Settle-up endpoint (empty state)")
    if group_id and member_token:
        status, body = get(
            f"/api/v1/groups/{group_id}/settle-up",
            {"Authorization": f"Bearer {member_token}"},
        )
        check("GET /groups/{id}/settle-up returns 200", status == 200, f"status={status}")
        if body:
            check(
                "all_settled = true when no expenses",
                body.get("all_settled") is True,
                str(body),
            )

    # ── 9. Log an expense ─────────────────────────────────────────────────
    print("\n9. Log expense")
    expense_id = None
    if group_id and member_token and join_token:
        # Get member IDs first
        _, members_body = get(
            f"/api/v1/groups/{group_id}/members",
            {"Authorization": f"Bearer {member_token}"},
        )
        members_list = (members_body or {}).get("data", [])
        if len(members_list) >= 2:
            payer_id = members_list[0]["id"]
            other_id = members_list[1]["id"]
            expense_key = str(uuid.uuid4())
            status, body = post(
                f"/api/v1/groups/{group_id}/expenses",
                {
                    "description": "Smoke test dinner",
                    "amount_cents": 4200,
                    "paid_by_member_id": payer_id,
                    "date": time.strftime("%Y-%m-%d"),
                    "split_type": "equal",
                    "splits": [
                        {"member_id": payer_id, "amount_cents": 2100},
                        {"member_id": other_id, "amount_cents": 2100},
                    ],
                },
                {
                    "Authorization": f"Bearer {member_token}",
                    "X-Idempotency-Key": expense_key,
                },
            )
            check(
                "POST /groups/{id}/expenses returns 201",
                status == 201,
                f"status={status}, body={body}",
            )
            if body:
                expense_id = body.get("id")
                check("expense.amount_cents = 4200", body.get("amount_cents") == 4200, str(body))
                check("expense.id present", bool(expense_id), str(body))

    # ── 10. Balances reflect the expense ──────────────────────────────────
    print("\n10. Balances after expense")
    if group_id and member_token and expense_id:
        status, body = get(
            f"/api/v1/groups/{group_id}/balances",
            {"Authorization": f"Bearer {member_token}"},
        )
        check("GET /groups/{id}/balances returns 200", status == 200, f"status={status}")
        if body:
            balances = body if isinstance(body, list) else body.get("data", [])
            nonzero = [b for b in balances if b.get("balance_cents", 0) != 0]
            check(
                "At least one non-zero balance after expense",
                len(nonzero) > 0,
                f"balances={balances}",
            )

    # ── 11. Settle-up returns transfers ───────────────────────────────────
    print("\n11. Settle-up after expense")
    if group_id and member_token and expense_id:
        status, body = get(
            f"/api/v1/groups/{group_id}/settle-up",
            {"Authorization": f"Bearer {member_token}"},
        )
        check("GET /groups/{id}/settle-up returns 200", status == 200, f"status={status}")
        if body:
            transfers = body.get("transfers", [])
            check(
                "Settle-up returns at least 1 transfer",
                len(transfers) >= 1,
                f"transfers={transfers}",
            )
            check(
                "all_settled = false with outstanding balance",
                body.get("all_settled") is False,
                str(body),
            )

    # ── 12. Frontend loads ────────────────────────────────────────────────
    print("\n12. Frontend availability")
    if FRONTEND_URL:
        frontend_status = frontend_get("/")
        check("Frontend GET / returns 200", frontend_status == 200, f"status={frontend_status}")

    # ── Summary ────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    if failures:
        print(f"FAILED — {len(failures)} check(s) failed:")
        for f in failures:
            print(f"  - {f}")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED")
        sys.exit(0)


if __name__ == "__main__":
    main()
