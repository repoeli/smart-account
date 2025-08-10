import os
import types

from unittest.mock import patch, MagicMock

from application.receipts.use_cases import ReceiptReprocessUseCase


def test_reprocess_infers_cloudinary_from_url(django_user_model):
    # Arrange: fake receipt with cloudinary file_url but missing telemetry
    class FakeReceipt:
        def __init__(self):
            self.id = 'rid'
            self.user = types.SimpleNamespace(id='uid')
            self.file_info = types.SimpleNamespace(file_url='https://res.cloudinary.com/demo/image/upload/v1/receipts/abc123.jpg', filename='x.jpg', mime_type='image/jpeg')
            self.status = types.SimpleNamespace(value='uploaded')
            self.receipt_type = types.SimpleNamespace(value='purchase')
            self.metadata = types.SimpleNamespace(custom_fields={})
            self.ocr_data = None

    class FakeRepo:
        def find_by_id(self, _):
            return FakeReceipt()
        def save(self, r):
            return r

    use_case = ReceiptReprocessUseCase(receipt_repository=FakeRepo(), ocr_service=MagicMock(), receipt_business_service=MagicMock(), receipt_validation_service=MagicMock())

    # Act
    use_case._ensure_cloudinary_metadata(FakeRepo().find_by_id('rid'))

    # Assert: cloudinary_public_id inferred
    rec = FakeRepo().find_by_id('rid')
    use_case._ensure_cloudinary_metadata(rec)
    assert rec.metadata.custom_fields.get('storage_provider') == 'cloudinary'
    assert rec.metadata.custom_fields.get('cloudinary_public_id')


def test_reprocess_migrates_external_to_cloudinary():
    class FakeReceipt:
        def __init__(self):
            self.id = 'rid'
            self.user = types.SimpleNamespace(id='uid')
            self.file_info = types.SimpleNamespace(file_url='http://example.com/image.jpg', filename='image.jpg', mime_type='image/jpeg')
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

    fake_asset = types.SimpleNamespace(secure_url='https://res.cloudinary.com/demo/image/upload/v1/receipts/xyz.jpg', public_id='receipts/xyz')

    with patch('backend.application.receipts.use_cases.requests.get') as req_get, \
         patch('backend.application.receipts.use_cases.CloudinaryStorageAdapter') as Cloud:
        req_get.return_value = types.SimpleNamespace(content=b'bytes', raise_for_status=lambda: None)
        Cloud.return_value.upload.return_value = fake_asset

        repo = FakeRepo()
        use_case = ReceiptReprocessUseCase(receipt_repository=repo, ocr_service=MagicMock(), receipt_business_service=MagicMock(), receipt_validation_service=MagicMock())
        rec = repo.find_by_id('rid')
        use_case._ensure_cloudinary_metadata(rec)
        assert 'cloudinary' == rec.metadata.custom_fields.get('storage_provider')
        assert 'receipts/xyz' == rec.metadata.custom_fields.get('cloudinary_public_id')
        assert rec.file_info.file_url.startswith('https://res.cloudinary.com/')


def test_reprocess_cloudinary_migration_failure_does_not_break():
    class FakeReceipt:
        def __init__(self):
            self.id = 'rid'
            self.user = types.SimpleNamespace(id='uid')
            self.file_info = types.SimpleNamespace(file_url='http://example.com/image.jpg', filename='image.jpg', mime_type='image/jpeg')
            self.status = types.SimpleNamespace(value='uploaded')
            self.receipt_type = types.SimpleNamespace(value='purchase')
            self.metadata = types.SimpleNamespace(custom_fields={})
            self.ocr_data = None

    class Repo:
        def __init__(self):
            self._r = FakeReceipt()
        def find_by_id(self, _):
            return self._r
        def save(self, r):
            self._r = r
            return r

    with patch('backend.application.receipts.use_cases.requests.get') as req_get, \
         patch('backend.application.receipts.use_cases.CloudinaryStorageAdapter') as Cloud:
        # simulate network ok but cloudinary upload throws
        req_get.return_value = types.SimpleNamespace(content=b'bytes', raise_for_status=lambda: None)
        Cloud.return_value.upload.side_effect = RuntimeError('cloudinary down')

        repo = Repo()
        use_case = ReceiptReprocessUseCase(receipt_repository=repo, ocr_service=MagicMock(), receipt_business_service=MagicMock(), receipt_validation_service=MagicMock())
        rec = repo.find_by_id('rid')
        # Should not raise
        use_case._ensure_cloudinary_metadata(rec)
        # Telemetry remains absent but code path completes
        assert rec.metadata.custom_fields.get('storage_provider') is None
        assert rec.file_info.file_url.startswith('http://example.com/')


