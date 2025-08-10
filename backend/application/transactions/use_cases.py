from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from domain.accounts.entities import User
from domain.transactions.repositories import TransactionRepository
from domain.transactions.entities import Transaction, TransactionType, Money, Category


@dataclass
class CreateTransactionCommand:
    user: User
    description: str
    amount: Decimal
    currency: str
    type: str  # 'income' | 'expense'
    transaction_date: date
    receipt_id: Optional[str] = None
    category: Optional[str] = None


class CreateTransactionUseCase:
    def __init__(self, tx_repo: TransactionRepository):
        self._tx_repo = tx_repo

    def execute(self, cmd: CreateTransactionCommand) -> dict:
        tx = Transaction(
            id="",  # repo to assign
            user=cmd.user,
            description=cmd.description,
            amount=Money(amount=cmd.amount, currency=cmd.currency or "GBP"),
            type=TransactionType(cmd.type),
            transaction_date=cmd.transaction_date,
            receipt_id=cmd.receipt_id,
            category=Category(cmd.category) if cmd.category else None,
        )
        saved = self._tx_repo.save(tx)
        return {"success": True, "transaction_id": saved.id}


