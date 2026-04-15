"""
Compatibility shim — re-exports from the app.models package.

The canonical models live in app/models/ (the package directory).
Each model file imports Base from app.database.

This file exists so that any code written as:
    from app.models import Group, Member, ...
continues to work alongside:
    from app.models.group import Group
    from app.models.member import Member

Do NOT define any models here. Do NOT define a DeclarativeBase here.
The single shared Base is in app.database.
"""

from app.database import Base  # re-exported for convenience
from app.models.expense import Expense
from app.models.expense_split import ExpenseSplit
from app.models.group import Group
from app.models.idempotency_key import IdempotencyKey
from app.models.member import Member
from app.models.settlement import Settlement

__all__ = [
    "Base",
    "Group",
    "Member",
    "Expense",
    "ExpenseSplit",
    "Settlement",
    "IdempotencyKey",
]
