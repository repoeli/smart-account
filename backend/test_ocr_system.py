"""
Test script to demonstrate the dual OCR system.
Shows how users can choose between PaddleOCR and OpenAI Vision API.
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_accounts.settings')
django.setup()

from infrastructure.ocr.services import OCRService, OCRMethod
from domain.receipts.entities import OCRData
import tempfile


def test_ocr_system():
    """Test the dual OCR system."""
    print("🧪 Testing Dual OCR System")
    print("=" * 50)
    
    # Initialize OCR service
    ocr_service = OCRService()
    
    # Check available methods
    available_methods = ocr_service.get_available_methods()
    print(f"✅ Available OCR Methods: {[method.value for method in available_methods]}")
    
    # Create a sample receipt text for testing
    sample_receipt_text = """
    TESCO EXPRESS
    123 High Street, London
    Tel: 020 1234 5678
    
    Receipt #: 123456789
    Date: 15/12/2024
    Time: 14:30
    
    Items:
    Milk 2L          £1.20
    Bread White      £0.85
    Eggs 6pk         £2.10
    Coffee Beans     £3.50
    
    Subtotal:        £7.65
    VAT (20%):       £1.53
    Total:           £9.18
    
    VAT Number: GB123456789
    Thank you for shopping with us!
    """
    
    # Create a temporary file with the sample text
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(sample_receipt_text)
        temp_file_path = f.name
    
    try:
        print("\n📄 Testing OCR Methods with Sample Receipt")
        print("-" * 40)
        
        # Test each available method
        for method in available_methods:
            print(f"\n🔍 Testing {method.value.upper()}:")
            
            if method == OCRMethod.FALLBACK:
                # For fallback, we'll test the parsing logic directly
                print("   Using fallback OCR (mock data)")
                ocr_data = ocr_service._parse_receipt_text(sample_receipt_text)
                
                print(f"   ✅ Merchant: {ocr_data.merchant_name}")
                print(f"   ✅ Total Amount: £{ocr_data.total_amount}")
                print(f"   ✅ Date: {ocr_data.date}")
                print(f"   ✅ VAT Amount: £{ocr_data.vat_amount}")
                print(f"   ✅ Confidence Score: {ocr_data.confidence_score:.2f}")
                
            else:
                # For real OCR methods, we would need an actual image
                print(f"   Method available: {ocr_service.is_method_available(method)}")
                if method == OCRMethod.OPENAI_VISION:
                    print("   ⚠️  OpenAI Vision requires actual image file")
                elif method == OCRMethod.PADDLE_OCR:
                    print("   ⚠️  PaddleOCR requires actual image file")
        
        print("\n🎯 OCR Method Selection Options:")
        print("-" * 40)
        print("1. PaddleOCR (Open Source):")
        print("   - Free and open source")
        print("   - Works offline")
        print("   - Good for basic text extraction")
        print("   - May require more processing time")
        
        print("\n2. OpenAI Vision API:")
        print("   - High accuracy and reliability")
        print("   - Excellent for complex receipts")
        print("   - Requires internet connection")
        print("   - Uses API credits")
        
        print("\n3. Auto (Best Available):")
        print("   - System automatically chooses the best method")
        print("   - Falls back gracefully if preferred method fails")
        print("   - Recommended for most users")
        
        print("\n📋 API Usage Example:")
        print("-" * 40)
        print("POST /api/v1/receipts/upload/")
        print("Content-Type: multipart/form-data")
        print("")
        print("Parameters:")
        print("- file: receipt_image.jpg")
        print("- receipt_type: purchase")
        print("- ocr_method: openai_vision  # or 'paddle_ocr' or 'auto'")
        
        print("\n✅ Dual OCR System Test Complete!")
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


if __name__ == "__main__":
    test_ocr_system() 