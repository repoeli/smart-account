from abc import ABC, abstractmethod
from typing import List, Optional

from domain.accounts.entities import User
from .entities import Transaction


class TransactionRepository(ABC):
    @abstractmethod
    def save(self, tx: Transaction) -> Transaction: ...

    @abstractmethod
    def find_by_id(self, tx_id: str) -> Optional[Transaction]: ...

    @abstractmethod
    def find_by_user(self, user: User, limit: int = 100, offset: int = 0) -> List[Transaction]: ...


