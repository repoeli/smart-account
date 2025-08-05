"""
Domain entities and value objects for receipt organization.
Supports folders, tags, and collections for managing receipts.
"""

from typing import List, Optional, Set, Any
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from domain.common.entities import Entity, ValueObject, AggregateRoot, DomainEvent


class FolderType(Enum):
    """Types of folders for organizing receipts."""
    SYSTEM = "system"      # System-created folders (e.g., Archive, Trash)
    USER = "user"          # User-created folders
    SMART = "smart"        # Smart folders with dynamic rules


@dataclass
class Tag(ValueObject):
    """Value object for receipt tags."""
    
    name: str
    color: Optional[str] = None
    
    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Tag name cannot be empty")
        self.name = self.name.strip().lower()
        if len(self.name) > 50:
            raise ValueError("Tag name cannot exceed 50 characters")
    
    def _get_equality_components(self) -> tuple:
        return (self.name,)
    
    def __hash__(self):
        return hash(self._get_equality_components())


@dataclass
class FolderMetadata(ValueObject):
    """Metadata for folders."""
    
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_favorite: bool = False
    sort_order: int = 0
    
    def _get_equality_components(self) -> tuple:
        return (
            self.description,
            self.icon,
            self.color,
            self.is_favorite,
            self.sort_order
        )


class SmartFolderRule(ValueObject):
    """Rules for smart folders that dynamically include receipts."""
    
    def __init__(self,
                 field: str,
                 operator: str,
                 value: Any,
                 combine_with: str = "AND"):
        self.field = field
        self.operator = operator
        self.value = value
        self.combine_with = combine_with
        self._validate()
    
    def _validate(self):
        """Validate smart folder rule."""
        valid_fields = [
            'merchant_name', 'total_amount', 'date', 'category',
            'tags', 'status', 'receipt_type', 'is_business_expense'
        ]
        valid_operators = [
            'equals', 'not_equals', 'contains', 'not_contains',
            'greater_than', 'less_than', 'between', 'in', 'not_in'
        ]
        valid_combiners = ['AND', 'OR']
        
        if self.field not in valid_fields:
            raise ValueError(f"Invalid field: {self.field}")
        if self.operator not in valid_operators:
            raise ValueError(f"Invalid operator: {self.operator}")
        if self.combine_with not in valid_combiners:
            raise ValueError(f"Invalid combiner: {self.combine_with}")
    
    def _get_equality_components(self) -> tuple:
        return (self.field, self.operator, self.value, self.combine_with)


class FolderCreatedEvent(DomainEvent):
    """Domain event for folder creation."""
    
    def __init__(self, folder_id: str, user_id: str, folder_name: str):
        super().__init__()
        self.folder_id = folder_id
        self.user_id = user_id
        self.folder_name = folder_name


class ReceiptMovedEvent(DomainEvent):
    """Domain event for receipt moved to folder."""
    
    def __init__(self, receipt_id: str, from_folder_id: Optional[str], to_folder_id: str):
        super().__init__()
        self.receipt_id = receipt_id
        self.from_folder_id = from_folder_id
        self.to_folder_id = to_folder_id


class Folder(AggregateRoot):
    """Folder aggregate for organizing receipts."""
    
    def __init__(self,
                 id: str,
                 user_id: str,
                 name: str,
                 folder_type: FolderType = FolderType.USER,
                 parent_id: Optional[str] = None,
                 metadata: Optional[FolderMetadata] = None,
                 smart_rules: Optional[List[SmartFolderRule]] = None):
        super().__init__(id)
        self.user_id = user_id
        self.name = name
        self.folder_type = folder_type
        self.parent_id = parent_id
        self.metadata = metadata or FolderMetadata()
        self.smart_rules = smart_rules or []
        self.receipt_ids: Set[str] = set()
        self._deleted = False
        
        # Add domain event
        self.add_domain_event(FolderCreatedEvent(
            folder_id=self.id,
            user_id=self.user_id,
            folder_name=self.name
        ))
    
    def add_receipt(self, receipt_id: str) -> None:
        """Add a receipt to this folder."""
        if self.folder_type == FolderType.SMART:
            raise ValueError("Cannot manually add receipts to smart folders")
        if receipt_id not in self.receipt_ids:
            self.receipt_ids.add(receipt_id)
            self._update_timestamp()
    
    def remove_receipt(self, receipt_id: str) -> None:
        """Remove a receipt from this folder."""
        if self.folder_type == FolderType.SMART:
            raise ValueError("Cannot manually remove receipts from smart folders")
        if receipt_id in self.receipt_ids:
            self.receipt_ids.discard(receipt_id)
            self._update_timestamp()
    
    def rename(self, new_name: str) -> None:
        """Rename the folder."""
        if self.folder_type == FolderType.SYSTEM:
            raise ValueError("Cannot rename system folders")
        if not new_name or not new_name.strip():
            raise ValueError("Folder name cannot be empty")
        self.name = new_name.strip()
        self._update_timestamp()
    
    def update_metadata(self, metadata: FolderMetadata) -> None:
        """Update folder metadata."""
        self.metadata = metadata
        self._update_timestamp()
    
    def add_smart_rule(self, rule: SmartFolderRule) -> None:
        """Add a smart folder rule."""
        if self.folder_type != FolderType.SMART:
            raise ValueError("Can only add rules to smart folders")
        self.smart_rules.append(rule)
        self._update_timestamp()
    
    def clear_smart_rules(self) -> None:
        """Clear all smart folder rules."""
        if self.folder_type != FolderType.SMART:
            raise ValueError("Can only clear rules from smart folders")
        self.smart_rules.clear()
        self._update_timestamp()
    
    def mark_as_deleted(self) -> None:
        """Mark folder as deleted (soft delete)."""
        if self.folder_type == FolderType.SYSTEM:
            raise ValueError("Cannot delete system folders")
        self._deleted = True
        self._update_timestamp()
    
    def is_deleted(self) -> bool:
        """Check if folder is deleted."""
        return self._deleted
    
    def get_receipt_count(self) -> int:
        """Get number of receipts in folder."""
        return len(self.receipt_ids)


class ReceiptCollection(AggregateRoot):
    """Collection aggregate for grouping related receipts."""
    
    def __init__(self,
                 id: str,
                 user_id: str,
                 name: str,
                 description: Optional[str] = None):
        super().__init__(id)
        self.user_id = user_id
        self.name = name
        self.description = description
        self.receipt_ids: Set[str] = set()
        self.tags: Set[Tag] = set()
        self.is_public = False
        self.shared_with: Set[str] = set()  # User IDs with access
    
    def add_receipt(self, receipt_id: str) -> None:
        """Add a receipt to the collection."""
        if receipt_id not in self.receipt_ids:
            self.receipt_ids.add(receipt_id)
            self._update_timestamp()
    
    def remove_receipt(self, receipt_id: str) -> None:
        """Remove a receipt from the collection."""
        if receipt_id in self.receipt_ids:
            self.receipt_ids.discard(receipt_id)
            self._update_timestamp()
    
    def add_tag(self, tag: Tag) -> None:
        """Add a tag to the collection."""
        self.tags.add(tag)
        self._update_timestamp()
    
    def remove_tag(self, tag: Tag) -> None:
        """Remove a tag from the collection."""
        self.tags.discard(tag)
        self._update_timestamp()
    
    def make_public(self) -> None:
        """Make collection publicly accessible."""
        self.is_public = True
        self._update_timestamp()
    
    def make_private(self) -> None:
        """Make collection private."""
        self.is_public = False
        self.shared_with.clear()
        self._update_timestamp()
    
    def share_with_user(self, user_id: str) -> None:
        """Share collection with specific user."""
        if user_id not in self.shared_with:
            self.shared_with.add(user_id)
            self._update_timestamp()
    
    def unshare_with_user(self, user_id: str) -> None:
        """Remove user's access to collection."""
        self.shared_with.discard(user_id)
        self._update_timestamp()
    
    def has_access(self, user_id: str) -> bool:
        """Check if user has access to collection."""
        return (
            self.user_id == user_id or
            self.is_public or
            user_id in self.shared_with
        )


class ReceiptSearchCriteria(ValueObject):
    """Search criteria for finding receipts."""
    
    def __init__(self,
                 query: Optional[str] = None,
                 merchant_names: Optional[List[str]] = None,
                 categories: Optional[List[str]] = None,
                 tags: Optional[List[str]] = None,
                 date_from: Optional[datetime] = None,
                 date_to: Optional[datetime] = None,
                 amount_min: Optional[Decimal] = None,
                 amount_max: Optional[Decimal] = None,
                 folder_ids: Optional[List[str]] = None,
                 receipt_types: Optional[List[str]] = None,
                 statuses: Optional[List[str]] = None,
                 is_business_expense: Optional[bool] = None):
        self.query = query
        self.merchant_names = merchant_names or []
        self.categories = categories or []
        self.tags = tags or []
        self.date_from = date_from
        self.date_to = date_to
        self.amount_min = amount_min
        self.amount_max = amount_max
        self.folder_ids = folder_ids or []
        self.receipt_types = receipt_types or []
        self.statuses = statuses or []
        self.is_business_expense = is_business_expense
    
    def _get_equality_components(self) -> tuple:
        return (
            self.query,
            tuple(self.merchant_names),
            tuple(self.categories),
            tuple(self.tags),
            self.date_from,
            self.date_to,
            self.amount_min,
            self.amount_max,
            tuple(self.folder_ids),
            tuple(self.receipt_types),
            tuple(self.statuses),
            self.is_business_expense
        )


class ReceiptSortOptions(ValueObject):
    """Sort options for receipt listings."""
    
    def __init__(self,
                 field: str = "date",
                 direction: str = "desc"):
        self.field = field
        self.direction = direction
        self._validate()
    
    def _validate(self):
        """Validate sort options."""
        valid_fields = [
            'date', 'amount', 'merchant_name', 'created_at',
            'updated_at', 'category'
        ]
        valid_directions = ['asc', 'desc']
        
        if self.field not in valid_fields:
            raise ValueError(f"Invalid sort field: {self.field}")
        if self.direction not in valid_directions:
            raise ValueError(f"Invalid sort direction: {self.direction}")
    
    def _get_equality_components(self) -> tuple:
        return (self.field, self.direction)