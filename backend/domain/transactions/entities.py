"""
Domain entities and value objects for transactions.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional

from domain.common.entities import AggregateRoot, ValueObject
from domain.accounts.entities import User


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"


@dataclass(frozen=True)
class Money(ValueObject):
    amount: Decimal
    currency: str = "GBP"


@dataclass(frozen=True)
class Category(ValueObject):
    name: str


class Transaction(AggregateRoot):
    def __init__(
        self,
        id: str,
        user: User,
        description: str,
        amount: Money,
        type: TransactionType,
        transaction_date: date,
        receipt_id: Optional[str] = None,
        category: Optional[Category] = None,
    ) -> None:
        super().__init__(id)
        self.user = user
        self.description = description
        self.amount = amount
        self.type = type
        self.transaction_date = transaction_date
        self.receipt_id = receipt_id
        self.category = category


