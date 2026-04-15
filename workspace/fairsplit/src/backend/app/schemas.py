"""Pydantic v2 request and response schemas.

All schemas match the api-spec.yaml contract exactly. Field names, types, and
required/optional markers are authoritative — do not deviate from these.

Money is always integer cents (amount_cents: int). The amount_display field
is a formatted string computed at serialisation time, never stored.

Enums are plain string literals checked by Pydantic validators, matching the
exact values defined in api-spec.yaml and the DB CHECK constraints.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

CURRENCY_RE = re.compile(r"^[A-Z]{3}$")

VALID_CURRENCIES = {"USD", "EUR", "GBP", "CAD", "AUD"}
VALID_SPLIT_TYPES = {"equal", "custom_amount", "custom_percentage"}
VALID_STATUSES = {"active", "archived"}


def format_cents(cents: int, currency: str = "USD") -> str:
    """Convert integer cents to a locale-formatted display string.

    Examples:
        4200, "USD"  -> "$42.00"
        -4200, "USD" -> "-$42.00"
        8450, "EUR"  -> "€84.50"
    """
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "CA$", "AUD": "AU$"}
    symbol = symbols.get(currency, currency + " ")
    abs_cents = abs(cents)
    display = f"{symbol}{abs_cents // 100}.{abs_cents % 100:02d}"
    return f"-{display}" if cents < 0 else display


def format_net_cents(cents: int, currency: str = "USD") -> str:
    """Format with explicit +/- prefix for balance display."""
    symbols = {"USD": "$", "EUR": "€", "GBP": "£", "CAD": "CA$", "AUD": "AU$"}
    symbol = symbols.get(currency, currency + " ")
    abs_cents = abs(cents)
    display = f"{symbol}{abs_cents // 100}.{abs_cents % 100:02d}"
    if cents > 0:
        return f"+{display}"
    if cents < 0:
        return f"-{display}"
    return display


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str  # "healthy" | "unhealthy"
    db: str       # "connected" | "unreachable"
    timestamp: datetime


# ---------------------------------------------------------------------------
# Group schemas
# ---------------------------------------------------------------------------


class Group(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: Optional[str] = None
    invite_token: UUID
    status: str
    default_currency: str
    member_count: int
    expense_count: int
    created_at: datetime
    updated_at: datetime


class CreateGroupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, max_length=200)
    admin_display_name: str = Field(min_length=1, max_length=40)
    default_currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Group name cannot be blank.")
        return stripped

    @field_validator("admin_display_name", mode="before")
    @classmethod
    def strip_admin_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Display name cannot be blank.")
        return stripped


class UpdateGroupRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    description: Optional[str] = Field(default=None, max_length=200)
    status: Optional[str] = None
    force: bool = False

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_STATUSES:
            raise ValueError(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")
        return v

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("Group name cannot be blank.")
        return stripped


# ---------------------------------------------------------------------------
# Member schemas
# ---------------------------------------------------------------------------


class Member(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    display_name: str
    is_admin: bool
    joined_at: datetime


class JoinGroupRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=40)

    @field_validator("display_name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Display name cannot be blank.")
        return stripped


# ---------------------------------------------------------------------------
# Auth / session response schemas
# ---------------------------------------------------------------------------


class CreateGroupResponse(BaseModel):
    group: Group
    member: Member
    token: str


class JoinGroupGroupSummary(BaseModel):
    """Minimal group info returned in the join response (per api-spec.yaml)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str
    default_currency: str
    member_count: int


class JoinGroupResponse(BaseModel):
    group: JoinGroupGroupSummary
    member: Member
    token: str


class InviteTokenResponse(BaseModel):
    invite_token: UUID


# ---------------------------------------------------------------------------
# Expense schemas
# ---------------------------------------------------------------------------


class ExpenseSplit(BaseModel):
    """Per-member split detail — used in the full expense detail view."""
    model_config = ConfigDict(from_attributes=True)

    member_id: UUID
    display_name: str
    amount_cents: int
    amount_display: str
    percentage: Optional[float] = None


class ExpensePayerSummary(BaseModel):
    """Minimal payer info embedded in Expense response."""
    id: UUID
    display_name: str


class ExpenseLoggedBySummary(BaseModel):
    """Minimal logged-by info embedded in Expense response."""
    display_name: str


class Expense(BaseModel):
    """Full expense detail including per-member splits."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    description: str
    amount_cents: int
    amount_display: str
    currency: str
    split_type: str
    expense_date: date
    payer: ExpensePayerSummary
    logged_by: ExpenseLoggedBySummary
    splits: list[ExpenseSplit]
    created_at: datetime
    updated_at: datetime


class ExpenseSummary(BaseModel):
    """Lightweight expense record for list view (no full splits array)."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    description: str
    amount_cents: int
    amount_display: str
    currency: str
    split_type: str
    split_count: int
    payer_id: UUID
    payer_name: str
    logged_by_name: str
    expense_date: date
    created_at: datetime


class SplitInput(BaseModel):
    """Per-member split instruction in expense create/update requests."""
    member_id: UUID
    amount_cents: Optional[int] = Field(default=None, ge=0)
    percentage: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class CreateExpenseRequest(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount_cents: int = Field(gt=0, le=99_999_999)
    currency: str = Field(default="USD", pattern=r"^[A-Z]{3}$")
    payer_member_id: UUID
    split_type: str
    expense_date: Optional[date] = None
    splits: list[SplitInput] = Field(min_length=1)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Description cannot be blank.")
        return stripped

    @field_validator("split_type")
    @classmethod
    def validate_split_type(cls, v: str) -> str:
        if v not in VALID_SPLIT_TYPES:
            raise ValueError(f"split_type must be one of: {', '.join(sorted(VALID_SPLIT_TYPES))}")
        return v


class UpdateExpenseRequest(BaseModel):
    description: Optional[str] = Field(default=None, min_length=1, max_length=200)
    amount_cents: Optional[int] = Field(default=None, gt=0, le=99_999_999)
    currency: Optional[str] = Field(default=None, pattern=r"^[A-Z]{3}$")
    payer_member_id: Optional[UUID] = None
    split_type: Optional[str] = None
    expense_date: Optional[date] = None
    splits: Optional[list[SplitInput]] = Field(default=None, min_length=1)

    @field_validator("description", mode="before")
    @classmethod
    def strip_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        stripped = v.strip()
        if not stripped:
            raise ValueError("Description cannot be blank.")
        return stripped

    @field_validator("split_type")
    @classmethod
    def validate_split_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_SPLIT_TYPES:
            raise ValueError(f"split_type must be one of: {', '.join(sorted(VALID_SPLIT_TYPES))}")
        return v


# ---------------------------------------------------------------------------
# Balance schemas
# ---------------------------------------------------------------------------


class MemberBalance(BaseModel):
    member_id: UUID
    display_name: str
    net_cents: int
    net_display: str
    paid_total_cents: int
    owed_total_cents: int
    settled_out_cents: int
    settled_in_cents: int
    status: str  # "creditor" | "debtor" | "settled"


class MemberBalanceDetail(MemberBalance):
    expense_count_paid: int
    summary: str


class BalancesResponse(BaseModel):
    currency: str
    members: list[MemberBalance]
    computed_at: datetime


# ---------------------------------------------------------------------------
# Settle-up schemas
# ---------------------------------------------------------------------------


class Transfer(BaseModel):
    debtor_id: UUID
    debtor_name: str
    creditor_id: UUID
    creditor_name: str
    amount_cents: int
    amount_display: str
    currency: str


class SettleUpResponse(BaseModel):
    group_name: str
    currency: str
    all_settled: bool
    transfer_count: int
    transfers: list[Transfer]
    clipboard_text: str
    computed_at: datetime


# ---------------------------------------------------------------------------
# Settlement schemas
# ---------------------------------------------------------------------------


class Settlement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    group_id: UUID
    payer_id: UUID
    payer_name: str
    payee_id: UUID
    payee_name: str
    amount_cents: int
    amount_display: str
    currency: str
    created_at: datetime


class CreateSettlementRequest(BaseModel):
    payer_member_id: UUID
    payee_member_id: UUID
    amount_cents: int = Field(gt=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")

    @model_validator(mode="after")
    def validate_different_members(self) -> "CreateSettlementRequest":
        if self.payer_member_id == self.payee_member_id:
            raise ValueError("payer and payee must be different members.")
        return self


# ---------------------------------------------------------------------------
# Pagination wrapper
# ---------------------------------------------------------------------------


class PaginatedResponse(BaseModel):
    """Generic pagination envelope used for collection endpoints."""

    data: list
    total: int
    page: int
    per_page: int


# ---------------------------------------------------------------------------
# Error response
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None
    request_id: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


# ---------------------------------------------------------------------------
# Delete confirmation
# ---------------------------------------------------------------------------


class DeletedResponse(BaseModel):
    message: str
