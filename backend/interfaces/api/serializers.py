"""
API serializers for request/response data transformation.
Defines serializers for all API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from infrastructure.ocr.services import OCRMethod

User = get_user_model()


class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    """
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    company_name = serializers.CharField(max_length=255, required=False)
    business_type = serializers.CharField(max_length=100, required=False)
    tax_id = serializers.CharField(max_length=50, required=False)
    vat_number = serializers.CharField(max_length=50, required=False)
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(max_length=128, write_only=True)


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(max_length=255)


class UserProfileSerializer(serializers.Serializer):
    """
    Serializer for user profile.
    """
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    company_name = serializers.CharField(max_length=255, required=False)
    business_type = serializers.CharField(max_length=100, required=False)
    tax_id = serializers.CharField(max_length=50, required=False)
    vat_number = serializers.CharField(max_length=50, required=False)
    phone = serializers.CharField(max_length=20, required=False)
    address_line_1 = serializers.CharField(max_length=255, required=False)
    address_line_2 = serializers.CharField(max_length=255, required=False)
    city = serializers.CharField(max_length=100, required=False)
    state = serializers.CharField(max_length=100, required=False)
    postal_code = serializers.CharField(max_length=20, required=False)
    country = serializers.CharField(max_length=100, required=False)
    timezone = serializers.CharField(max_length=50, required=False)
    language = serializers.CharField(max_length=10, required=False)


class ReceiptUploadSerializer(serializers.Serializer):
    """
    Serializer for receipt upload.
    """
    file = serializers.FileField(
        max_length=255,
        allow_empty_file=False,
        use_url=False
    )
    receipt_type = serializers.ChoiceField(
        choices=[
            ('purchase', 'Purchase'),
            ('expense', 'Expense'),
            ('invoice', 'Invoice'),
            ('bill', 'Bill'),
            ('other', 'Other'),
        ],
        default='purchase'
    )
    ocr_method = serializers.ChoiceField(
        choices=[
            ('paddle_ocr', 'PaddleOCR (Open Source)'),
            ('openai_vision', 'OpenAI Vision API'),
            ('auto', 'Auto (Best Available)')
        ],
        default='auto',
        required=False,
        help_text="OCR method to use for text extraction"
    )
    
    def validate_file(self, value):
        """Validate uploaded file."""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB.")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError("Only image files are allowed.")
        
        return value


class ReceiptUploadResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt upload response.
    """
    success = serializers.BooleanField()
    receipt_id = serializers.CharField(required=False)
    file_url = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    ocr_processed = serializers.BooleanField(required=False)
    ocr_data = serializers.DictField(required=False)
    ocr_error = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class ReceiptReprocessSerializer(serializers.Serializer):
    """
    Serializer for receipt reprocessing.
    """
    ocr_method = serializers.ChoiceField(
        choices=[
            ('paddle_ocr', 'PaddleOCR (Open Source)'),
            ('openai_vision', 'OpenAI Vision API'),
            ('auto', 'Auto (Best Available)')
        ],
        help_text="OCR method to use for reprocessing"
    )


class ReceiptValidateSerializer(serializers.Serializer):
    """
    Serializer for receipt validation and correction.
    """
    merchant_name = serializers.CharField(max_length=255, required=False)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    date = serializers.CharField(max_length=50, required=False, help_text="Date in DD/MM/YYYY format")
    vat_number = serializers.CharField(max_length=50, required=False)
    receipt_number = serializers.CharField(max_length=100, required=False)
    
    def validate_total_amount(self, value):
        """Validate total amount."""
        if value and value <= 0:
            raise serializers.ValidationError("Total amount must be greater than zero.")
        return value


class ReceiptCategorizeSerializer(serializers.Serializer):
    """
    Serializer for receipt categorization.
    """
    # This serializer is mainly for API consistency
    # The categorization is done automatically by the system
    pass


class ReceiptUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating receipt metadata.
    """
    category = serializers.CharField(max_length=100, required=False)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )
    notes = serializers.CharField(max_length=1000, required=False)
    is_business_expense = serializers.BooleanField(required=False)
    tax_deductible = serializers.BooleanField(required=False)
    custom_fields = serializers.DictField(required=False)


class ReceiptListResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt list response.
    """
    success = serializers.BooleanField()
    receipts = serializers.ListField(child=serializers.DictField())
    total_count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    error = serializers.CharField(required=False)


class ReceiptDetailResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt detail response.
    """
    success = serializers.BooleanField()
    receipt = serializers.DictField(required=False)
    error = serializers.CharField(required=False)


class ReceiptStatisticsResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt statistics response.
    """
    success = serializers.BooleanField()
    statistics = serializers.DictField(required=False)
    error = serializers.CharField(required=False)


class ReceiptReprocessResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt reprocess response.
    """
    success = serializers.BooleanField()
    receipt_id = serializers.CharField(required=False)
    ocr_method = serializers.CharField(required=False)
    ocr_data = serializers.DictField(required=False)
    error = serializers.CharField(required=False)


class ReceiptValidateResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt validation response.
    """
    success = serializers.BooleanField()
    receipt_id = serializers.CharField(required=False)
    validation_errors = serializers.ListField(child=serializers.CharField(), required=False)
    suggestions = serializers.DictField(required=False)
    quality_score = serializers.FloatField(required=False)
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


class ReceiptCategorizeResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt categorization response.
    """
    success = serializers.BooleanField()
    receipt_id = serializers.CharField(required=False)
    suggested_category = serializers.CharField(required=False)
    expense_type = serializers.CharField(required=False)
    is_business_expense = serializers.BooleanField(required=False)
    tax_deductible_amount = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    error = serializers.CharField(required=False)


# US-006: Receipt Management and Organization Serializers

class CreateFolderSerializer(serializers.Serializer):
    """
    Serializer for creating a folder.
    """
    name = serializers.CharField(max_length=100)
    parent_id = serializers.CharField(required=False, allow_null=True)
    description = serializers.CharField(max_length=500, required=False)
    icon = serializers.CharField(max_length=50, required=False)
    color = serializers.CharField(max_length=7, required=False)  # Hex color


class MoveFolderSerializer(serializers.Serializer):
    """
    Serializer for moving a folder.
    """
    new_parent_id = serializers.CharField(required=False, allow_null=True)


class SearchReceiptsSerializer(serializers.Serializer):
    """
    Serializer for receipt search.
    """
    query = serializers.CharField(required=False)
    merchant_names = serializers.ListField(child=serializers.CharField(), required=False)
    categories = serializers.ListField(child=serializers.CharField(), required=False)
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    date_from = serializers.DateTimeField(required=False)
    date_to = serializers.DateTimeField(required=False)
    amount_min = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    amount_max = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    folder_ids = serializers.ListField(child=serializers.CharField(), required=False)
    receipt_types = serializers.ListField(child=serializers.CharField(), required=False)
    statuses = serializers.ListField(child=serializers.CharField(), required=False)
    is_business_expense = serializers.BooleanField(required=False)
    sort_field = serializers.ChoiceField(
        choices=['date', 'amount', 'merchant_name', 'created_at', 'updated_at', 'category'],
        default='date'
    )
    sort_direction = serializers.ChoiceField(choices=['asc', 'desc'], default='desc')
    limit = serializers.IntegerField(default=50, min_value=1, max_value=200)
    offset = serializers.IntegerField(default=0, min_value=0)


class AddTagsSerializer(serializers.Serializer):
    """
    Serializer for adding tags to receipt.
    """
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        min_length=1,
        max_length=10
    )


class BulkOperationSerializer(serializers.Serializer):
    """
    Serializer for bulk operations.
    """
    receipt_ids = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(
        choices=[
            'add_tags', 'remove_tags', 'categorize',
            'mark_business', 'archive', 'delete'
        ]
    )
    params = serializers.DictField(required=False)


class MoveReceiptsToFolderSerializer(serializers.Serializer):
    """
    Serializer for moving receipts to folder.
    """
    receipt_ids = serializers.ListField(
        child=serializers.CharField(),
        min_length=1,
        max_length=100
    )


class FolderResponseSerializer(serializers.Serializer):
    """
    Serializer for folder response.
    """
    id = serializers.CharField()
    name = serializers.CharField()
    folder_type = serializers.CharField()
    parent_id = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    icon = serializers.CharField(required=False)
    color = serializers.CharField(required=False)
    is_favorite = serializers.BooleanField()
    receipt_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class SearchResultsSerializer(serializers.Serializer):
    """
    Serializer for search results response.
    """
    success = serializers.BooleanField()
    receipts = serializers.ListField(child=serializers.DictField())
    total_count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    error = serializers.CharField(required=False)


class UserStatisticsResponseSerializer(serializers.Serializer):
    """
    Serializer for user statistics response.
    """
    success = serializers.BooleanField()
    statistics = serializers.DictField(required=False)
    error = serializers.CharField(required=False) 