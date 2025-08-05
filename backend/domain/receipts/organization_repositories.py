"""
Repository interfaces for receipt organization entities.
Defines abstract repositories for folders, tags, and collections.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Set

from domain.receipts.organization import Folder, Tag, ReceiptCollection, FolderType
from domain.accounts.entities import User


class FolderRepository(ABC):
    """Abstract repository for folder persistence."""
    
    @abstractmethod
    def save(self, folder: Folder) -> Folder:
        """Save or update a folder."""
        pass
    
    @abstractmethod
    def find_by_id(self, folder_id: str) -> Optional[Folder]:
        """Find folder by ID."""
        pass
    
    @abstractmethod
    def find_by_user(self, user_id: str) -> List[Folder]:
        """Find all folders for a user."""
        pass
    
    @abstractmethod
    def find_by_user_and_type(self, user_id: str, folder_type: FolderType) -> List[Folder]:
        """Find folders by user and type."""
        pass
    
    @abstractmethod
    def find_by_parent(self, parent_id: str) -> List[Folder]:
        """Find child folders of a parent."""
        pass
    
    @abstractmethod
    def find_system_folder(self, user_id: str, folder_name: str) -> Optional[Folder]:
        """Find a system folder by name for a user."""
        pass
    
    @abstractmethod
    def delete(self, folder_id: str) -> bool:
        """Delete a folder (hard delete)."""
        pass
    
    @abstractmethod
    def exists_by_name(self, user_id: str, name: str, parent_id: Optional[str] = None) -> bool:
        """Check if folder with name exists for user in parent."""
        pass


class TagRepository(ABC):
    """Abstract repository for tag persistence."""
    
    @abstractmethod
    def save(self, tag: Tag) -> Tag:
        """Save or update a tag."""
        pass
    
    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Tag]:
        """Find tag by name."""
        pass
    
    @abstractmethod
    def find_by_user_receipts(self, user_id: str) -> Set[Tag]:
        """Find all tags used in user's receipts."""
        pass
    
    @abstractmethod
    def find_popular_tags(self, limit: int = 20) -> List[Tag]:
        """Find most popular tags across all users."""
        pass
    
    @abstractmethod
    def delete(self, tag_name: str) -> bool:
        """Delete a tag."""
        pass
    
    @abstractmethod
    def merge_tags(self, source_tag: str, target_tag: str) -> int:
        """Merge source tag into target tag, returns affected count."""
        pass


class CollectionRepository(ABC):
    """Abstract repository for collection persistence."""
    
    @abstractmethod
    def save(self, collection: ReceiptCollection) -> ReceiptCollection:
        """Save or update a collection."""
        pass
    
    @abstractmethod
    def find_by_id(self, collection_id: str) -> Optional[ReceiptCollection]:
        """Find collection by ID."""
        pass
    
    @abstractmethod
    def find_by_user(self, user_id: str) -> List[ReceiptCollection]:
        """Find all collections created by user."""
        pass
    
    @abstractmethod
    def find_shared_with_user(self, user_id: str) -> List[ReceiptCollection]:
        """Find collections shared with user."""
        pass
    
    @abstractmethod
    def find_public_collections(self, limit: int = 50, offset: int = 0) -> List[ReceiptCollection]:
        """Find public collections."""
        pass
    
    @abstractmethod
    def delete(self, collection_id: str) -> bool:
        """Delete a collection."""
        pass
    
    @abstractmethod
    def add_receipt_to_collection(self, collection_id: str, receipt_id: str) -> bool:
        """Add receipt to collection."""
        pass
    
    @abstractmethod
    def remove_receipt_from_collection(self, collection_id: str, receipt_id: str) -> bool:
        """Remove receipt from collection."""
        pass