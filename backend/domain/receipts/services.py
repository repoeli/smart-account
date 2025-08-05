"""
Domain services for receipt management.
Defines business logic and validation for receipt operations.
"""

import os
import mimetypes
from typing import List, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from domain.receipts.entities import (
    Receipt, FileInfo, OCRData, ReceiptMetadata, 
    ReceiptStatus, ReceiptType
)
from domain.accounts.entities import User


class FileValidationService:
    """Service for validating file uploads."""
    
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/jpg', 'image/png', 
        'application/pdf', 'image/tiff', 'image/bmp'
    }
    
    def validate_file(self, filename: str, file_size: int, mime_type: str) -> Tuple[bool, List[str]]:
        """Validate file upload."""
        errors = []
        
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            errors.append(f"File extension '{file_ext}' is not allowed. Allowed: {', '.join(self.ALLOWED_EXTENSIONS)}")
        
        # Check file size
        if file_size > self.MAX_FILE_SIZE:
            errors.append(f"File size {file_size} bytes exceeds maximum allowed size of {self.MAX_FILE_SIZE} bytes")
        
        # Check MIME type
        if mime_type not in self.ALLOWED_MIME_TYPES:
            errors.append(f"MIME type '{mime_type}' is not allowed. Allowed: {', '.join(self.ALLOWED_MIME_TYPES)}")
        
        return len(errors) == 0, errors
    
    def get_file_info(self, filename: str, file_size: int, mime_type: str, file_url: str) -> FileInfo:
        """Create FileInfo value object from file data."""
        return FileInfo(
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            file_url=file_url
        )


class ReceiptValidationService:
    """Service for validating receipt data."""
    
    def validate_ocr_data(self, ocr_data: OCRData) -> Tuple[bool, List[str]]:
        """Validate OCR extracted data."""
        errors = []
        
        # Validate total amount
        if ocr_data.total_amount is not None:
            if ocr_data.total_amount <= 0:
                errors.append("Total amount must be greater than zero")
            if ocr_data.total_amount > 999999.99:
                errors.append("Total amount seems unreasonably high")
        
        # Validate currency
        if ocr_data.currency not in ['GBP', 'USD', 'EUR']:
            errors.append(f"Currency '{ocr_data.currency}' is not supported")
        
        # Validate date
        if ocr_data.date is not None:
            if ocr_data.date > datetime.utcnow():
                errors.append("Receipt date cannot be in the future")
            if ocr_data.date < datetime(2020, 1, 1):
                errors.append("Receipt date seems too old")
        
        # Validate VAT amount
        if ocr_data.vat_amount is not None and ocr_data.total_amount is not None:
            if ocr_data.vat_amount > ocr_data.total_amount:
                errors.append("VAT amount cannot be greater than total amount")
        
        # Validate confidence score
        if ocr_data.confidence_score is not None:
            if not (0 <= ocr_data.confidence_score <= 1):
                errors.append("Confidence score must be between 0 and 1")
        
        return len(errors) == 0, errors
    
    def validate_metadata(self, metadata: ReceiptMetadata) -> Tuple[bool, List[str]]:
        """Validate receipt metadata."""
        errors = []
        
        # Validate category
        if metadata.category and len(metadata.category) > 100:
            errors.append("Category name is too long (max 100 characters)")
        
        # Validate tags
        if metadata.tags:
            for tag in metadata.tags:
                if len(tag) > 50:
                    errors.append(f"Tag '{tag}' is too long (max 50 characters)")
                if not tag.strip():
                    errors.append("Tags cannot be empty")
        
        # Validate notes
        if metadata.notes and len(metadata.notes) > 1000:
            errors.append("Notes are too long (max 1000 characters)")
        
        return len(errors) == 0, errors
    
    def validate_receipt_type(self, receipt_type: ReceiptType) -> bool:
        """Validate receipt type."""
        return receipt_type in ReceiptType


class ReceiptBusinessService:
    """Service for receipt business logic."""
    
    def calculate_vat_rate(self, total_amount: Decimal, vat_amount: Decimal) -> Optional[Decimal]:
        """Calculate VAT rate from total and VAT amounts."""
        if total_amount and vat_amount and total_amount > 0:
            return (vat_amount / (total_amount - vat_amount)) * 100
        return None
    
    def is_business_expense(self, receipt: Receipt) -> bool:
        """Determine if receipt is a business expense based on business rules."""
        if not receipt.ocr_data:
            return False
        
        # Business expense indicators
        business_keywords = [
            'office', 'stationery', 'equipment', 'travel', 'meals', 
            'software', 'subscription', 'professional', 'business'
        ]
        
        merchant_name = receipt.ocr_data.merchant_name or ""
        merchant_lower = merchant_name.lower()
        
        # Check if merchant name contains business keywords
        for keyword in business_keywords:
            if keyword in merchant_lower:
                return True
        
        # Check if amount is reasonable for business expense
        if receipt.ocr_data.total_amount:
            if receipt.ocr_data.total_amount > 1000:
                return True  # High amounts are likely business expenses
        
        return False
    
    def suggest_category(self, receipt: Receipt) -> Optional[str]:
        """Suggest category based on receipt data."""
        if not receipt.ocr_data or not receipt.ocr_data.merchant_name:
            return None
        
        merchant_name = receipt.ocr_data.merchant_name.lower()
        
        # Category mapping based on merchant names
        category_mapping = {
            'supermarket': ['tesco', 'sainsbury', 'asda', 'morrisons', 'waitrose', 'coop'],
            'restaurant': ['restaurant', 'cafe', 'pub', 'bar', 'takeaway', 'delivery'],
            'transport': ['uber', 'lyft', 'train', 'bus', 'taxi', 'parking'],
            'office': ['staples', 'office depot', 'amazon', 'dell', 'apple'],
            'utilities': ['british gas', 'edf', 'e.on', 'thames water', 'bt'],
            'entertainment': ['netflix', 'spotify', 'cinema', 'theatre', 'concert'],
            'health': ['boots', 'superdrug', 'pharmacy', 'doctor', 'dentist'],
            'clothing': ['next', 'h&m', 'zara', 'uniqlo', 'm&s', 'primark']
        }
        
        for category, keywords in category_mapping.items():
            for keyword in keywords:
                if keyword in merchant_name:
                    return category
        
        return 'other'
    
    def calculate_monthly_totals(self, receipts: List[Receipt]) -> dict:
        """Calculate monthly totals from receipts."""
        monthly_totals = {}
        
        for receipt in receipts:
            if receipt.ocr_data and receipt.ocr_data.date and receipt.ocr_data.total_amount:
                month_key = receipt.ocr_data.date.strftime('%Y-%m')
                if month_key not in monthly_totals:
                    monthly_totals[month_key] = Decimal('0')
                monthly_totals[month_key] += receipt.ocr_data.total_amount
        
        return monthly_totals
    
    def get_receipt_statistics(self, receipts: List[Receipt]) -> dict:
        """Get statistics from receipts."""
        if not receipts:
            return {
                'total_receipts': 0,
                'total_amount': Decimal('0'),
                'average_amount': Decimal('0'),
                'highest_amount': Decimal('0'),
                'lowest_amount': Decimal('0'),
                'processed_count': 0,
                'failed_count': 0
            }
        
        amounts = []
        processed_count = 0
        failed_count = 0
        
        for receipt in receipts:
            if receipt.ocr_data and receipt.ocr_data.total_amount:
                amounts.append(receipt.ocr_data.total_amount)
            
            if receipt.status == ReceiptStatus.PROCESSED:
                processed_count += 1
            elif receipt.status == ReceiptStatus.FAILED:
                failed_count += 1
        
        total_amount = sum(amounts) if amounts else Decimal('0')
        
        return {
            'total_receipts': len(receipts),
            'total_amount': total_amount,
            'average_amount': total_amount / len(amounts) if amounts else Decimal('0'),
            'highest_amount': max(amounts) if amounts else Decimal('0'),
            'lowest_amount': min(amounts) if amounts else Decimal('0'),
            'processed_count': processed_count,
            'failed_count': failed_count
        } 