"""Expense CRUD endpoints.

GET    /api/v1/groups/{id}/expenses              — list expenses (paginated)
POST   /api/v1/groups/{id}/expenses              — create expense
GET    /api/v1/groups/{id}/expenses/{expense_id} — get expense detail
PATCH  /api/v1/groups/{id}/expenses/{expense_id} — update expense
DELETE /api/v1/groups/{id}/expenses/{expense_id} — soft-delete expense
"""

from __future__ import annotations

import logging
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

import app.schemas as schemas
from app.database import get_db
from app.middleware.auth_middleware import MemberContext, get_current_member
from app.repositories.expense_repo import ExpenseRepository
from app.repositories.group_repo import GroupRepository
from app.repositories.member_repo import MemberRepository
from app.services.idempotency_service import check_idempotency, store_idempotency

router = APIRouter(prefix="/api/v1", tags=["expenses"])
logger = logging.getLogger(__name__)


@router.get("/groups/{group_id}/expenses")
async def list_expenses(
    group_id: uuid.UUID,
    request: Request,
    page: int = 1,
    per_page: int = 20,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """List active expenses, newest first, paginated."""
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)
    _validate_pagination(page, per_page)

    group_repo = GroupRepository(session)
    group = await group_repo.get_by_id(group_id)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    expense_repo = ExpenseRepository(session)
    summaries, total = await expense_repo.list_by_group(group_id, page, per_page)

    data = [
        schemas.ExpenseSummary(
            id=s["id"],
            description=s["description"],
            amount_cents=s["amount_cents"],
            amount_display=schemas.format_cents(s["amount_cents"], s["currency"]),
            currency=s["currency"],
            split_type=s["split_type"],
            split_count=s["split_count"],
            payer_id=s["payer_id"],
            payer_name=s["payer_name"],
            logged_by_name=s["logged_by_name"],
            expense_date=s["expense_date"],
            created_at=s["created_at"],
        ).model_dump(mode="json")
        for s in summaries
    ]

    return {"data": data, "total": total, "page": page, "per_page": per_page}


@router.post("/groups/{group_id}/expenses", status_code=201)
async def create_expense(
    group_id: uuid.UUID,
    body: schemas.CreateExpenseRequest,
    request: Request,
    x_idempotency_key: Optional[str] = Header(default=None, alias="X-Idempotency-Key"),
    session: AsyncSession = Depends(get_db),
) -> schemas.Expense:
    """Log a new expense with split breakdown.

    Split validation:
    - equal: splits list provides member_ids; server computes equal shares.
    - custom_amount: split amount_cents must sum to expense amount_cents.
    - custom_percentage: split percentages must sum to 100.0; server converts
      to cents; 1-cent rounding remainder goes to first member alphabetically.

    Idempotent: provide X-Idempotency-Key to prevent double-submission.
    """
    request_id = str(uuid.uuid4())[:8]
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    idem_key: uuid.UUID | None = None
    if x_idempotency_key:
        try:
            idem_key = uuid.UUID(x_idempotency_key)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail={"error": {"code": "VALIDATION_ERROR", "message": "X-Idempotency-Key must be a valid UUID.", "request_id": request_id}},
            )

    async with session.begin():
        cached = await check_idempotency(session, idem_key)
        if cached is not None:
            return schemas.Expense(**cached)

        # Validate group exists and is active
        group_repo = GroupRepository(session)
        group = await group_repo.get_by_id(group_id)
        if group is None:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": request_id}},
            )
        if group.status == "archived":
            raise HTTPException(
                status_code=409,
                detail={"error": {"code": "GROUP_ARCHIVED", "message": "Cannot add expenses to an archived group.", "request_id": request_id}},
            )

        # Validate payer is in this group
        member_repo = MemberRepository(session)
        payer = await member_repo.get_by_id(body.payer_member_id)
        if payer is None or payer.group_id != group_id:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "MEMBER_NOT_FOUND", "message": "Payer member not found in this group.", "request_id": request_id}},
            )

        # Validate all split members are in this group
        for split in body.splits:
            split_member = await member_repo.get_by_id(split.member_id)
            if split_member is None or split_member.group_id != group_id:
                raise HTTPException(
                    status_code=404,
                    detail={"error": {"code": "MEMBER_NOT_FOUND", "message": f"Member {split.member_id} not found in this group.", "request_id": request_id}},
                )

        # Compute splits
        split_data = _compute_splits(body, group_id, request_id)

        expense_date = body.expense_date or date.today()

        expense_repo = ExpenseRepository(session)
        expense = await expense_repo.create(
            group_id=group_id,
            payer_member_id=body.payer_member_id,
            logged_by_member_id=current_member.member_id,
            description=body.description,
            amount_cents=body.amount_cents,
            currency=body.currency,
            split_type=body.split_type,
            expense_date=expense_date,
            splits=split_data,
        )

        result = _expense_to_schema(expense, group.default_currency)
        response_dict = result.model_dump(mode="json")

        await store_idempotency(
            session=session,
            idempotency_key=idem_key,
            endpoint=f"POST /api/v1/groups/{group_id}/expenses",
            response_body=response_dict,
            status_code=201,
        )

    logger.info(
        "expense_created",
        extra={
            "group_id": str(group_id),
            "expense_id": str(expense.id),
            "member_id": str(current_member.member_id),
            "amount_cents": expense.amount_cents,
        },
    )

    return result


@router.get("/groups/{group_id}/expenses/{expense_id}")
async def get_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.Expense:
    """Get full expense detail with per-member split breakdown."""
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    group_repo = GroupRepository(session)
    group = await group_repo.get_by_id(group_id)
    if group is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": _req_id()}},
        )

    expense_repo = ExpenseRepository(session)
    expense = await expense_repo.get_by_id(expense_id)
    if expense is None or expense.group_id != group_id:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "EXPENSE_NOT_FOUND", "message": "Expense not found.", "request_id": _req_id()}},
        )

    return _expense_to_schema(expense, group.default_currency)


@router.patch("/groups/{group_id}/expenses/{expense_id}")
async def update_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    body: schemas.UpdateExpenseRequest,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.Expense:
    """Edit an expense. Caller must be the logger or a group admin."""
    request_id = _req_id()
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    async with session.begin():
        group_repo = GroupRepository(session)
        group = await group_repo.get_by_id(group_id)
        if group is None:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": request_id}},
            )
        if group.status == "archived":
            raise HTTPException(
                status_code=409,
                detail={"error": {"code": "GROUP_ARCHIVED", "message": "Cannot edit expenses in an archived group.", "request_id": request_id}},
            )

        expense_repo = ExpenseRepository(session)
        expense = await expense_repo.get_by_id(expense_id)
        if expense is None or expense.group_id != group_id:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "EXPENSE_NOT_FOUND", "message": "Expense not found.", "request_id": request_id}},
            )

        # Permission check: must be logger or admin
        if (
            expense.logged_by_member_id != current_member.member_id
            and not current_member.is_admin
        ):
            raise HTTPException(
                status_code=403,
                detail={"error": {"code": "PERMISSION_DENIED", "message": "You can only edit expenses you logged, or you must be the group admin.", "request_id": request_id}},
            )

        updates: dict = {}
        if body.description is not None:
            updates["description"] = body.description
        if body.amount_cents is not None:
            updates["amount_cents"] = body.amount_cents
        if body.currency is not None:
            updates["currency"] = body.currency
        if body.payer_member_id is not None:
            # Validate new payer is in this group
            member_repo = MemberRepository(session)
            new_payer = await member_repo.get_by_id(body.payer_member_id)
            if new_payer is None or new_payer.group_id != group_id:
                raise HTTPException(
                    status_code=404,
                    detail={"error": {"code": "MEMBER_NOT_FOUND", "message": "Payer not found in this group.", "request_id": request_id}},
                )
            updates["payer_member_id"] = body.payer_member_id
        if body.split_type is not None:
            updates["split_type"] = body.split_type
        if body.expense_date is not None:
            updates["expense_date"] = body.expense_date

        # Compute new splits if provided
        split_data: list[dict] | None = None
        if body.splits is not None:
            # Build a synthetic create request to reuse split computation
            effective_amount = body.amount_cents if body.amount_cents is not None else expense.amount_cents
            effective_split_type = body.split_type if body.split_type is not None else expense.split_type

            class _SyntheticRequest:
                amount_cents = effective_amount
                split_type = effective_split_type
                splits = body.splits

            split_data = _compute_splits(_SyntheticRequest(), group_id, request_id)  # type: ignore[arg-type]

        updated = await expense_repo.update(expense_id, split_data, **updates)

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "EXPENSE_NOT_FOUND", "message": "Expense not found.", "request_id": request_id}},
        )

    logger.info(
        "expense_updated",
        extra={"group_id": str(group_id), "expense_id": str(expense_id), "member_id": str(current_member.member_id)},
    )

    return _expense_to_schema(updated, group.default_currency)


@router.delete("/groups/{group_id}/expenses/{expense_id}")
async def delete_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> schemas.DeletedResponse:
    """Soft-delete an expense. Caller must be the logger or a group admin.

    Idempotent: deleting an already-deleted expense returns 200.
    """
    request_id = _req_id()
    current_member = get_current_member(request)
    _verify_group_access(current_member, group_id)

    async with session.begin():
        group_repo = GroupRepository(session)
        group = await group_repo.get_by_id(group_id)
        if group is None:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "GROUP_NOT_FOUND", "message": "Group not found.", "request_id": request_id}},
            )
        if group.status == "archived":
            raise HTTPException(
                status_code=409,
                detail={"error": {"code": "GROUP_ARCHIVED", "message": "Cannot delete expenses in an archived group.", "request_id": request_id}},
            )

        expense_repo = ExpenseRepository(session)
        # Check including already-deleted (idempotent delete)
        expense = await expense_repo.get_by_id_including_deleted(expense_id)
        if expense is None or expense.group_id != group_id:
            raise HTTPException(
                status_code=404,
                detail={"error": {"code": "EXPENSE_NOT_FOUND", "message": "Expense not found.", "request_id": request_id}},
            )

        # If already deleted, return success (idempotent)
        if expense.deleted_at is not None:
            return schemas.DeletedResponse(message="Expense deleted successfully.")

        # Permission check
        if (
            expense.logged_by_member_id != current_member.member_id
            and not current_member.is_admin
        ):
            raise HTTPException(
                status_code=403,
                detail={"error": {"code": "PERMISSION_DENIED", "message": "You can only delete expenses you logged, or you must be the group admin.", "request_id": request_id}},
            )

        await expense_repo.soft_delete(expense_id)

    logger.info(
        "expense_deleted",
        extra={"group_id": str(group_id), "expense_id": str(expense_id), "member_id": str(current_member.member_id)},
    )

    return schemas.DeletedResponse(message="Expense deleted successfully.")


# ---------------------------------------------------------------------------
# Split computation helpers
# ---------------------------------------------------------------------------


def _compute_splits(body, group_id: uuid.UUID, request_id: str) -> list[dict]:  # type: ignore[type-arg]
    """Compute the per-member split_data list from the request body.

    Returns a list of dicts ready for ExpenseRepository.create().
    Raises HTTPException 422 on validation failures.
    """
    splits = body.splits
    split_type = body.split_type
    amount_cents = body.amount_cents

    if split_type == "equal":
        # Server computes equal shares
        n = len(splits)
        base = amount_cents // n
        remainder = amount_cents % n

        # Sort by member_id string for deterministic remainder assignment
        sorted_splits = sorted(splits, key=lambda s: str(s.member_id))
        result = []
        for i, split in enumerate(sorted_splits):
            share = base + (1 if i < remainder else 0)
            result.append({"member_id": split.member_id, "amount_cents": share, "percentage": None})
        return result

    elif split_type == "custom_amount":
        total = sum(s.amount_cents or 0 for s in splits)
        if total != amount_cents:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "code": "SPLIT_SUM_MISMATCH",
                        "message": f"Split amounts sum to {total} cents but expense total is {amount_cents} cents.",
                        "request_id": request_id,
                    }
                },
            )
        for split in splits:
            if split.amount_cents is None:
                raise HTTPException(
                    status_code=422,
                    detail={"error": {"code": "VALIDATION_ERROR", "message": "amount_cents is required for custom_amount splits.", "request_id": request_id}},
                )
        return [
            {"member_id": s.member_id, "amount_cents": s.amount_cents, "percentage": None}
            for s in splits
        ]

    elif split_type == "custom_percentage":
        for split in splits:
            if split.percentage is None:
                raise HTTPException(
                    status_code=422,
                    detail={"error": {"code": "VALIDATION_ERROR", "message": "percentage is required for custom_percentage splits.", "request_id": request_id}},
                )
        pct_total = sum(s.percentage or 0.0 for s in splits)
        # Allow tiny floating point tolerance
        if abs(pct_total - 100.0) > 0.001:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": {
                        "code": "SPLIT_SUM_MISMATCH",
                        "message": f"Split percentages sum to {pct_total:.3f}% but must equal 100.0%.",
                        "request_id": request_id,
                    }
                },
            )

        # Convert percentages to cents; remainder goes to first member alphabetically
        # Sort by member_id string for deterministic ordering
        sorted_splits = sorted(splits, key=lambda s: str(s.member_id))
        computed = []
        total_assigned = 0
        for split in sorted_splits:
            share = int(amount_cents * (split.percentage or 0.0) / 100.0)
            total_assigned += share
            computed.append({
                "member_id": split.member_id,
                "amount_cents": share,
                "percentage": Decimal(str(split.percentage)),
            })

        # Assign 1-cent remainder to first member alphabetically
        remainder = amount_cents - total_assigned
        if remainder != 0 and computed:
            computed[0]["amount_cents"] += remainder

        return computed

    raise HTTPException(
        status_code=422,
        detail={"error": {"code": "VALIDATION_ERROR", "message": f"Unknown split_type: {split_type}", "request_id": request_id}},
    )


def _expense_to_schema(expense, default_currency: str) -> schemas.Expense:
    """Convert an Expense ORM object (with eagerly loaded relations) to a schema."""
    splits = []
    for es in expense.splits:
        splits.append(
            schemas.ExpenseSplit(
                member_id=es.member_id,
                display_name=es.member.display_name,
                amount_cents=es.amount_cents,
                amount_display=schemas.format_cents(es.amount_cents, expense.currency),
                percentage=float(es.percentage) if es.percentage is not None else None,
            )
        )

    return schemas.Expense(
        id=expense.id,
        group_id=expense.group_id,
        description=expense.description,
        amount_cents=expense.amount_cents,
        amount_display=schemas.format_cents(expense.amount_cents, expense.currency),
        currency=expense.currency,
        split_type=expense.split_type,
        expense_date=expense.expense_date,
        payer=schemas.ExpensePayerSummary(
            id=expense.payer.id,
            display_name=expense.payer.display_name,
        ),
        logged_by=schemas.ExpenseLoggedBySummary(
            display_name=expense.logged_by.display_name,
        ),
        splits=splits,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


def _verify_group_access(current_member: MemberContext, group_id: uuid.UUID) -> None:
    if current_member.group_id != group_id:
        raise HTTPException(
            status_code=403,
            detail={
                "error": {
                    "code": "MEMBER_WRONG_GROUP",
                    "message": "Your session token is for a different group.",
                    "request_id": _req_id(),
                }
            },
        )


def _validate_pagination(page: int, per_page: int) -> None:
    if page < 1:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "VALIDATION_ERROR", "message": "page must be >= 1.", "request_id": _req_id()}},
        )
    if per_page < 1 or per_page > 100:
        raise HTTPException(
            status_code=422,
            detail={"error": {"code": "VALIDATION_ERROR", "message": "per_page must be between 1 and 100.", "request_id": _req_id()}},
        )


def _req_id() -> str:
    return str(uuid.uuid4())[:8]
