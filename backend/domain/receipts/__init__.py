"""
Receipt domain module for Smart Accounts Management System.
"""

from .entities import (
    Receipt,
    ReceiptStatus,
    ReceiptType,
    FileInfo,
    OCRData,
    ReceiptMetadata,
    ReceiptUploadedEvent,
    ReceiptProcessedEvent
)
from .repositories import ReceiptRepository
from .services import (
    FileValidationService,
    ReceiptDataEnrichmentService,
    ReceiptValidationService,
    ReceiptBusinessService,
    ExpenseCategory,
    ExpenseType,
    VATRate
)
from .organization import (
    Folder,
    FolderType,
    FolderMetadata,
    Tag,
    ReceiptCollection,
    ReceiptSearchCriteria,
    ReceiptSortOptions,
    SmartFolderRule
)
from .organization_services import (
    FolderService,
    TagService,
    ReceiptSearchService,
    ReceiptBulkOperationService
)
from .organization_repositories import (
    FolderRepository,
    TagRepository,
    CollectionRepository
)

__all__ = [
    # Entities
    'Receipt',
    'ReceiptStatus',
    'ReceiptType',
    'FileInfo',
    'OCRData',
    'ReceiptMetadata',
    'ReceiptUploadedEvent',
    'ReceiptProcessedEvent',
    # Organization entities
    'Folder',
    'FolderType',
    'FolderMetadata',
    'Tag',
    'ReceiptCollection',
    'ReceiptSearchCriteria',
    'ReceiptSortOptions',
    'SmartFolderRule',
    # Repositories
    'ReceiptRepository',
    'FolderRepository',
    'TagRepository',
    'CollectionRepository',
    # Services
    'FileValidationService',
    'ReceiptDataEnrichmentService',
    'ReceiptValidationService',
    'ReceiptBusinessService',
    'ExpenseCategory',
    'ExpenseType',
    'VATRate',
    # Organization services
    'FolderService',
    'TagService',
    'ReceiptSearchService',
    'ReceiptBulkOperationService'
] 