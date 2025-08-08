"""
Domain entities for receipt management.
Defines the Receipt aggregate root and related value objects.
"""

from typing import Optional, List, Dict, Any, Set, Union
from datetime import datetime
from decimal import Decimal
from enum import Enum

from domain.common.entities import Entity, AggregateRoot, ValueObject, DomainEvent
from domain.accounts.entities import User


class ReceiptStatus(Enum):
    """Receipt processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    ARCHIVED = "archived"


class ReceiptType(Enum):
    """Types of receipts."""
    PURCHASE = "purchase"
    EXPENSE = "expense"
    INVOICE = "invoice"
    BILL = "bill"
    OTHER = "other"


class FileInfo(ValueObject):
    """Value object for file information."""
    
    def __init__(self, filename: str, file_size: int, mime_type: str, file_url: str):
        self.filename = filename
        self.file_size = file_size
        self.mime_type = mime_type
        self.file_url = file_url
    
    def __eq__(self, other):
        if not isinstance(other, FileInfo):
            return False
        return (self.filename == other.filename and
                self.file_size == other.file_size and
                self.mime_type == other.mime_type and
                self.file_url == other.file_url)
    
    def __hash__(self):
        return hash((self.filename, self.file_size, self.mime_type, self.file_url))


class OCRData(ValueObject):
    """Value object for OCR extracted data."""
    
    def __init__(self, 
                 merchant_name: Optional[str] = None,
                 total_amount: Optional[Decimal] = None,
                 currency: str = "GBP",
                 date: Optional[datetime] = None,
                 vat_amount: Optional[Decimal] = None,
                 vat_number: Optional[str] = None,
                 receipt_number: Optional[str] = None,
                 items: Optional[List[Dict[str, Any]]] = None,
                 confidence_score: Optional[float] = None,
                 raw_text: Optional[str] = None,
                 additional_data: Optional[Dict[str, Any]] = None):
        self.merchant_name = merchant_name
        self.total_amount = total_amount
        self.currency = currency
        self.date = date
        self.vat_amount = vat_amount
        self.vat_number = vat_number
        self.receipt_number = receipt_number
        self.items = items or []
        self.confidence_score = confidence_score
        self.raw_text = raw_text
        self.additional_data = additional_data or {}
    
    def __eq__(self, other):
        if not isinstance(other, OCRData):
            return False
        return (self.merchant_name == other.merchant_name and
                self.total_amount == other.total_amount and
                self.currency == other.currency and
                self.date == other.date and
                self.vat_amount == other.vat_amount and
                self.vat_number == other.vat_number and
                self.receipt_number == other.receipt_number and
                self.items == other.items and
                self.confidence_score == other.confidence_score and
                self.raw_text == other.raw_text and
                self.additional_data == other.additional_data)
    
    def _get_equality_components(self) -> tuple:
        """Return components used for equality comparison."""
        return (
            self.merchant_name,
            self.total_amount,
            self.currency,
            self.date,
            self.vat_amount,
            self.vat_number,
            self.receipt_number,
            tuple(self.items) if self.items else None,
            self.confidence_score,
            self.raw_text,
            tuple(sorted(self.additional_data.items())) if self.additional_data else None
        )
    
    def __hash__(self):
        return hash(self._get_equality_components())


class ReceiptMetadata(ValueObject):
    """Value object for receipt metadata."""
    
    def __init__(self,
                 category: Optional[str] = None,
                 tags: Optional[Union[List[str], Set[str]]] = None,
                 notes: Optional[str] = None,
                 is_business_expense: bool = False,
                 tax_deductible: bool = False,
                 custom_fields: Optional[Dict[str, Any]] = None):
        self.category = category
        # Convert tags to set if provided as list
        if tags is None:
            self.tags = set()
        elif isinstance(tags, list):
            self.tags = set(tags)
        else:
            self.tags = tags
        self.notes = notes
        self.is_business_expense = is_business_expense
        self.tax_deductible = tax_deductible
        self.custom_fields = custom_fields or {}
    
    def __eq__(self, other):
        if not isinstance(other, ReceiptMetadata):
            return False
        return (self.category == other.category and
                self.tags == other.tags and
                self.notes == other.notes and
                self.is_business_expense == other.is_business_expense and
                self.tax_deductible == other.tax_deductible and
                self.custom_fields == other.custom_fields)
    
    def _get_equality_components(self) -> tuple:
        """Return components used for equality comparison."""
        return (
            self.category,
            tuple(self.tags),
            self.notes,
            self.is_business_expense,
            self.tax_deductible,
            tuple(sorted(self.custom_fields.items())) if self.custom_fields else ()
        )
    
    def __hash__(self):
        return hash(self._get_equality_components())


class ReceiptUploadedEvent(DomainEvent):
    """Domain event for receipt upload."""
    
    def __init__(self, receipt_id: str, user_id: str, file_info: FileInfo):
        super().__init__()
        self.receipt_id = receipt_id
        self.user_id = user_id
        self.file_info = file_info


class ReceiptProcessedEvent(DomainEvent):
    """Domain event for receipt processing completion."""
    
    def __init__(self, receipt_id: str, ocr_data: OCRData, status: ReceiptStatus):
        super().__init__()
        self.receipt_id = receipt_id
        self.ocr_data = ocr_data
        self.status = status


class Receipt(AggregateRoot):
    """Receipt aggregate root."""
    
    def __init__(self,
                 id: str,
                 user: User,
                 file_info: FileInfo,
                 status: ReceiptStatus = ReceiptStatus.UPLOADED,
                 receipt_type: ReceiptType = ReceiptType.PURCHASE,
                 ocr_data: Optional[OCRData] = None,
                 metadata: Optional[ReceiptMetadata] = None,
                 processed_at: Optional[datetime] = None):
        super().__init__(id)
        self.user = user
        self.file_info = file_info
        self.status = status
        self.receipt_type = receipt_type
        self.ocr_data = ocr_data
        self.metadata = metadata or ReceiptMetadata()
        self._processed_at = processed_at
        
        # Add domain event for receipt creation
        self.add_domain_event(ReceiptUploadedEvent(
            receipt_id=self.id,
            user_id=self.user.id,
            file_info=self.file_info
        ))
    
    @property
    def processed_at(self) -> Optional[datetime]:
        """Get the processed timestamp."""
        return self._processed_at
    
    @processed_at.setter
    def processed_at(self, value: Optional[datetime]) -> None:
        """Set the processed timestamp."""
        self._processed_at = value
    
    def process_ocr_data(self, ocr_data: OCRData) -> None:
        """Process OCR data and update receipt status."""
        self.ocr_data = ocr_data
        self.status = ReceiptStatus.PROCESSED
        self.processed_at = datetime.utcnow()
        self._update_timestamp()
        
        # Add domain event for processing completion
        self.add_domain_event(ReceiptProcessedEvent(
            receipt_id=self.id,
            ocr_data=self.ocr_data,
            status=self.status
        ))
    
    def update_metadata(self, metadata: ReceiptMetadata) -> None:
        """Update receipt metadata."""
        self.metadata = metadata
        self._update_timestamp()
    
    def mark_as_failed(self, error_message: str) -> None:
        """Mark receipt processing as failed."""
        self.status = ReceiptStatus.FAILED
        self._update_timestamp()
        # Could add error_message to metadata or create separate field
    
    def archive(self) -> None:
        """Archive the receipt."""
        self.status = ReceiptStatus.ARCHIVED
        self._update_timestamp()
    
    def get_merchant_name(self) -> Optional[str]:
        """Get merchant name from OCR data."""
        return self.ocr_data.merchant_name if self.ocr_data else None
    
    def get_total_amount(self) -> Optional[Decimal]:
        """Get total amount from OCR data."""
        return self.ocr_data.total_amount if self.ocr_data else None
    
    def get_receipt_date(self) -> Optional[datetime]:
        """Get receipt date from OCR data."""
        return self.ocr_data.date if self.ocr_data else None
    
    def is_processed(self) -> bool:
        """Check if receipt has been processed."""
        return self.status == ReceiptStatus.PROCESSED
    
    def is_failed(self) -> bool:
        """Check if receipt processing failed."""
        return self.status == ReceiptStatus.FAILED
    
    def get_total_amount(self) -> Optional[Decimal]:
        """Get total amount from OCR data."""
        return self.ocr_data.total_amount if self.ocr_data else None
    
    def get_merchant_name(self) -> Optional[str]:
        """Get merchant name from OCR data."""
        return self.ocr_data.merchant_name if self.ocr_data else None
    
    def get_receipt_date(self) -> Optional[datetime]:
        """Get receipt date from OCR data."""
        return self.ocr_data.date if self.ocr_data else None 