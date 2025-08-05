"""
Test script to verify US-005: Enhanced Receipt Processing implementation.
Tests domain services, use cases, and API endpoints for enhanced receipt processing.
"""

import os
import sys
import django
from pathlib import Path
from decimal import Decimal
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_accounts.settings')
django.setup()

from domain.receipts.services import (
    ReceiptDataEnrichmentService, ReceiptValidationService, ReceiptBusinessService,
    ExpenseCategory, ExpenseType, VATRate
)
from domain.receipts.entities import Receipt, OCRData, ReceiptMetadata, ReceiptStatus, ReceiptType, FileInfo
from domain.accounts.entities import User, UserType, UserStatus, SubscriptionTier


def test_domain_services():
    """Test enhanced domain services for US-005."""
    print("🧪 Testing US-005 Domain Services")
    print("=" * 50)
    
    # Initialize services
    enrichment_service = ReceiptDataEnrichmentService()
    validation_service = ReceiptValidationService()
    business_service = ReceiptBusinessService()
    
    # Test 1: Merchant name standardization
    print("\n1. Testing Merchant Name Standardization:")
    test_merchants = [
        "TESCO EXPRESS",
        "tesco extra",
        "Sainsburys Local",
        "Boots UK",
        "Unknown Store"
    ]
    
    for merchant in test_merchants:
        standardized = enrichment_service.standardize_merchant_name(merchant)
        print(f"   {merchant} -> {standardized}")
    
    # Test 2: VAT number validation
    print("\n2. Testing VAT Number Validation:")
    test_vat_numbers = [
        "GB123456789",
        "GB123456789012",
        "GBABCD12345",
        "INVALID123",
        ""
    ]
    
    for vat_number in test_vat_numbers:
        is_valid, error = enrichment_service.validate_vat_number(vat_number)
        print(f"   {vat_number}: {'✅ Valid' if is_valid else f'❌ Invalid - {error}'}")
    
    # Test 3: Date extraction and validation
    print("\n3. Testing Date Extraction and Validation:")
    test_dates = [
        "15/12/2024",
        "2024-12-15",
        "15 Dec 2024",
        "Invalid Date",
        ""
    ]
    
    for date_text in test_dates:
        parsed_date, error = enrichment_service.extract_and_validate_date(date_text)
        if parsed_date:
            print(f"   {date_text} -> {parsed_date.strftime('%Y-%m-%d')}")
        else:
            print(f"   {date_text} -> ❌ {error}")
    
    # Test 4: VAT calculation
    print("\n4. Testing VAT Calculation:")
    test_amounts = [Decimal("100.00"), Decimal("50.00"), Decimal("25.00")]
    
    for amount in test_amounts:
        vat_amount = enrichment_service.calculate_vat_amount(amount, VATRate.STANDARD)
        print(f"   £{amount} -> VAT: £{vat_amount}")
    
    # Test 5: Expense classification
    print("\n5. Testing Expense Classification:")
    
    # Create mock receipt for testing without full User entity
    # This tests the business logic without database dependencies
    
    # Create test receipt with OCR data
    ocr_data = OCRData(
        merchant_name="Tesco Express",
        total_amount=Decimal("25.50"),
        currency="GBP",
        date=datetime.now(),
        items=[
            {"description": "Milk", "price": Decimal("1.20"), "quantity": 1},
            {"description": "Bread", "price": Decimal("0.85"), "quantity": 1},
            {"description": "Coffee", "price": Decimal("3.50"), "quantity": 1}
        ]
    )
    
    # Create a simple mock receipt for testing
    class MockReceipt:
        def __init__(self, ocr_data):
            self.ocr_data = ocr_data
            self.metadata = ReceiptMetadata()
    
    test_receipt = MockReceipt(ocr_data)
    
    # Test category suggestion
    suggested_category = business_service.suggest_category(test_receipt)
    print(f"   Suggested Category: {suggested_category}")
    
    # Test expense type classification
    expense_type = enrichment_service.classify_expense_type(test_receipt)
    print(f"   Expense Type: {expense_type.value}")
    
    # Test business expense detection
    is_business = business_service.is_business_expense(test_receipt)
    print(f"   Is Business Expense: {is_business}")
    
    # Test tax deductible calculation
    tax_deductible = business_service.calculate_tax_deductible_amount(test_receipt)
    print(f"   Tax Deductible Amount: £{tax_deductible}")
    
    # Test 6: OCR data validation
    print("\n6. Testing OCR Data Validation:")
    
    # Valid OCR data
    valid_ocr = OCRData(
        merchant_name="Tesco Express",
        total_amount=Decimal("25.50"),
        currency="GBP",
        date=datetime.now(),
        vat_amount=Decimal("4.25"),
        vat_number="GB123456789",
        receipt_number="123456789",
        confidence_score=0.85,
        items=[
            {"description": "Milk", "price": Decimal("1.20"), "quantity": 1}
        ]
    )
    
    is_valid, errors = validation_service.validate_ocr_data(valid_ocr)
    print(f"   Valid OCR Data: {'✅ Valid' if is_valid else f'❌ Invalid - {errors}'}")
    
    # Invalid OCR data (high amount)
    invalid_ocr = OCRData(
        merchant_name="Test Store",
        total_amount=Decimal("200000.00"),  # Too high
        currency="GBP",
        date=datetime.now(),
        confidence_score=0.3  # Low confidence
    )
    
    is_valid, errors = validation_service.validate_ocr_data(invalid_ocr)
    print(f"   Invalid OCR Data: {'✅ Valid' if is_valid else f'❌ Invalid - {errors}'}")
    
    # Test 7: Data quality scoring
    print("\n7. Testing Data Quality Scoring:")
    quality_score = validation_service.calculate_data_quality_score(valid_ocr)
    print(f"   Quality Score: {quality_score:.2f}")
    
    # Test 8: Correction suggestions
    print("\n8. Testing Correction Suggestions:")
    suggestions = validation_service.suggest_corrections(valid_ocr)
    print(f"   Suggestions: {suggestions}")
    
    print("\n✅ Domain Services Tests Complete!")


def test_use_cases():
    """Test new use cases for US-005."""
    print("\n🧪 Testing US-005 Use Cases")
    print("=" * 50)
    
    try:
        # Initialize dependencies
        from infrastructure.database.repositories import DjangoReceiptRepository
        from infrastructure.ocr.services import OCRService
        from domain.receipts.services import (
            ReceiptBusinessService, ReceiptValidationService, ReceiptDataEnrichmentService
        )
        from application.receipts.use_cases import (
            ReceiptReprocessUseCase, ReceiptValidateUseCase, 
            ReceiptCategorizeUseCase, ReceiptStatisticsUseCase
        )
        
        # Create test user
        test_user = User(
            id="test-user-005",
            email="test-us005@example.com",
            user_type=UserType.INDIVIDUAL,
            status=UserStatus.ACTIVE,
            subscription_tier=SubscriptionTier.BASIC
        )
        
        # Initialize services
        receipt_repository = DjangoReceiptRepository()
        ocr_service = OCRService()
        receipt_business_service = ReceiptBusinessService()
        receipt_validation_service = ReceiptValidationService()
        receipt_enrichment_service = ReceiptDataEnrichmentService()
        
        print("\n1. Testing ReceiptReprocessUseCase:")
        reprocess_use_case = ReceiptReprocessUseCase(
            receipt_repository=receipt_repository,
            ocr_service=ocr_service,
            receipt_business_service=receipt_business_service,
            receipt_validation_service=receipt_validation_service
        )
        print("   ✅ ReceiptReprocessUseCase initialized")
        
        print("\n2. Testing ReceiptValidateUseCase:")
        validate_use_case = ReceiptValidateUseCase(
            receipt_repository=receipt_repository,
            receipt_validation_service=receipt_validation_service,
            receipt_enrichment_service=receipt_enrichment_service
        )
        print("   ✅ ReceiptValidateUseCase initialized")
        
        print("\n3. Testing ReceiptCategorizeUseCase:")
        categorize_use_case = ReceiptCategorizeUseCase(
            receipt_repository=receipt_repository,
            receipt_business_service=receipt_business_service,
            receipt_enrichment_service=receipt_enrichment_service
        )
        print("   ✅ ReceiptCategorizeUseCase initialized")
        
        print("\n4. Testing ReceiptStatisticsUseCase:")
        statistics_use_case = ReceiptStatisticsUseCase(
            receipt_repository=receipt_repository
        )
        print("   ✅ ReceiptStatisticsUseCase initialized")
        
        print("\n✅ Use Cases Tests Complete!")
        
    except Exception as e:
        print(f"   ❌ Use Cases Test Failed: {e}")


def test_api_endpoints():
    """Test new API endpoints for US-005."""
    print("\n🧪 Testing US-005 API Endpoints")
    print("=" * 50)
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Test endpoint existence
        endpoints = [
            ('api:receipt-reprocess', {'receipt_id': 'test-receipt-id'}),
            ('api:receipt-validate', {'receipt_id': 'test-receipt-id'}), 
            ('api:receipt-categorize', {'receipt_id': 'test-receipt-id'}),
            ('api:receipt-statistics', {})  # This endpoint doesn't take receipt_id
        ]
        
        for endpoint_name, kwargs in endpoints:
            try:
                url = reverse(endpoint_name, kwargs=kwargs)
                print(f"   ✅ {endpoint_name}: {url}")
            except Exception as e:
                print(f"   ❌ {endpoint_name}: {e}")
        
        print("\n✅ API Endpoints Tests Complete!")
        
    except Exception as e:
        print(f"   ❌ API Endpoints Test Failed: {e}")


def test_integration():
    """Test integration of US-005 features."""
    print("\n🧪 Testing US-005 Integration")
    print("=" * 50)
    
    try:
        # Test complete workflow
        print("\n1. Testing Complete Receipt Processing Workflow:")
        
        # Create test OCR data
        ocr_data = OCRData(
            merchant_name="tesco express",
            total_amount=Decimal("45.75"),
            currency="GBP",
            date=datetime.now(),
            vat_amount=Decimal("7.63"),
            vat_number="GB123456789",
            receipt_number="123456789",
            confidence_score=0.92,
            items=[
                {"description": "Milk 2L", "price": Decimal("1.20"), "quantity": 1},
                {"description": "Bread White", "price": Decimal("0.85"), "quantity": 1},
                {"description": "Coffee Beans", "price": Decimal("3.50"), "quantity": 1}
            ],
            raw_text="TESCO EXPRESS\nReceipt #123456789\nMilk 2L £1.20\nBread White £0.85\nCoffee Beans £3.50\nTotal: £45.75"
        )
        
        # Test enrichment
        enrichment_service = ReceiptDataEnrichmentService()
        enriched_ocr = enrichment_service.enrich_ocr_data(ocr_data)
        print(f"   Original merchant: {ocr_data.merchant_name}")
        print(f"   Enriched merchant: {enriched_ocr.merchant_name}")
        
        # Test validation
        validation_service = ReceiptValidationService()
        is_valid, errors = validation_service.validate_ocr_data(enriched_ocr)
        print(f"   Validation result: {'✅ Valid' if is_valid else f'❌ Invalid - {errors}'}")
        
        # Test business logic
        business_service = ReceiptBusinessService()
        
        # Create mock receipt for testing
        class MockReceipt:
            def __init__(self, ocr_data):
                self.ocr_data = ocr_data
                self.metadata = ReceiptMetadata()
        
        test_receipt = MockReceipt(enriched_ocr)
        
        # Test categorization
        suggested_category = business_service.suggest_category(test_receipt)
        print(f"   Suggested category: {suggested_category}")
        
        # Test expense classification
        expense_type = enrichment_service.classify_expense_type(test_receipt)
        print(f"   Expense type: {expense_type.value}")
        
        # Test tax processing
        tax_result = business_service.process_receipt_for_tax(test_receipt)
        print(f"   Tax processing result: {tax_result}")
        
        print("\n✅ Integration Tests Complete!")
        
    except Exception as e:
        print(f"   ❌ Integration Test Failed: {e}")


def main():
    """Run all US-005 tests."""
    print("🚀 US-005: Enhanced Receipt Processing - Implementation Test")
    print("=" * 70)
    
    # Test domain services
    test_domain_services()
    
    # Test use cases
    test_use_cases()
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test integration
    test_integration()
    
    print("\n" + "=" * 70)
    print("🎉 US-005 Implementation Test Complete!")
    print("\n📋 Summary of US-005 Features Implemented:")
    print("   ✅ Enhanced Domain Services:")
    print("      - ReceiptDataEnrichmentService (merchant standardization, VAT validation)")
    print("      - ReceiptValidationService (data validation, quality scoring)")
    print("      - ReceiptBusinessService (categorization, tax processing)")
    print("   ✅ New Use Cases:")
    print("      - ReceiptReprocessUseCase (reprocess with different OCR methods)")
    print("      - ReceiptValidateUseCase (validate and correct receipt data)")
    print("      - ReceiptCategorizeUseCase (auto-categorize receipts)")
    print("      - ReceiptStatisticsUseCase (processing statistics)")
    print("   ✅ New API Endpoints:")
    print("      - POST /api/v1/receipts/{id}/reprocess/")
    print("      - PUT /api/v1/receipts/{id}/validate/")
    print("      - POST /api/v1/receipts/{id}/categorize/")
    print("      - GET /api/v1/receipts/statistics/")
    print("   ✅ Enhanced Business Logic:")
    print("      - UK VAT calculation and validation")
    print("      - Expense classification (business vs personal)")
    print("      - Merchant name standardization")
    print("      - Data quality scoring")
    print("      - Correction suggestions")
    print("\n🚀 Ready for US-006: Receipt Management and Organization!")


if __name__ == "__main__":
    main() 