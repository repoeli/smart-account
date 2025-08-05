"""
Application use cases for receipt management and organization.
Orchestrates receipt organization, search, and bulk operations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal

from domain.receipts.entities import Receipt
from domain.receipts.organization import (
    Folder, Tag, ReceiptCollection, ReceiptSearchCriteria, 
    ReceiptSortOptions, FolderMetadata, FolderType
)
from domain.receipts.repositories import ReceiptRepository
from domain.receipts.organization_services import (
    FolderService, TagService, ReceiptSearchService, ReceiptBulkOperationService
)
from domain.accounts.entities import User


class CreateFolderUseCase:
    """Use case for creating a new folder."""
    
    def __init__(self, 
                 folder_repository: 'FolderRepository',
                 folder_service: FolderService):
        self.folder_repository = folder_repository
        self.folder_service = folder_service
    
    def execute(self,
                user: User,
                name: str,
                parent_id: Optional[str] = None,
                description: Optional[str] = None,
                icon: Optional[str] = None,
                color: Optional[str] = None) -> Dict[str, Any]:
        """Create a new folder."""
        try:
            # Create folder metadata
            metadata = FolderMetadata(
                description=description,
                icon=icon,
                color=color
            )
            
            # Generate folder ID
            import uuid
            folder_id = str(uuid.uuid4())
            
            # Create folder
            folder = Folder(
                id=folder_id,
                user_id=user.id,
                name=name,
                folder_type=FolderType.USER,
                parent_id=parent_id,
                metadata=metadata
            )
            
            # Validate hierarchy if parent is provided
            if parent_id:
                parent_folder = self.folder_repository.find_by_id(parent_id)
                if not parent_folder:
                    return {
                        'success': False,
                        'error': 'Parent folder not found'
                    }
                
                is_valid, error = self.folder_service.validate_folder_hierarchy(folder, parent_folder)
                if not is_valid:
                    return {
                        'success': False,
                        'error': error
                    }
            
            # Save folder
            saved_folder = self.folder_repository.save(folder)
            
            return {
                'success': True,
                'folder_id': saved_folder.id,
                'name': saved_folder.name,
                'message': 'Folder created successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create folder: {str(e)}'
            }


class MoveFolderUseCase:
    """Use case for moving a folder to a different parent."""
    
    def __init__(self,
                 folder_repository: 'FolderRepository',
                 folder_service: FolderService):
        self.folder_repository = folder_repository
        self.folder_service = folder_service
    
    def execute(self,
                user: User,
                folder_id: str,
                new_parent_id: Optional[str]) -> Dict[str, Any]:
        """Move folder to a new parent."""
        try:
            # Get folder
            folder = self.folder_repository.find_by_id(folder_id)
            if not folder:
                return {
                    'success': False,
                    'error': 'Folder not found'
                }
            
            # Check ownership
            if folder.user_id != user.id:
                return {
                    'success': False,
                    'error': 'Access denied'
                }
            
            # Check if it's a system folder
            if folder.folder_type == FolderType.SYSTEM:
                return {
                    'success': False,
                    'error': 'Cannot move system folders'
                }
            
            # Validate new parent
            new_parent = None
            if new_parent_id:
                new_parent = self.folder_repository.find_by_id(new_parent_id)
                if not new_parent:
                    return {
                        'success': False,
                        'error': 'New parent folder not found'
                    }
                
                is_valid, error = self.folder_service.validate_folder_hierarchy(folder, new_parent)
                if not is_valid:
                    return {
                        'success': False,
                        'error': error
                    }
            
            # Update folder
            folder.parent_id = new_parent_id
            self.folder_repository.save(folder)
            
            return {
                'success': True,
                'folder_id': folder_id,
                'message': 'Folder moved successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to move folder: {str(e)}'
            }


class SearchReceiptsUseCase:
    """Use case for searching receipts."""
    
    def __init__(self,
                 receipt_repository: ReceiptRepository,
                 search_service: ReceiptSearchService):
        self.receipt_repository = receipt_repository
        self.search_service = search_service
    
    def execute(self,
                user: User,
                query: Optional[str] = None,
                merchant_names: Optional[List[str]] = None,
                categories: Optional[List[str]] = None,
                tags: Optional[List[str]] = None,
                date_from: Optional[str] = None,
                date_to: Optional[str] = None,
                amount_min: Optional[float] = None,
                amount_max: Optional[float] = None,
                folder_ids: Optional[List[str]] = None,
                receipt_types: Optional[List[str]] = None,
                statuses: Optional[List[str]] = None,
                is_business_expense: Optional[bool] = None,
                sort_field: str = "date",
                sort_direction: str = "desc",
                limit: int = 50,
                offset: int = 0) -> Dict[str, Any]:
        """Search receipts based on criteria."""
        try:
            # Parse dates
            date_from_dt = datetime.fromisoformat(date_from) if date_from else None
            date_to_dt = datetime.fromisoformat(date_to) if date_to else None
            
            # Create search criteria
            criteria = ReceiptSearchCriteria(
                query=query,
                merchant_names=merchant_names,
                categories=categories,
                tags=tags,
                date_from=date_from_dt,
                date_to=date_to_dt,
                amount_min=Decimal(str(amount_min)) if amount_min else None,
                amount_max=Decimal(str(amount_max)) if amount_max else None,
                folder_ids=folder_ids,
                receipt_types=receipt_types,
                statuses=statuses,
                is_business_expense=is_business_expense
            )
            
            # Create sort options
            sort_options = ReceiptSortOptions(
                field=sort_field,
                direction=sort_direction
            )
            
            # Search receipts
            receipts, total_count = self.search_service.search_receipts(
                user_id=user.id,
                criteria=criteria,
                sort_options=sort_options,
                limit=limit,
                offset=offset
            )
            
            # Convert to response format
            receipt_list = []
            for receipt in receipts:
                receipt_data = {
                    'id': receipt.id,
                    'filename': receipt.file_info.filename,
                    'status': receipt.status.value,
                    'receipt_type': receipt.receipt_type.value,
                    'created_at': receipt.created_at.isoformat(),
                    'file_url': receipt.file_info.file_url
                }
                
                if receipt.ocr_data:
                    receipt_data['merchant_name'] = receipt.ocr_data.merchant_name
                    receipt_data['total_amount'] = str(receipt.ocr_data.total_amount) if receipt.ocr_data.total_amount else None
                    receipt_data['date'] = receipt.ocr_data.date.isoformat() if receipt.ocr_data.date else None
                
                if receipt.metadata:
                    receipt_data['category'] = receipt.metadata.category
                    receipt_data['tags'] = list(receipt.metadata.tags)
                    receipt_data['is_business_expense'] = receipt.metadata.is_business_expense
                
                receipt_list.append(receipt_data)
            
            return {
                'success': True,
                'receipts': receipt_list,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Search failed: {str(e)}'
            }


class AddTagsToReceiptUseCase:
    """Use case for adding tags to a receipt."""
    
    def __init__(self,
                 receipt_repository: ReceiptRepository,
                 tag_service: TagService):
        self.receipt_repository = receipt_repository
        self.tag_service = tag_service
    
    def execute(self,
                user: User,
                receipt_id: str,
                tag_names: List[str]) -> Dict[str, Any]:
        """Add tags to a receipt."""
        try:
            # Get receipt
            receipt = self.receipt_repository.find_by_id(receipt_id)
            if not receipt:
                return {
                    'success': False,
                    'error': 'Receipt not found'
                }
            
            # Check ownership
            if receipt.user.id != user.id:
                return {
                    'success': False,
                    'error': 'Access denied'
                }
            
            # Create and validate tags
            tags_added = []
            for tag_name in tag_names:
                normalized_name = self.tag_service.normalize_tag_name(tag_name)
                tag = Tag(name=normalized_name)
                
                is_valid, error = self.tag_service.validate_tag(tag)
                if not is_valid:
                    continue
                
                if receipt.metadata and tag not in receipt.metadata.tags:
                    receipt.metadata.tags.add(tag)
                    tags_added.append(tag.name)
            
            # Save receipt
            self.receipt_repository.save(receipt)
            
            return {
                'success': True,
                'receipt_id': receipt_id,
                'tags_added': tags_added,
                'message': f'Added {len(tags_added)} tags'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to add tags: {str(e)}'
            }


class BulkOperationUseCase:
    """Use case for bulk operations on receipts."""
    
    def __init__(self,
                 receipt_repository: ReceiptRepository,
                 bulk_service: ReceiptBulkOperationService):
        self.receipt_repository = receipt_repository
        self.bulk_service = bulk_service
    
    def execute(self,
                user: User,
                receipt_ids: List[str],
                operation: str,
                params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bulk operation on receipts."""
        try:
            # Get receipts
            receipts = []
            for receipt_id in receipt_ids:
                receipt = self.receipt_repository.find_by_id(receipt_id)
                if receipt and receipt.user.id == user.id:
                    receipts.append(receipt)
            
            if not receipts:
                return {
                    'success': False,
                    'error': 'No valid receipts found'
                }
            
            # Execute operation
            count = 0
            
            if operation == 'add_tags':
                tags = [Tag(name=name) for name in params.get('tags', [])]
                count = self.bulk_service.bulk_add_tags(receipts, tags)
                
            elif operation == 'remove_tags':
                tags = [Tag(name=name) for name in params.get('tags', [])]
                count = self.bulk_service.bulk_remove_tags(receipts, tags)
                
            elif operation == 'categorize':
                category = params.get('category')
                if category:
                    count = self.bulk_service.bulk_categorize(receipts, category)
                    
            elif operation == 'mark_business':
                is_business = params.get('is_business', True)
                count = self.bulk_service.bulk_mark_as_business(receipts, is_business)
                
            elif operation == 'archive':
                count = self.bulk_service.bulk_archive(receipts)
                
            elif operation == 'delete':
                count = self.bulk_service.bulk_delete(receipts)
                
            else:
                return {
                    'success': False,
                    'error': f'Unknown operation: {operation}'
                }
            
            # Save all receipts
            for receipt in receipts:
                self.receipt_repository.save(receipt)
            
            return {
                'success': True,
                'operation': operation,
                'affected_count': count,
                'total_receipts': len(receipts),
                'message': f'{operation} completed on {count} items'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Bulk operation failed: {str(e)}'
            }


class MoveReceiptsToFolderUseCase:
    """Use case for moving receipts to a folder."""
    
    def __init__(self,
                 receipt_repository: ReceiptRepository,
                 folder_repository: 'FolderRepository',
                 bulk_service: ReceiptBulkOperationService):
        self.receipt_repository = receipt_repository
        self.folder_repository = folder_repository
        self.bulk_service = bulk_service
    
    def execute(self,
                user: User,
                receipt_ids: List[str],
                folder_id: str) -> Dict[str, Any]:
        """Move receipts to a folder."""
        try:
            # Get folder
            folder = self.folder_repository.find_by_id(folder_id)
            if not folder:
                return {
                    'success': False,
                    'error': 'Folder not found'
                }
            
            # Check ownership
            if folder.user_id != user.id:
                return {
                    'success': False,
                    'error': 'Access denied'
                }
            
            # Check if it's a smart folder
            if folder.folder_type == FolderType.SMART:
                return {
                    'success': False,
                    'error': 'Cannot manually add receipts to smart folders'
                }
            
            # Move receipts
            count = self.bulk_service.bulk_move_to_folder(receipt_ids, folder)
            
            # Save folder
            self.folder_repository.save(folder)
            
            return {
                'success': True,
                'folder_id': folder_id,
                'moved_count': count,
                'message': f'Moved {count} receipts to {folder.name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to move receipts: {str(e)}'
            }


class GetUserStatisticsUseCase:
    """Use case for getting user receipt statistics."""
    
    def __init__(self, receipt_repository: ReceiptRepository):
        self.receipt_repository = receipt_repository
    
    def execute(self, user: User) -> Dict[str, Any]:
        """Get comprehensive statistics for user's receipts."""
        try:
            # Get all user receipts
            receipts = self.receipt_repository.find_by_user(user, limit=10000, offset=0)
            
            # Basic counts
            total_receipts = len(receipts)
            
            # Status breakdown
            status_counts = {}
            for receipt in receipts:
                status = receipt.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Type breakdown
            type_counts = {}
            for receipt in receipts:
                receipt_type = receipt.receipt_type.value
                type_counts[receipt_type] = type_counts.get(receipt_type, 0) + 1
            
            # Monthly breakdown
            monthly_counts = {}
            monthly_amounts = {}
            
            for receipt in receipts:
                if receipt.ocr_data and receipt.ocr_data.date:
                    month_key = receipt.ocr_data.date.strftime('%Y-%m')
                    monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
                    
                    if receipt.ocr_data.total_amount:
                        monthly_amounts[month_key] = monthly_amounts.get(month_key, Decimal('0')) + receipt.ocr_data.total_amount
            
            # Category breakdown
            category_counts = {}
            category_amounts = {}
            
            for receipt in receipts:
                if receipt.metadata and receipt.metadata.category:
                    category = receipt.metadata.category
                    category_counts[category] = category_counts.get(category, 0) + 1
                    
                    if receipt.ocr_data and receipt.ocr_data.total_amount:
                        category_amounts[category] = category_amounts.get(category, Decimal('0')) + receipt.ocr_data.total_amount
            
            # Calculate totals
            total_amount = Decimal('0')
            business_amount = Decimal('0')
            personal_amount = Decimal('0')
            
            for receipt in receipts:
                if receipt.ocr_data and receipt.ocr_data.total_amount:
                    total_amount += receipt.ocr_data.total_amount
                    
                    if receipt.metadata and receipt.metadata.is_business_expense:
                        business_amount += receipt.ocr_data.total_amount
                    else:
                        personal_amount += receipt.ocr_data.total_amount
            
            # Top merchants
            merchant_counts = {}
            merchant_amounts = {}
            
            for receipt in receipts:
                if receipt.ocr_data and receipt.ocr_data.merchant_name:
                    merchant = receipt.ocr_data.merchant_name
                    merchant_counts[merchant] = merchant_counts.get(merchant, 0) + 1
                    
                    if receipt.ocr_data.total_amount:
                        merchant_amounts[merchant] = merchant_amounts.get(merchant, Decimal('0')) + receipt.ocr_data.total_amount
            
            # Sort top merchants by amount
            top_merchants = sorted(
                merchant_amounts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return {
                'success': True,
                'statistics': {
                    'total_receipts': total_receipts,
                    'status_breakdown': status_counts,
                    'type_breakdown': type_counts,
                    'monthly_counts': monthly_counts,
                    'monthly_amounts': {k: str(v) for k, v in monthly_amounts.items()},
                    'category_counts': category_counts,
                    'category_amounts': {k: str(v) for k, v in category_amounts.items()},
                    'total_amount': str(total_amount),
                    'business_amount': str(business_amount),
                    'personal_amount': str(personal_amount),
                    'top_merchants': [
                        {
                            'name': name,
                            'count': merchant_counts[name],
                            'total_amount': str(amount)
                        }
                        for name, amount in top_merchants
                    ]
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to get statistics: {str(e)}'
            }