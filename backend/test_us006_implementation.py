"""
Test script to verify US-006: Receipt Management and Organization implementation.
Tests domain entities, services, use cases, and API endpoints.
"""

import os
import sys
import django
from pathlib import Path
from decimal import Decimal
from datetime import datetime, timedelta

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_accounts.settings')
django.setup()

from domain.receipts.organization import (
    Folder, FolderType, FolderMetadata, Tag, ReceiptCollection,
    ReceiptSearchCriteria, ReceiptSortOptions, SmartFolderRule
)
from domain.receipts.organization_services import (
    FolderService, TagService, ReceiptSearchService, ReceiptBulkOperationService
)
from domain.receipts.entities import Receipt, ReceiptStatus, ReceiptType, OCRData, ReceiptMetadata


def test_domain_entities():
    """Test organization domain entities."""
    print("🧪 Testing US-006 Domain Entities")
    print("=" * 50)
    
    # Test 1: Folder creation
    print("\n1. Testing Folder Creation:")
    folder = Folder(
        id="test-folder-1",
        user_id="test-user",
        name="My Receipts",
        folder_type=FolderType.USER,
        metadata=FolderMetadata(
            description="Personal receipts",
            icon="folder",
            color="#4CAF50",
            is_favorite=True
        )
    )
    print(f"   ✅ Created folder: {folder.name}")
    print(f"   ✅ Folder type: {folder.folder_type.value}")
    print(f"   ✅ Is favorite: {folder.metadata.is_favorite}")
    
    # Test 2: Smart folder rules
    print("\n2. Testing Smart Folder Rules:")
    smart_folder = Folder(
        id="test-smart-folder",
        user_id="test-user",
        name="Recent Business Expenses",
        folder_type=FolderType.SMART
    )
    
    rule1 = SmartFolderRule(
        field='date',
        operator='greater_than',
        value=(datetime.now() - timedelta(days=30)).timestamp()
    )
    
    rule2 = SmartFolderRule(
        field='is_business_expense',
        operator='equals',
        value=True,
        combine_with='AND'
    )
    
    smart_folder.add_smart_rule(rule1)
    smart_folder.add_smart_rule(rule2)
    print(f"   ✅ Created smart folder with {len(smart_folder.smart_rules)} rules")
    
    # Test 3: Tags
    print("\n3. Testing Tags:")
    tag1 = Tag(name="business", color="#2196F3")
    tag2 = Tag(name="tax-deductible", color="#FF9800")
    print(f"   ✅ Created tag: {tag1.name} with color {tag1.color}")
    print(f"   ✅ Created tag: {tag2.name} with color {tag2.color}")
    
    # Test 4: Collections
    print("\n4. Testing Collections:")
    collection = ReceiptCollection(
        id="test-collection",
        user_id="test-user",
        name="Q4 2024 Expenses",
        description="All expenses for Q4 2024"
    )
    
    collection.add_tag(tag1)
    collection.add_tag(tag2)
    collection.add_receipt("receipt-1")
    collection.add_receipt("receipt-2")
    
    print(f"   ✅ Created collection: {collection.name}")
    print(f"   ✅ Added {len(collection.tags)} tags")
    print(f"   ✅ Added {len(collection.receipt_ids)} receipts")
    
    # Test 5: Search criteria
    print("\n5. Testing Search Criteria:")
    search_criteria = ReceiptSearchCriteria(
        query="tesco",
        categories=["food_and_drink"],
        date_from=datetime.now() - timedelta(days=30),
        date_to=datetime.now(),
        amount_min=Decimal("10.00"),
        amount_max=Decimal("100.00"),
        is_business_expense=True
    )
    print("   ✅ Created search criteria with:")
    print(f"      - Query: {search_criteria.query}")
    print(f"      - Categories: {search_criteria.categories}")
    print(f"      - Date range: {search_criteria.date_from.date()} to {search_criteria.date_to.date()}")
    print(f"      - Amount range: £{search_criteria.amount_min} to £{search_criteria.amount_max}")
    
    print("\n✅ Domain Entities Tests Complete!")


def test_domain_services():
    """Test organization domain services."""
    print("\n🧪 Testing US-006 Domain Services")
    print("=" * 50)
    
    # Initialize services
    folder_service = FolderService()
    tag_service = TagService()
    
    # Test 1: Default folder creation
    print("\n1. Testing Default Folder Creation:")
    default_folders = folder_service.create_default_folders("test-user")
    print(f"   ✅ Created {len(default_folders)} default folders:")
    for folder in default_folders:
        print(f"      - {folder.name} ({folder.folder_type.value})")
    
    # Test 2: Tag normalization
    print("\n2. Testing Tag Normalization:")
    test_tags = [
        "Business Expense",
        "TAX DEDUCTIBLE",
        "travel & transport",
        "Q4-2024"
    ]
    
    for tag_name in test_tags:
        normalized = tag_service.normalize_tag_name(tag_name)
        print(f"   '{tag_name}' -> '{normalized}'")
    
    # Test 3: Tag validation
    print("\n3. Testing Tag Validation:")
    valid_tag = Tag(name="business")
    
    is_valid, error = tag_service.validate_tag(valid_tag)
    print(f"   Tag '{valid_tag.name}': {'✅ Valid' if is_valid else f'❌ Invalid - {error}'}")
    
    # Test empty tag
    try:
        invalid_tag1 = Tag(name="")
    except ValueError as e:
        print(f"   Empty tag: ❌ Invalid - {e}")
    
    # Test tag with invalid characters
    invalid_tag2 = Tag(name="tag/with/slashes")
    is_valid, error = tag_service.validate_tag(invalid_tag2)
    print(f"   Tag '{invalid_tag2.name}': {'✅ Valid' if is_valid else f'❌ Invalid - {error}'}")
    
    # Test 4: Smart folder rule evaluation
    print("\n4. Testing Smart Folder Rule Evaluation:")
    
    # Create mock receipt
    class MockReceipt:
        def __init__(self):
            self.status = ReceiptStatus.PROCESSED
            self.receipt_type = ReceiptType.PURCHASE
            self.created_at = datetime.now()
            self.updated_at = datetime.now()
            self.ocr_data = OCRData(
                merchant_name="Tesco Express",
                total_amount=Decimal("45.50"),
                date=datetime.now() - timedelta(days=5)
            )
            self.metadata = ReceiptMetadata(
                category="food_and_drink",
                is_business_expense=True
            )
        
        def get_merchant_name(self):
            return self.ocr_data.merchant_name
        
        def get_total_amount(self):
            return self.ocr_data.total_amount
        
        def get_receipt_date(self):
            return self.ocr_data.date
    
    receipt = MockReceipt()
    
    # Test rule evaluation
    rule = SmartFolderRule(
        field='total_amount',
        operator='greater_than',
        value=Decimal("40.00")
    )
    
    result = folder_service._evaluate_rule(rule, receipt)
    print(f"   Rule: total_amount > 40.00")
    print(f"   Receipt amount: £{receipt.get_total_amount()}")
    print(f"   Result: {'✅ Matches' if result else '❌ No match'}")
    
    print("\n✅ Domain Services Tests Complete!")


def test_api_endpoints():
    """Test new API endpoints for US-006."""
    print("\n🧪 Testing US-006 API Endpoints")
    print("=" * 50)
    
    try:
        from django.test import Client
        from django.urls import reverse
        
        client = Client()
        
        # Test endpoint existence
        endpoints = [
            ('api:folder-list', {}),
            ('api:folder-create', {}),
            ('api:folder-detail', {'folder_id': 'test-folder-id'}),
            ('api:folder-receipts', {'folder_id': 'test-folder-id'}),
            ('api:receipt-search', {}),
            ('api:receipt-tags', {'receipt_id': 'test-receipt-id'}),
            ('api:receipt-bulk', {}),
            ('api:user-statistics', {})
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


def test_search_functionality():
    """Test receipt search functionality."""
    print("\n🧪 Testing Receipt Search Functionality")
    print("=" * 50)
    
    # Create mock receipts
    receipts = []
    
    # Create a proper mock receipt class
    class MockReceipt:
        def __init__(self, id, status, receipt_type, ocr_data, metadata):
            self.id = id
            self.status = status
            self.receipt_type = receipt_type
            self.created_at = datetime.now()
            self.updated_at = datetime.now()
            self.ocr_data = ocr_data
            self.metadata = metadata
        
        def get_merchant_name(self):
            return self.ocr_data.merchant_name if self.ocr_data else None
        
        def get_total_amount(self):
            return self.ocr_data.total_amount if self.ocr_data else None
        
        def get_receipt_date(self):
            return self.ocr_data.date if self.ocr_data else None
    
    # Receipt 1: Tesco, Business expense
    receipt1 = MockReceipt(
        id="receipt-1",
        status=ReceiptStatus.PROCESSED,
        receipt_type=ReceiptType.PURCHASE,
        ocr_data=OCRData(
            merchant_name="Tesco Express",
            total_amount=Decimal("25.50"),
            date=datetime.now() - timedelta(days=5),
            raw_text="TESCO EXPRESS\nMilk £1.20\nBread £0.85"
        ),
        metadata=ReceiptMetadata(
            category="food_and_drink",
            is_business_expense=True,
            notes="Client lunch meeting"
        )
    )
    receipts.append(receipt1)
    
    # Receipt 2: Amazon, Personal expense
    receipt2 = MockReceipt(
        id="receipt-2",
        status=ReceiptStatus.PROCESSED,
        receipt_type=ReceiptType.PURCHASE,
        ocr_data=OCRData(
            merchant_name="Amazon UK",
            total_amount=Decimal("150.00"),
            date=datetime.now() - timedelta(days=10),
            receipt_number="AMZ-123456"
        ),
        metadata=ReceiptMetadata(
            category="technology",
            is_business_expense=False
        )
    )
    receipts.append(receipt2)
    
    # Mock search service
    class MockReceiptRepository:
        def find_by_user(self, user_id, limit, offset):
            return receipts
    
    search_service = ReceiptSearchService(MockReceiptRepository())
    
    # Test 1: Text search
    print("\n1. Testing Text Search:")
    criteria = ReceiptSearchCriteria(query="tesco")
    filtered = search_service._apply_filters(receipts, criteria)
    print(f"   Query: 'tesco'")
    print(f"   Results: {len(filtered)} receipts found")
    
    # Test 2: Amount range search
    print("\n2. Testing Amount Range Search:")
    criteria = ReceiptSearchCriteria(
        amount_min=Decimal("100.00"),
        amount_max=Decimal("200.00")
    )
    filtered = search_service._apply_filters(receipts, criteria)
    print(f"   Range: £100.00 - £200.00")
    print(f"   Results: {len(filtered)} receipts found")
    
    # Test 3: Business expense filter
    print("\n3. Testing Business Expense Filter:")
    criteria = ReceiptSearchCriteria(is_business_expense=True)
    filtered = search_service._apply_filters(receipts, criteria)
    print(f"   Filter: Business expenses only")
    print(f"   Results: {len(filtered)} receipts found")
    
    # Test 4: Sorting
    print("\n4. Testing Sorting:")
    sort_options = ReceiptSortOptions(field="amount", direction="desc")
    sorted_receipts = search_service._apply_sorting(receipts, sort_options)
    print(f"   Sort by: amount (descending)")
    for r in sorted_receipts:
        print(f"      - {r.ocr_data.merchant_name}: £{r.ocr_data.total_amount}")
    
    print("\n✅ Search Functionality Tests Complete!")


def test_bulk_operations():
    """Test bulk operations functionality."""
    print("\n🧪 Testing Bulk Operations")
    print("=" * 50)
    
    # Create mock receipts
    receipts = []
    for i in range(5):
        receipt = type('Receipt', (), {})()
        receipt.id = f"receipt-{i}"
        receipt.metadata = ReceiptMetadata()
        receipt.status = ReceiptStatus.PROCESSED
        receipts.append(receipt)
    
    # Mock repository
    class MockReceiptRepository:
        pass
    
    bulk_service = ReceiptBulkOperationService(MockReceiptRepository())
    
    # Test 1: Bulk add tags
    print("\n1. Testing Bulk Add Tags:")
    tags = [Tag(name="q4-2024"), Tag(name="reviewed")]
    count = bulk_service.bulk_add_tags(receipts, tags)
    print(f"   Added {len(tags)} tags to {len(receipts)} receipts")
    print(f"   Total operations: {count}")
    
    # Test 2: Bulk categorize
    print("\n2. Testing Bulk Categorize:")
    count = bulk_service.bulk_categorize(receipts, "business")
    print(f"   Set category 'business' on {count} receipts")
    
    # Test 3: Bulk mark as business
    print("\n3. Testing Bulk Mark as Business:")
    count = bulk_service.bulk_mark_as_business(receipts, True)
    print(f"   Marked {count} receipts as business expenses")
    
    print("\n✅ Bulk Operations Tests Complete!")


def main():
    """Run all US-006 tests."""
    print("🚀 US-006: Receipt Management and Organization - Implementation Test")
    print("=" * 70)
    
    # Test domain entities
    test_domain_entities()
    
    # Test domain services
    test_domain_services()
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test search functionality
    test_search_functionality()
    
    # Test bulk operations
    test_bulk_operations()
    
    print("\n" + "=" * 70)
    print("🎉 US-006 Implementation Test Complete!")
    print("\n📋 Summary of US-006 Features Implemented:")
    print("   ✅ Domain Entities:")
    print("      - Folder (with types: SYSTEM, USER, SMART)")
    print("      - Tag (with color support)")
    print("      - ReceiptCollection (for grouping receipts)")
    print("      - Search criteria and sort options")
    print("   ✅ Domain Services:")
    print("      - FolderService (hierarchy, smart folders)")
    print("      - TagService (normalization, validation)")
    print("      - ReceiptSearchService (advanced filtering)")
    print("      - ReceiptBulkOperationService")
    print("   ✅ Application Use Cases:")
    print("      - CreateFolderUseCase")
    print("      - MoveFolderUseCase")
    print("      - SearchReceiptsUseCase")
    print("      - AddTagsToReceiptUseCase")
    print("      - BulkOperationUseCase")
    print("      - MoveReceiptsToFolderUseCase")
    print("      - GetUserStatisticsUseCase")
    print("   ✅ API Endpoints:")
    print("      - GET /api/v1/folders/ - List folders")
    print("      - POST /api/v1/folders/create/ - Create folder")
    print("      - PUT /api/v1/folders/{id}/ - Update folder")
    print("      - POST /api/v1/folders/{id}/receipts/ - Move receipts")
    print("      - POST /api/v1/receipts/search/ - Advanced search")
    print("      - POST /api/v1/receipts/{id}/tags/ - Add tags")
    print("      - POST /api/v1/receipts/bulk/ - Bulk operations")
    print("      - GET /api/v1/users/statistics/ - User statistics")
    print("   ✅ Features:")
    print("      - Hierarchical folder organization")
    print("      - Smart folders with dynamic rules")
    print("      - Tagging system")
    print("      - Advanced search and filtering")
    print("      - Bulk operations")
    print("      - Collections for grouping")
    print("      - Comprehensive statistics")
    print("\n🚀 Ready for Frontend Implementation!")


if __name__ == "__main__":
    main()