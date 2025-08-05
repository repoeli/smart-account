"""
Repository interfaces for receipt management.
Defines abstract repository interfaces for receipt persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.receipts.entities import Receipt, ReceiptStatus, ReceiptType
from domain.accounts.entities import User


class ReceiptRepository(ABC):
    """Abstract repository interface for receipt persistence."""
    
    @abstractmethod
    def save(self, receipt: Receipt) -> Receipt:
        """Save or update a receipt."""
        pass
    
    @abstractmethod
    def find_by_id(self, receipt_id: str) -> Optional[Receipt]:
        """Find a receipt by its ID."""
        pass
    
    @abstractmethod
    def find_by_user(self, user: User, limit: int = 100, offset: int = 0) -> List[Receipt]:
        """Find receipts by user with pagination."""
        pass
    
    @abstractmethod
    def find_by_status(self, user: User, status: ReceiptStatus, limit: int = 100, offset: int = 0) -> List[Receipt]:
        """Find receipts by status for a specific user."""
        pass
    
    @abstractmethod
    def find_by_type(self, user: User, receipt_type: ReceiptType, limit: int = 100, offset: int = 0) -> List[Receipt]:
        """Find receipts by type for a specific user."""
        pass
    
    @abstractmethod
    def find_by_date_range(self, user: User, start_date, end_date, limit: int = 100, offset: int = 0) -> List[Receipt]:
        """Find receipts within a date range for a specific user."""
        pass
    
    @abstractmethod
    def find_by_merchant(self, user: User, merchant_name: str, limit: int = 100, offset: int = 0) -> List[Receipt]:
        """Find receipts by merchant name for a specific user."""
        pass
    
    @abstractmethod
    def find_by_amount_range(self, user: User, min_amount: float, max_amount: float, limit: int = 100, offset: int = 0) -> List[Receipt]:
        """Find receipts within an amount range for a specific user."""
        pass
    
    @abstractmethod
    def search_receipts(self, user: User, query: str, limit: int = 100, offset: int = 0) -> List[Receipt]:
        """Search receipts by text query for a specific user."""
        pass
    
    @abstractmethod
    def delete(self, receipt_id: str) -> bool:
        """Delete a receipt by ID."""
        pass
    
    @abstractmethod
    def count_by_user(self, user: User) -> int:
        """Count total receipts for a user."""
        pass
    
    @abstractmethod
    def count_by_status(self, user: User, status: ReceiptStatus) -> int:
        """Count receipts by status for a user."""
        pass
    
    @abstractmethod
    def get_processing_receipts(self) -> List[Receipt]:
        """Get all receipts that are currently being processed."""
        pass
    
    @abstractmethod
    def get_failed_receipts(self) -> List[Receipt]:
        """Get all receipts that failed processing."""
        pass 