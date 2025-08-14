"""
Domain services for receipt organization and management.
Provides business logic for folders, tags, search, and bulk operations.
"""

from typing import List, Dict, Set, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal

from domain.receipts.entities import Receipt, ReceiptStatus, ReceiptType
from domain.receipts.organization import (
    Folder, FolderType, FolderMetadata, Tag, ReceiptCollection,
    ReceiptSearchCriteria, ReceiptSortOptions, SmartFolderRule
)
from domain.receipts.repositories import ReceiptRepository


class FolderService:
    """Service for managing receipt folders."""
    
    SYSTEM_FOLDERS = {
        'all': 'All Receipts',
        'recent': 'Recent',
        'archive': 'Archive',
        'trash': 'Trash',
        'uncategorized': 'Uncategorized',
        'business': 'Business Expenses',
        'personal': 'Personal Expenses'
    }
    
    def create_default_folders(self, user_id: str) -> List[Folder]:
        """Create default system folders for a new user."""
        import uuid
        folders = []

        for folder_key, folder_name in self.SYSTEM_FOLDERS.items():
            folder = Folder(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=folder_name,
                folder_type=FolderType.SYSTEM,
                metadata=FolderMetadata(
                    description=f"System folder: {folder_name}",
                    is_favorite=folder_key in ['all', 'recent']
                )
            )
            folders.append(folder)

        # Create smart folder for recent receipts (find by name, not id)
        recent_folder = next(f for f in folders if f.name.lower() == 'recent')
        recent_folder.folder_type = FolderType.SMART
        recent_folder.add_smart_rule(SmartFolderRule(
            field='date',
            operator='greater_than',
            value=(datetime.now().timestamp() - 30 * 24 * 60 * 60)  # Last 30 days
        ))
        
        return folders
    
    def validate_folder_hierarchy(self, folder: Folder, parent_folder: Optional[Folder]) -> Tuple[bool, Optional[str]]:
        """Validate folder hierarchy to prevent circular references."""
        if not parent_folder:
            return True, None
        
        if folder.id == parent_folder.id:
            return False, "Cannot set folder as its own parent"
        
        # Check if parent is a descendant of the folder
        # (In real implementation, would need to traverse the hierarchy)
        
        return True, None
    
    def can_delete_folder(self, folder: Folder) -> Tuple[bool, Optional[str]]:
        """Check if folder can be deleted."""
        if folder.folder_type == FolderType.SYSTEM:
            return False, "Cannot delete system folders"
        
        if folder.is_deleted():
            return False, "Folder is already deleted"
        
        return True, None
    
    def apply_smart_folder_rules(self, folder: Folder, receipts: List[Receipt]) -> List[Receipt]:
        """Apply smart folder rules to filter receipts."""
        if folder.folder_type != FolderType.SMART or not folder.smart_rules:
            return receipts
        
        filtered_receipts = []
        
        for receipt in receipts:
            matches = True
            
            for rule in folder.smart_rules:
                if not self._evaluate_rule(rule, receipt):
                    if rule.combine_with == "AND":
                        matches = False
                        break
                elif rule.combine_with == "OR" and matches:
                    break
            
            if matches:
                filtered_receipts.append(receipt)
        
        return filtered_receipts
    
    def _evaluate_rule(self, rule: SmartFolderRule, receipt: Receipt) -> bool:
        """Evaluate a single smart folder rule against a receipt."""
        # Get the field value from receipt
        field_value = self._get_field_value(receipt, rule.field)
        
        # Apply operator
        if rule.operator == 'equals':
            return field_value == rule.value
        elif rule.operator == 'not_equals':
            return field_value != rule.value
        elif rule.operator == 'contains':
            return rule.value in str(field_value).lower()
        elif rule.operator == 'not_contains':
            return rule.value not in str(field_value).lower()
        elif rule.operator == 'greater_than':
            return field_value > rule.value
        elif rule.operator == 'less_than':
            return field_value < rule.value
        elif rule.operator == 'between':
            return rule.value[0] <= field_value <= rule.value[1]
        elif rule.operator == 'in':
            return field_value in rule.value
        elif rule.operator == 'not_in':
            return field_value not in rule.value
        
        return False
    
    def _get_field_value(self, receipt: Receipt, field: str) -> Any:
        """Get field value from receipt for rule evaluation."""
        if field == 'merchant_name':
            return receipt.get_merchant_name() or ''
        elif field == 'total_amount':
            return receipt.get_total_amount() or Decimal('0')
        elif field == 'date':
            return receipt.get_receipt_date() or receipt.created_at
        elif field == 'category':
            return receipt.metadata.category if receipt.metadata else ''
        elif field == 'tags':
            return receipt.metadata.tags if receipt.metadata else []
        elif field == 'status':
            return receipt.status.value
        elif field == 'receipt_type':
            return receipt.receipt_type.value
        elif field == 'is_business_expense':
            return receipt.metadata.is_business_expense if receipt.metadata else False
        
        return None


class TagService:
    """Service for managing receipt tags."""
    
    def normalize_tag_name(self, tag_name: str) -> str:
        """Normalize tag name for consistency."""
        return tag_name.strip().lower().replace(' ', '-')
    
    def validate_tag(self, tag: Tag) -> Tuple[bool, Optional[str]]:
        """Validate a tag."""
        if not tag.name:
            return False, "Tag name cannot be empty"
        
        if len(tag.name) > 50:
            return False, "Tag name cannot exceed 50 characters"
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', '#', '?', '&']
        for char in invalid_chars:
            if char in tag.name:
                return False, f"Tag name cannot contain '{char}'"
        
        return True, None
    
    def merge_tags(self, source_tag: Tag, target_tag: Tag, receipts: List[Receipt]) -> int:
        """Merge source tag into target tag."""
        count = 0
        
        for receipt in receipts:
            if receipt.metadata and source_tag in receipt.metadata.tags:
                receipt.metadata.tags.remove(source_tag)
                receipt.metadata.tags.add(target_tag)
                count += 1
        
        return count
    
    def suggest_tags(self, receipt: Receipt, existing_tags: Set[Tag]) -> List[Tag]:
        """Suggest tags based on receipt content."""
        suggestions = []
        
        # Suggest based on merchant name
        if receipt.get_merchant_name():
            merchant_tag = Tag(name=self.normalize_tag_name(receipt.get_merchant_name()))
            if merchant_tag in existing_tags:
                suggestions.append(merchant_tag)
        
        # Suggest based on category
        if receipt.metadata and receipt.metadata.category:
            category_tag = Tag(name=self.normalize_tag_name(receipt.metadata.category))
            if category_tag in existing_tags:
                suggestions.append(category_tag)
        
        # Suggest based on amount ranges
        amount = receipt.get_total_amount()
        if amount:
            if amount < Decimal('10'):
                suggestions.append(Tag(name='small-purchase'))
            elif amount > Decimal('100'):
                suggestions.append(Tag(name='large-purchase'))
        
        return suggestions[:5]  # Return top 5 suggestions


class ReceiptSearchService:
    """Service for searching and filtering receipts."""
    
    def __init__(self, receipt_repository: ReceiptRepository):
        self.receipt_repository = receipt_repository
    
    def search_receipts(self, 
                       user_id: str,
                       criteria: ReceiptSearchCriteria,
                       sort_options: ReceiptSortOptions,
                       limit: int = 50,
                       offset: int = 0) -> Tuple[List[Receipt], int]:
        """Search receipts based on criteria."""
        # This is a simplified implementation
        # In real implementation, this would delegate to repository with proper query building
        
        # Get all user receipts (repository accepts user object or id)
        all_receipts = self.receipt_repository.find_by_user(user_id, limit=1000, offset=0)
        
        # Apply filters
        filtered_receipts = self._apply_filters(all_receipts, criteria)
        
        # Apply sorting
        sorted_receipts = self._apply_sorting(filtered_receipts, sort_options)
        
        # Apply pagination
        total_count = len(sorted_receipts)
        paginated_receipts = sorted_receipts[offset:offset + limit]
        
        return paginated_receipts, total_count
    
    def _apply_filters(self, receipts: List[Receipt], criteria: ReceiptSearchCriteria) -> List[Receipt]:
        """Apply search filters to receipts."""
        filtered = receipts
        
        # Text search
        if criteria.query:
            query_lower = criteria.query.lower()
            filtered = [r for r in filtered if self._matches_query(r, query_lower)]
        
        # Merchant filter
        if criteria.merchant_names:
            filtered = [r for r in filtered if r.get_merchant_name() in criteria.merchant_names]
        
        # Category filter
        if criteria.categories:
            filtered = [r for r in filtered if r.metadata and r.metadata.category in criteria.categories]
        
        # Date range filter
        if criteria.date_from:
            filtered = [r for r in filtered if r.get_receipt_date() and r.get_receipt_date() >= criteria.date_from]
        if criteria.date_to:
            filtered = [r for r in filtered if r.get_receipt_date() and r.get_receipt_date() <= criteria.date_to]
        
        # Amount range filter
        if criteria.amount_min:
            filtered = [r for r in filtered if r.get_total_amount() and r.get_total_amount() >= criteria.amount_min]
        if criteria.amount_max:
            filtered = [r for r in filtered if r.get_total_amount() and r.get_total_amount() <= criteria.amount_max]
        
        # Status filter
        if criteria.statuses:
            filtered = [r for r in filtered if r.status.value in criteria.statuses]
        
        # Receipt type filter
        if criteria.receipt_types:
            filtered = [r for r in filtered if r.receipt_type.value in criteria.receipt_types]
        
        # Business expense filter
        if criteria.is_business_expense is not None:
            filtered = [r for r in filtered if r.metadata and r.metadata.is_business_expense == criteria.is_business_expense]
        
        return filtered
    
    def _matches_query(self, receipt: Receipt, query: str) -> bool:
        """Check if receipt matches search query."""
        # Search in merchant name
        if receipt.get_merchant_name() and query in receipt.get_merchant_name().lower():
            return True
        
        # Search in receipt number
        if receipt.ocr_data and receipt.ocr_data.receipt_number and query in receipt.ocr_data.receipt_number.lower():
            return True
        
        # Search in notes
        if receipt.metadata and receipt.metadata.notes and query in receipt.metadata.notes.lower():
            return True
        
        # Search in raw OCR text
        if receipt.ocr_data and receipt.ocr_data.raw_text and query in receipt.ocr_data.raw_text.lower():
            return True
        
        return False
    
    def _apply_sorting(self, receipts: List[Receipt], sort_options: ReceiptSortOptions) -> List[Receipt]:
        """Apply sorting to receipts with None-safe keys to avoid TypeError."""
        reverse = sort_options.direction == 'desc'
        
        if sort_options.field == 'date':
            # Sort by receipt date; if None, fall back to created_at; place None at end
            return sorted(
                receipts,
                key=lambda r: (
                    (r.get_receipt_date() or r.created_at) is None,
                    (r.get_receipt_date() or r.created_at or datetime.min)
                ),
                reverse=reverse
            )
        elif sort_options.field == 'amount':
            return sorted(receipts, key=lambda r: r.get_total_amount() or Decimal('0'), reverse=reverse)
        elif sort_options.field == 'merchant_name':
            return sorted(receipts, key=lambda r: r.get_merchant_name() or '', reverse=reverse)
        elif sort_options.field == 'created_at':
            return sorted(receipts, key=lambda r: r.created_at or datetime.min, reverse=reverse)
        elif sort_options.field == 'updated_at':
            return sorted(receipts, key=lambda r: r.updated_at or datetime.min, reverse=reverse)
        elif sort_options.field == 'category':
            return sorted(receipts, key=lambda r: (r.metadata.category if r.metadata else ''), reverse=reverse)
        
        return receipts


class ReceiptBulkOperationService:
    """Service for bulk operations on receipts."""
    
    def __init__(self, receipt_repository: ReceiptRepository):
        self.receipt_repository = receipt_repository
    
    def bulk_move_to_folder(self, receipt_ids: List[str], folder: Folder) -> int:
        """Move multiple receipts to a folder."""
        count = 0
        
        for receipt_id in receipt_ids:
            if receipt_id not in folder.receipt_ids:
                folder.add_receipt(receipt_id)
                count += 1
        
        return count
    
    def bulk_add_tags(self, receipts: List[Receipt], tags: List[Tag]) -> int:
        """Add tags to multiple receipts."""
        count = 0
        
        for receipt in receipts:
            if receipt.metadata:
                for tag in tags:
                    if tag not in receipt.metadata.tags:
                        receipt.metadata.tags.add(tag)
                        count += 1
        
        return count
    
    def bulk_remove_tags(self, receipts: List[Receipt], tags: List[Tag]) -> int:
        """Remove tags from multiple receipts."""
        count = 0
        
        for receipt in receipts:
            if receipt.metadata:
                for tag in tags:
                    if tag in receipt.metadata.tags:
                        receipt.metadata.tags.remove(tag)
                        count += 1
        
        return count
    
    def bulk_categorize(self, receipts: List[Receipt], category: str) -> int:
        """Set category for multiple receipts."""
        count = 0
        
        for receipt in receipts:
            if receipt.metadata:
                receipt.metadata.category = category
                count += 1
        
        return count
    
    def bulk_mark_as_business(self, receipts: List[Receipt], is_business: bool) -> int:
        """Mark multiple receipts as business/personal expense."""
        count = 0
        
        for receipt in receipts:
            if receipt.metadata:
                receipt.metadata.is_business_expense = is_business
                count += 1
        
        return count
    
    def bulk_archive(self, receipts: List[Receipt]) -> int:
        """Archive multiple receipts."""
        count = 0
        
        for receipt in receipts:
            if receipt.status != ReceiptStatus.ARCHIVED:
                receipt.archive()
                count += 1
        
        return count
    
    def bulk_delete(self, receipts: List[Receipt]) -> int:
        """Delete multiple receipts."""
        count = 0
        
        for receipt in receipts:
            # Soft delete by marking as failed
            receipt.mark_as_failed("Deleted by user")
            count += 1
        
        return count