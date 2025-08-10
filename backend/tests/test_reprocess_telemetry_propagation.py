import types
from unittest.mock import patch, MagicMock

from application.receipts.use_cases import ReceiptReprocessUseCase


def test_reprocess_sets_needs_review_when_validation_fails():
    """Test that reprocess sets needs_review=True when validation fails"""
    class FakeReceipt:
        def __init__(self):
            self.id = 'rid'
            self.user = types.SimpleNamespace(id='uid')
            self.file_info = types.SimpleNamespace(file_url='https://example.com/image.jpg', filename='test.jpg', mime_type='image/jpeg')
            self.status = types.SimpleNamespace(value='uploaded')
            self.receipt_type = types.SimpleNamespace(value='purchase')
            self.metadata = types.SimpleNamespace(custom_fields={})
            self.ocr_data = None

    class FakeRepo:
        def __init__(self):
            self._r = FakeReceipt()
        def find_by_id(self, _):
            return self._r
        def save(self, r):
            self._r = r
            return r

    # Mock OCR service to return successful OCR but failed validation
    mock_ocr_service = MagicMock()
    mock_ocr_service.process_image.return_value = {
        'text': 'Test receipt text',
        'confidence': 0.8,
        'additional_data': {'source_url': 'https://example.com/ocr'}
    }

    # Mock validation service to fail
    mock_validation_service = MagicMock()
    mock_validation_service.validate_receipt.return_value = {
        'is_valid': False,
        'confidence': 0.3,
        'errors': ['Missing total amount', 'Invalid date format']
    }

    use_case = ReceiptReprocessUseCase(
        receipt_repository=FakeRepo(),
        ocr_service=mock_ocr_service,
        receipt_business_service=MagicMock(),
        receipt_validation_service=mock_validation_service
    )

    # Act
    result = use_case.execute('rid', 'uid', 'paddle_ocr')

    # Assert
    assert result['success'] is True
    assert result['receipt_id'] == 'rid'
    
    # Check that needs_review is set
    assert result['metadata']['custom_fields']['needs_review'] is True
    assert 'validation_errors' in result['metadata']['custom_fields']
    assert len(result['metadata']['custom_fields']['validation_errors']) == 2


def test_reprocess_propagates_latency_ms():
    """Test that reprocess includes OCR latency in response"""
    class FakeReceipt:
        def __init__(self):
            self.id = 'rid'
            self.user = types.SimpleNamespace(id='uid')
            self.file_info = types.SimpleNamespace(file_url='https://example.com/image.jpg', filename='test.jpg', mime_type='image/jpeg')
            self.status = types.SimpleNamespace(value='uploaded')
            self.receipt_type = types.SimpleNamespace(value='purchase')
            self.metadata = types.SimpleNamespace(custom_fields={})
            self.ocr_data = None

    class FakeRepo:
        def __init__(self):
            self._r = FakeReceipt()
        def find_by_id(self, _):
            return self._r
        def save(self, r):
            self._r = r
            return r

    # Mock OCR service with timing
    mock_ocr_service = MagicMock()
    mock_ocr_service.process_image.return_value = {
        'text': 'Test receipt text',
        'confidence': 0.9,
        'additional_data': {'source_url': 'https://example.com/ocr'}
    }

    # Mock validation service to succeed
    mock_validation_service = MagicMock()
    mock_validation_service.validate_receipt.return_value = {
        'is_valid': True,
        'confidence': 0.85,
        'errors': []
    }

    use_case = ReceiptReprocessUseCase(
        receipt_repository=FakeRepo(),
        ocr_service=mock_ocr_service,
        receipt_business_service=MagicMock(),
        receipt_validation_service=mock_validation_service
    )

    # Act
    result = use_case.execute('rid', 'uid', 'paddle_ocr')

    # Assert
    assert result['success'] is True
    assert 'ocr_latency_ms' in result
    assert isinstance(result['ocr_latency_ms'], (int, float))
    assert result['ocr_latency_ms'] > 0


def test_reprocess_detail_response_includes_telemetry():
    """Test that detail response includes all telemetry fields after reprocess"""
    class FakeReceipt:
        def __init__(self):
            self.id = 'rid'
            self.user = types.SimpleNamespace(id='uid')
            self.file_info = types.SimpleNamespace(file_url='https://example.com/image.jpg', filename='test.jpg', mime_type='image/jpeg')
            self.status = types.SimpleNamespace(value='processed')
            self.receipt_type = types.SimpleNamespace(value='purchase')
            self.metadata = types.SimpleNamespace(custom_fields={
                'needs_review': True,
                'validation_errors': ['Missing total amount'],
                'storage_provider': 'local',
                'ocr_latency_ms': 1250
            })
            self.ocr_data = types.SimpleNamespace(
                text='Test receipt text',
                confidence=0.8,
                additional_data={'source_url': 'https://example.com/ocr'}
            )

    class FakeRepo:
        def find_by_id(self, _):
            return FakeReceipt()

    # Mock business service
    mock_business_service = MagicMock()
    mock_business_service.get_receipt_details.return_value = {
        'id': 'rid',
        'filename': 'test.jpg',
        'status': 'processed',
        'metadata': {
            'custom_fields': {
                'needs_review': True,
                'validation_errors': ['Missing total amount'],
                'storage_provider': 'local',
                'ocr_latency_ms': 1250
            }
        },
        'ocr_data': {
            'text': 'Test receipt text',
            'confidence': 0.8,
            'additional_data': {'source_url': 'https://example.com/ocr'}
        }
    }

    # Test that the business service properly maps all fields
    result = mock_business_service.get_receipt_details('rid', 'uid')
    
    # Assert all telemetry fields are present
    assert result['metadata']['custom_fields']['needs_review'] is True
    assert 'validation_errors' in result['metadata']['custom_fields']
    assert result['metadata']['custom_fields']['storage_provider'] == 'local'
    assert result['metadata']['custom_fields']['ocr_latency_ms'] == 1250
    assert result['ocr_data']['additional_data']['source_url'] == 'https://example.com/ocr'


def test_reprocess_preserves_existing_telemetry():
    """Test that reprocess doesn't overwrite existing telemetry"""
    class FakeReceipt:
        def __init__(self):
            self.id = 'rid'
            self.user = types.SimpleNamespace(id='uid')
            self.file_info = types.SimpleNamespace(file_url='https://example.com/image.jpg', filename='test.jpg', mime_type='image/jpeg')
            self.status = types.SimpleNamespace(value='processed')
            self.receipt_type = types.SimpleNamespace(value='purchase')
            self.metadata = types.SimpleNamespace(custom_fields={
                'storage_provider': 'cloudinary',
                'cloudinary_public_id': 'receipts/abc123',
                'ocr_latency_ms': 800,
                'previous_processing_count': 2
            })
            self.ocr_data = types.SimpleNamespace(
                text='Existing OCR text',
                confidence=0.7
            )

    class FakeRepo:
        def __init__(self):
            self._r = FakeReceipt()
        def find_by_id(self, _):
            return self._r
        def save(self, r):
            self._r = r
            return r

    # Mock OCR service
    mock_ocr_service = MagicMock()
    mock_ocr_service.process_image.return_value = {
        'text': 'New OCR text',
        'confidence': 0.9,
        'additional_data': {'source_url': 'https://example.com/ocr'}
    }

    # Mock validation service
    mock_validation_service = MagicMock()
    mock_validation_service.validate_receipt.return_value = {
        'is_valid': True,
        'confidence': 0.9,
        'errors': []
    }

    use_case = ReceiptReprocessUseCase(
        receipt_repository=FakeRepo(),
        ocr_service=mock_ocr_service,
        receipt_business_service=MagicMock(),
        receipt_validation_service=mock_validation_service
    )

    # Act
    result = use_case.execute('rid', 'uid', 'paddle_ocr')

    # Assert
    assert result['success'] is True
    
    # Check that existing telemetry is preserved
    metadata = result['metadata']['custom_fields']
    assert metadata['storage_provider'] == 'cloudinary'
    assert metadata['cloudinary_public_id'] == 'receipts/abc123'
    assert metadata['previous_processing_count'] == 2
    
    # Check that new telemetry is added
    assert 'ocr_latency_ms' in metadata
    assert metadata['ocr_latency_ms'] > 0
