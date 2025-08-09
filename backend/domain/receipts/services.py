"""
Domain services for receipt management.
Defines business logic for receipt processing, validation, and enrichment.
"""

import re
import os
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime, date
from enum import Enum

from domain.receipts.entities import Receipt, OCRData, ReceiptMetadata, FileInfo
from django.conf import settings
from domain.common.entities import ValueObject


class FileValidationService:
    """Service for validating file uploads."""
    
    def __init__(self):
        max_mb = getattr(settings, 'MAX_RECEIPT_MB', 10)
        self.max_file_size = int(max_mb) * 1024 * 1024
        self.allowed_mime_types = [
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 
            'image/bmp', 'image/tiff', 'image/webp', 'application/pdf'
        ]
        self.allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.pdf']
    
    def validate_file(self, filename: str, file_size: int, mime_type: str) -> Tuple[bool, List[str]]:
        """
        Validate uploaded file.
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check file size
        if file_size > self.max_file_size:
            errors.append(f"File size ({file_size} bytes) exceeds maximum allowed size ({self.max_file_size} bytes)")
        
        # Check MIME type
        if mime_type not in self.allowed_mime_types:
            errors.append(f"MIME type '{mime_type}' is not allowed. Allowed types: {', '.join(self.allowed_mime_types)}")
        
        # Check file extension
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in self.allowed_extensions:
            errors.append(f"File extension '{file_ext}' is not allowed. Allowed extensions: {', '.join(self.allowed_extensions)}")
        
        return len(errors) == 0, errors
    
    def get_file_info(self, filename: str, file_size: int, mime_type: str, file_url: str) -> FileInfo:
        """
        Create FileInfo object from file data.
        
        Args:
            filename: Name of the file
            file_size: Size of the file in bytes
            mime_type: MIME type of the file
            file_url: URL where the file is stored
            
        Returns:
            FileInfo object
        """
        return FileInfo(
            filename=filename,
            file_size=file_size,
            mime_type=mime_type,
            file_url=file_url
        )


class ExpenseCategory(Enum):
    """Expense categories for receipt classification."""
    FOOD_AND_DRINK = "food_and_drink"
    TRANSPORT = "transport"
    ACCOMMODATION = "accommodation"
    OFFICE_SUPPLIES = "office_supplies"
    TECHNOLOGY = "technology"
    MARKETING = "marketing"
    TRAINING = "training"
    ENTERTAINMENT = "entertainment"
    UTILITIES = "utilities"
    INSURANCE = "insurance"
    LEGAL = "legal"
    ACCOUNTING = "accounting"
    OTHER = "other"


class ExpenseType(Enum):
    """Types of expenses."""
    BUSINESS = "business"
    PERSONAL = "personal"
    MIXED = "mixed"


class VATRate(Enum):
    """UK VAT rates."""
    STANDARD = Decimal("0.20")  # 20%
    REDUCED = Decimal("0.05")   # 5%
    ZERO = Decimal("0.00")      # 0%
    EXEMPT = None               # Exempt from VAT


class ReceiptDataEnrichmentService:
    """Service for enriching and standardizing receipt data."""
    
    def __init__(self):
        # Common UK merchant name variations
        self.merchant_aliases = {
            'tesco': ['tesco express', 'tesco extra', 'tesco metro'],
            'sainsburys': ['sainsbury', 'sainsburys local'],
            'asda': ['asda superstore', 'asda express'],
            'morrisons': ['morrisons daily', 'morrisons express'],
            'coop': ['co-operative', 'co op', 'cooperative'],
            'waitrose': ['waitrose & partners', 'waitrose partners'],
            'aldi': ['aldi uk'],
            'lidl': ['lidl uk'],
            'boots': ['boots uk', 'boots the chemist'],
            'superdrug': ['superdrug stores'],
            'w h smith': ['wh smith', 'w h smiths'],
            'marks and spencer': ['m&s', 'marks & spencer'],
            'john lewis': ['john lewis & partners'],
            'debenhams': ['debenhams uk'],
            'next': ['next retail'],
            'primark': ['primark uk'],
            'h&m': ['h&m uk', 'h and m'],
            'zara': ['zara uk'],
            'starbucks': ['starbucks coffee'],
            'costa': ['costa coffee'],
            'pret a manger': ['pret', 'pret a manger uk'],
            'greggs': ['greggs uk'],
            'subway': ['subway uk'],
            'mcdonalds': ['mcdonalds uk', 'mcdonalds restaurant'],
            'kfc': ['kentucky fried chicken', 'kfc uk'],
            'burger king': ['burger king uk'],
            'pizza hut': ['pizza hut uk'],
            'dominos': ['dominos pizza', 'dominos uk'],
            'just eat': ['just eat uk'],
            'deliveroo': ['deliveroo uk'],
            'uber eats': ['uber eats uk'],
        }
        
        # UK VAT number patterns
        self.vat_patterns = [
            r'GB\d{9}',  # Standard GB VAT number
            r'GB\d{12}', # 12-digit GB VAT number
            r'GB\w{5}\d{4}', # GB with letters and numbers
        ]
        
        # Common expense keywords for classification
        self.category_keywords = {
            ExpenseCategory.FOOD_AND_DRINK: [
                'food', 'drink', 'coffee', 'tea', 'lunch', 'dinner', 'breakfast',
                'restaurant', 'cafe', 'pub', 'bar', 'takeaway', 'delivery',
                'grocery', 'supermarket', 'convenience', 'bakery', 'butcher'
            ],
            ExpenseCategory.TRANSPORT: [
                'transport', 'travel', 'train', 'bus', 'tube', 'taxi', 'uber',
                'parking', 'fuel', 'petrol', 'diesel', 'car', 'vehicle',
                'tfl', 'national rail', 'first bus', 'stagecoach'
            ],
            ExpenseCategory.ACCOMMODATION: [
                'hotel', 'accommodation', 'lodging', 'bnb', 'airbnb',
                'hostel', 'guesthouse', 'inn', 'resort', 'apartment'
            ],
            ExpenseCategory.OFFICE_SUPPLIES: [
                'office', 'stationery', 'paper', 'pen', 'pencil', 'notebook',
                'folder', 'file', 'printer', 'ink', 'toner', 'desk', 'chair'
            ],
            ExpenseCategory.TECHNOLOGY: [
                'computer', 'laptop', 'phone', 'tablet', 'software', 'app',
                'internet', 'wifi', 'broadband', 'mobile', 'data', 'cloud'
            ],
            ExpenseCategory.MARKETING: [
                'marketing', 'advertising', 'promotion', 'social media',
                'website', 'design', 'print', 'brochure', 'flyer', 'banner'
            ],
            ExpenseCategory.TRAINING: [
                'training', 'course', 'education', 'learning', 'workshop',
                'seminar', 'conference', 'certification', 'qualification'
            ],
            ExpenseCategory.ENTERTAINMENT: [
                'entertainment', 'cinema', 'theatre', 'concert', 'show',
                'game', 'sport', 'fitness', 'gym', 'leisure', 'recreation'
            ],
            ExpenseCategory.UTILITIES: [
                'utility', 'electricity', 'gas', 'water', 'heating',
                'cooling', 'internet', 'phone', 'mobile', 'broadband'
            ],
            ExpenseCategory.INSURANCE: [
                'insurance', 'policy', 'premium', 'cover', 'protection'
            ],
            ExpenseCategory.LEGAL: [
                'legal', 'lawyer', 'solicitor', 'attorney', 'court',
                'contract', 'agreement', 'document', 'compliance'
            ],
            ExpenseCategory.ACCOUNTING: [
                'accounting', 'bookkeeping', 'tax', 'audit', 'financial',
                'consultant', 'advisor', 'cpa', 'chartered accountant'
            ]
        }
    
    def standardize_merchant_name(self, merchant_name: str) -> str:
        """
        Standardize merchant name using known aliases.
        
        Args:
            merchant_name: Raw merchant name from OCR
            
        Returns:
            Standardized merchant name
        """
        if not merchant_name:
            return ""
        
        # Convert to lowercase for matching
        merchant_lower = merchant_name.lower().strip()
        
        # Check for exact matches in aliases
        for standard_name, aliases in self.merchant_aliases.items():
            if merchant_lower == standard_name or merchant_lower in aliases:
                return standard_name.title()
        
        # Check for partial matches
        for standard_name, aliases in self.merchant_aliases.items():
            for alias in aliases:
                if alias in merchant_lower or merchant_lower in alias:
                    return standard_name.title()
        
        # If no match found, return original with basic cleaning
        return merchant_name.strip().title()
    
    def validate_vat_number(self, vat_number: str) -> Tuple[bool, Optional[str]]:
        """
        Validate UK VAT number format.
        
        Args:
            vat_number: VAT number to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not vat_number:
            return True, None  # VAT number is optional
        
        vat_clean = vat_number.strip().upper()
        
        # Check against known patterns
        for pattern in self.vat_patterns:
            if re.match(pattern, vat_clean):
                return True, None
        
        return False, f"Invalid VAT number format: {vat_number}"
    
    def extract_and_validate_date(self, date_text: str) -> Tuple[Optional[datetime], Optional[str]]:
        """
        Extract and validate date from text.
        
        Args:
            date_text: Date text from OCR
            
        Returns:
            Tuple of (datetime_object, error_message)
        """
        if not date_text:
            return None, "No date text provided"
        
        # UK date patterns
        date_patterns = [
            r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{1,2})\s+(\w+)\s+(\d{2,4})',  # DD Month YYYY
            r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if len(match.groups()) == 3:
                        day, month, year = match.groups()
                        
                        # Handle 2-digit years
                        if len(year) == 2:
                            year = f"20{year}"
                        
                        # Convert month name to number if needed
                        if month.isalpha():
                            month_names = {
                                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                                'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                                'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                            }
                            month = month_names.get(month[:3].lower(), 1)
                        
                        parsed_date = datetime(int(year), int(month), int(day))
                        
                        # Validate date is reasonable (not too far in past/future)
                        current_date = datetime.now()
                        if parsed_date > current_date:
                            return None, f"Date is in the future: {parsed_date.date()}"
                        
                        if (current_date - parsed_date).days > 365 * 10:  # 10 years ago
                            return None, f"Date is too far in the past: {parsed_date.date()}"
                        
                        return parsed_date, None
                        
                except (ValueError, TypeError) as e:
                    continue
        
        return None, f"Could not parse date from text: {date_text}"
    
    def suggest_expense_category(self, receipt: Receipt) -> Optional[ExpenseCategory]:
        """
        Suggest expense category based on receipt data.
        
        Args:
            receipt: Receipt entity with OCR data
            
        Returns:
            Suggested expense category
        """
        if not receipt.ocr_data or not receipt.ocr_data.merchant_name:
            return ExpenseCategory.OTHER
        
        merchant_name = receipt.ocr_data.merchant_name.lower()
        items_text = " ".join([item.get('description', '') for item in receipt.ocr_data.items])
        all_text = f"{merchant_name} {items_text}".lower()
        
        # Score each category based on keyword matches
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in all_text:
                    score += 1
            category_scores[category] = score
        
        # Return category with highest score
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:  # Only suggest if we have matches
                return best_category[0]
        
        return ExpenseCategory.OTHER
    
    def classify_expense_type(self, receipt: Receipt) -> ExpenseType:
        """
        Classify expense as business, personal, or mixed.
        
        Args:
            receipt: Receipt entity with OCR data
            
        Returns:
            Expense type classification
        """
        if not receipt.ocr_data:
            return ExpenseType.PERSONAL
        
        merchant_name = receipt.ocr_data.merchant_name.lower()
        items_text = " ".join([item.get('description', '') for item in receipt.ocr_data.items])
        
        # Business expense indicators
        business_indicators = [
            'office', 'business', 'corporate', 'company', 'ltd', 'limited',
            'consulting', 'services', 'professional', 'commercial',
            'stationery', 'equipment', 'software', 'training', 'travel'
        ]
        
        # Personal expense indicators
        personal_indicators = [
            'personal', 'home', 'family', 'entertainment', 'leisure',
            'restaurant', 'cinema', 'theatre', 'gym', 'fitness'
        ]
        
        business_score = sum(1 for indicator in business_indicators if indicator in merchant_name or indicator in items_text)
        personal_score = sum(1 for indicator in personal_indicators if indicator in merchant_name or indicator in items_text)
        
        if business_score > personal_score:
            return ExpenseType.BUSINESS
        elif personal_score > business_score:
            return ExpenseType.PERSONAL
        else:
            return ExpenseType.MIXED
    
    def calculate_vat_amount(self, total_amount: Decimal, vat_rate: VATRate = VATRate.STANDARD) -> Optional[Decimal]:
        """
        Calculate VAT amount from total amount.
        
        Args:
            total_amount: Total amount including VAT
            vat_rate: VAT rate to apply
            
        Returns:
            Calculated VAT amount
        """
        if not total_amount or vat_rate == VATRate.EXEMPT:
            return None
        
        # Calculate VAT amount: VAT = Total / (1 + Rate) * Rate
        if vat_rate.value:
            vat_amount = total_amount / (1 + vat_rate.value) * vat_rate.value
            return round(vat_amount, 2)
        
        return None
    
    def enrich_ocr_data(self, ocr_data: OCRData) -> OCRData:
        """
        Enrich OCR data with standardized and validated information.
        
        Args:
            ocr_data: Raw OCR data
            
        Returns:
            Enriched OCR data
        """
        # Standardize merchant name
        if ocr_data.merchant_name:
            ocr_data.merchant_name = self.standardize_merchant_name(ocr_data.merchant_name)
        
        # Validate VAT number
        if ocr_data.vat_number:
            is_valid, error = self.validate_vat_number(ocr_data.vat_number)
            if not is_valid:
                # Could add error to metadata or log it
                pass
        
        # Validate and standardize date
        if ocr_data.date:
            # If date is already a datetime object, validate it
            if isinstance(ocr_data.date, datetime):
                current_date = datetime.now()
                if ocr_data.date > current_date:
                    # Date is in future, might be wrong
                    pass
            else:
                # Try to parse date from string
                parsed_date, error = self.extract_and_validate_date(str(ocr_data.date))
                if parsed_date:
                    ocr_data.date = parsed_date
        
        # Calculate VAT if not provided
        if ocr_data.total_amount and not ocr_data.vat_amount:
            ocr_data.vat_amount = self.calculate_vat_amount(ocr_data.total_amount)
        
        return ocr_data


class ReceiptValidationService:
    """Service for validating receipt data and OCR results."""
    
    def __init__(self):
        # Be permissive by default: low confidence should not hard-fail the receipt.
        # We surface low confidence to the UI via quality score and allow manual correction.
        self.min_confidence_threshold = 0.2
        self.max_amount_threshold = Decimal("100000.00")  # £100,000
        self.min_amount_threshold = Decimal("0.01")       # £0.01
    
    def validate_ocr_data(self, ocr_data: OCRData) -> Tuple[bool, List[str]]:
        """
        Validate OCR extracted data.
        
        Args:
            ocr_data: OCR data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate confidence score
        if ocr_data.confidence_score is not None:
            if ocr_data.confidence_score < self.min_confidence_threshold:
                errors.append(f"Low confidence score: {ocr_data.confidence_score:.2f}")
        
        # Validate total amount
        if ocr_data.total_amount:
            if ocr_data.total_amount > self.max_amount_threshold:
                errors.append(f"Total amount too high: £{ocr_data.total_amount}")
            if ocr_data.total_amount < self.min_amount_threshold:
                errors.append(f"Total amount too low: £{ocr_data.total_amount}")
        
        # Validate VAT amount if present
        if ocr_data.vat_amount and ocr_data.total_amount:
            if ocr_data.vat_amount >= ocr_data.total_amount:
                errors.append("VAT amount cannot be greater than or equal to total amount")
        
        # Validate date
        if ocr_data.date:
            if isinstance(ocr_data.date, datetime):
                current_date = datetime.now()
                if ocr_data.date > current_date:
                    errors.append("Receipt date is in the future")
                if (current_date - ocr_data.date).days > 365 * 10:
                    errors.append("Receipt date is too old (more than 10 years)")
        
        # Validate VAT number format
        if ocr_data.vat_number:
            vat_service = ReceiptDataEnrichmentService()
            is_valid, error = vat_service.validate_vat_number(ocr_data.vat_number)
            if not is_valid:
                errors.append(error)
        
        # Validate currency
        if ocr_data.currency and ocr_data.currency not in ['GBP', '£']:
            errors.append(f"Unsupported currency: {ocr_data.currency}")
        
        # Validate items
        if ocr_data.items:
            for i, item in enumerate(ocr_data.items):
                if not item.get('description'):
                    errors.append(f"Item {i+1} missing description")
                if not item.get('price'):
                    errors.append(f"Item {i+1} missing price")
                elif item.get('price', 0) <= 0:
                    errors.append(f"Item {i+1} has invalid price: {item.get('price')}")
        
        return len(errors) == 0, errors
    
    def validate_metadata(self, metadata: ReceiptMetadata) -> Tuple[bool, List[str]]:
        """
        Validate receipt metadata.
        
        Args:
            metadata: Receipt metadata to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate category
        if metadata.category:
            try:
                ExpenseCategory(metadata.category)
            except ValueError:
                errors.append(f"Invalid expense category: {metadata.category}")
        
        # Validate tags
        if metadata.tags:
            for tag in metadata.tags:
                if len(tag) > 50:
                    errors.append(f"Tag too long: {tag}")
                if not tag.strip():
                    errors.append("Empty tag found")
        
        # Validate notes
        if metadata.notes and len(metadata.notes) > 1000:
            errors.append("Notes too long (max 1000 characters)")
        
        # Validate custom fields
        if metadata.custom_fields:
            for key, value in metadata.custom_fields.items():
                if len(key) > 100:
                    errors.append(f"Custom field key too long: {key}")
                if len(str(value)) > 500:
                    errors.append(f"Custom field value too long: {key}")
        
        return len(errors) == 0, errors
    
    def suggest_corrections(self, ocr_data: OCRData) -> Dict[str, Any]:
        """
        Suggest corrections for OCR data issues.
        
        Args:
            ocr_data: OCR data to analyze
            
        Returns:
            Dictionary of suggested corrections
        """
        suggestions = {}
        
        # Suggest VAT amount if missing
        if ocr_data.total_amount and not ocr_data.vat_amount:
            enrichment_service = ReceiptDataEnrichmentService()
            suggested_vat = enrichment_service.calculate_vat_amount(ocr_data.total_amount)
            if suggested_vat:
                suggestions['vat_amount'] = suggested_vat
        
        # Suggest standardized merchant name
        if ocr_data.merchant_name:
            enrichment_service = ReceiptDataEnrichmentService()
            standardized_name = enrichment_service.standardize_merchant_name(ocr_data.merchant_name)
            if standardized_name != ocr_data.merchant_name:
                suggestions['merchant_name'] = standardized_name
        
        # Suggest category
        if not hasattr(ocr_data, 'suggested_category') or not ocr_data.suggested_category:
            # Create a mock receipt for category suggestion
            class MockReceipt:
                def __init__(self, ocr_data):
                    self.ocr_data = ocr_data
                    self.metadata = ReceiptMetadata()
            
            temp_receipt = MockReceipt(ocr_data)
            enrichment_service = ReceiptDataEnrichmentService()
            suggested_category = enrichment_service.suggest_expense_category(temp_receipt)
            suggestions['category'] = suggested_category.value
        
        return suggestions
    
    def calculate_data_quality_score(self, ocr_data: OCRData) -> float:
        """
        Calculate data quality score for OCR data.
        
        Args:
            ocr_data: OCR data to score
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 0.0
        total_fields = 0
        
        # Base confidence score
        if ocr_data.confidence_score is not None:
            score += ocr_data.confidence_score * 0.3
        total_fields += 1
        
        # Required fields
        if ocr_data.merchant_name:
            score += 0.2
        total_fields += 1
        
        if ocr_data.total_amount:
            score += 0.2
        total_fields += 1
        
        if ocr_data.date:
            score += 0.15
        total_fields += 1
        
        # Optional but valuable fields
        if ocr_data.vat_amount:
            score += 0.1
        total_fields += 1
        
        if ocr_data.vat_number:
            score += 0.05
        total_fields += 1
        
        if ocr_data.receipt_number:
            score += 0.05
        total_fields += 1
        
        if ocr_data.items and len(ocr_data.items) > 0:
            score += 0.1 * min(len(ocr_data.items) / 10, 1.0)  # Cap at 10 items
        total_fields += 1
        
        # Normalize score
        return min(score, 1.0)


class ReceiptBusinessService:
    """Service for business logic related to receipts."""
    
    def __init__(self):
        self.enrichment_service = ReceiptDataEnrichmentService()
        self.validation_service = ReceiptValidationService()
    
    def suggest_category(self, receipt: Receipt) -> Optional[str]:
        """Suggest category for receipt based on business rules."""
        return self.enrichment_service.suggest_expense_category(receipt).value
    
    def is_business_expense(self, receipt: Receipt) -> bool:
        """Determine if receipt is a business expense."""
        expense_type = self.enrichment_service.classify_expense_type(receipt)
        return expense_type in [ExpenseType.BUSINESS, ExpenseType.MIXED]
    
    def calculate_tax_deductible_amount(self, receipt: Receipt) -> Optional[Decimal]:
        """Calculate tax deductible amount for business expenses."""
        if not self.is_business_expense(receipt):
            return None
        
        if not receipt.ocr_data or not receipt.ocr_data.total_amount:
            return None
        
        # For business expenses, the full amount is typically tax deductible
        # unless it's entertainment (which has restrictions)
        if receipt.metadata and receipt.metadata.category == ExpenseCategory.ENTERTAINMENT.value:
            # Entertainment expenses are typically 50% deductible
            return receipt.ocr_data.total_amount * Decimal("0.5")
        
        return receipt.ocr_data.total_amount
    
    def process_receipt_for_tax(self, receipt: Receipt) -> Dict[str, Any]:
        """Process receipt for tax purposes."""
        result = {
            'is_business_expense': self.is_business_expense(receipt),
            'tax_deductible_amount': self.calculate_tax_deductible_amount(receipt),
            'category': self.suggest_category(receipt),
            'data_quality_score': 0.0
        }
        
        if receipt.ocr_data:
            result['data_quality_score'] = self.validation_service.calculate_data_quality_score(receipt.ocr_data)
        
        return result 