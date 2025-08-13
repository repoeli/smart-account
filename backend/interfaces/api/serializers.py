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
    password_confirm = serializers.CharField(max_length=128, write_only=True)
    first_name = serializers.CharField(max_length=100, required=False)
    last_name = serializers.CharField(max_length=100, required=False)
    user_type = serializers.ChoiceField(choices=['individual', 'business'], default='individual')
    company_name = serializers.CharField(max_length=255, required=False)
    business_type = serializers.CharField(max_length=100, required=False)
    tax_id = serializers.CharField(max_length=50, required=False)
    vat_number = serializers.CharField(max_length=50, required=False)
    phone = serializers.CharField(max_length=20, required=False)
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate(self, data):
        """Validate password confirmation and business fields."""
        # Validate password confirmation
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError("Passwords do not match.")
        
        # Validate business fields if user_type is business
        if data.get('user_type') == 'business':
            if not data.get('company_name', '').strip():
                raise serializers.ValidationError("Company name is required for business accounts.")
            if not data.get('business_type', '').strip():
                raise serializers.ValidationError("Business type is required for business accounts.")
        
        return data


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


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(max_length=255)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True)
    password_confirm = serializers.CharField(max_length=128, write_only=True)
    
    def validate(self, data):
        """Validate password confirmation."""
        if data.get('password') != data.get('password_confirm'):
            raise serializers.ValidationError("Passwords do not match.")
        return data


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
        
        # Check file type (align with domain validation and US-004: include PDF, WEBP; accept common JPEG aliases)
        allowed_types = [
            'image/jpeg', 'image/jpg', 'image/pjpeg', 'image/png', 'image/gif',
            'image/bmp', 'image/tiff', 'image/webp', 'application/pdf'
        ]
        
        # Log the actual content type for debugging
        print(f"DEBUG: File content type: {value.content_type}")
        print(f"DEBUG: File name: {value.name}")
        print(f"DEBUG: File size: {value.size}")
        
        # More flexible validation - check if content type contains image or pdf
        content_type = value.content_type.lower()
        is_valid = any(allowed in content_type for allowed in ['image', 'pdf', 'jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff', 'webp'])
        
        if not is_valid:
            raise serializers.ValidationError(f"File type '{value.content_type}' not supported. Allowed types: {', '.join(allowed_types)}")
        
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


class ReceiptParseResponseSerializer(serializers.Serializer):
    """
    Serializer for unified OCR parse response.
    """
    engine = serializers.ChoiceField(choices=["paddle", "openai", "fallback"]) 
    merchant = serializers.CharField(required=False, allow_null=True)
    date = serializers.CharField(required=False, allow_null=True)
    total = serializers.FloatField(required=False, allow_null=True)
    currency = serializers.CharField(required=False, allow_null=True)
    tax = serializers.FloatField(required=False, allow_null=True)
    tax_rate = serializers.FloatField(required=False, allow_null=True)
    subtotal = serializers.FloatField(required=False, allow_null=True)
    ocr_confidence = serializers.FloatField(required=False, allow_null=True)
    raw_text = serializers.CharField(required=False, allow_null=True)
    source_url = serializers.CharField(required=False, allow_null=True)
    latency_ms = serializers.IntegerField(required=False, allow_null=True)


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


class ReceiptReplaceSerializer(serializers.Serializer):
    """Serializer for replacing a receipt's file (US-004)."""
    file = serializers.FileField(allow_empty_file=False)
    reprocess = serializers.BooleanField(required=False, default=True)

class ReceiptValidateSerializer(serializers.Serializer):
    """
    Serializer for receipt validation and correction.
    """
    merchant_name = serializers.CharField(max_length=255, required=False)
    total_amount = serializers.CharField(required=False, help_text="Supports plain number or 2dp")
    date = serializers.CharField(max_length=50, required=False, allow_blank=True, help_text="Date in DD/MM/YYYY or YYYY-MM-DD format")
    vat_number = serializers.CharField(max_length=50, required=False)
    receipt_number = serializers.CharField(max_length=100, required=False)
    currency = serializers.CharField(max_length=10, required=False)
    
    def validate(self, attrs):
        # Normalize total_amount string -> Decimal-ish string with 2dp where possible
        from decimal import Decimal, InvalidOperation
        amt = attrs.get('total_amount')
        if amt is not None and amt != '':
            try:
                amt_num = Decimal(str(amt))
                if amt_num <= 0:
                    raise serializers.ValidationError({'total_amount': ['Total amount must be greater than zero.']})
                attrs['total_amount'] = str(amt_num)
            except InvalidOperation:
                raise serializers.ValidationError({'total_amount': ['Invalid amount']})

        # Normalize date: accept DD/MM/YYYY, YYYY-MM-DD; keep as DD/MM/YYYY for UI
        d = attrs.get('date')
        if d:
            from datetime import datetime
            normalized = None
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y'):
                try:
                    dt = datetime.strptime(d, fmt)
                    normalized = dt.strftime('%d/%m/%Y')
                    break
                except Exception:
                    continue
            if normalized:
                attrs['date'] = normalized
            else:
                raise serializers.ValidationError({'date': ['Invalid date format']})
        
        # Normalize currency: uppercase 3-letter if provided
        c = attrs.get('currency')
        if c:
            c_norm = str(c).strip().upper()
            if len(c_norm) not in (3, 4):
                raise serializers.ValidationError({'currency': ['Invalid currency']})
            attrs['currency'] = c_norm
        return attrs


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


class ReceiptManualCreateSerializer(serializers.Serializer):
    """Manual receipt creation (without OCR) with optional Cloudinary upload.
    Aligns with US-006: allow creating receipts by entering data manually.
    """
    filename = serializers.CharField(max_length=255, required=False, allow_blank=True)
    file_url = serializers.URLField(required=False)
    mime_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    receipt_type = serializers.ChoiceField(choices=['purchase', 'expense', 'invoice', 'bill', 'other'], required=False, default='purchase')
    merchant_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    total_amount = serializers.CharField(max_length=50, required=False, allow_blank=True)
    currency = serializers.CharField(max_length=10, required=False, allow_blank=True)
    date = serializers.CharField(max_length=50, required=False, allow_blank=True)
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    upload_to_cloudinary = serializers.BooleanField(required=False)


class ReceiptSearchRequestSerializer(serializers.Serializer):
    """
    Serializer for receipt search request parameters.
    """
    accountId = serializers.UUIDField(required=True, help_text="Account ID to scope the search")
    q = serializers.CharField(required=False, max_length=255, help_text="Search query (min 2 chars)")
    status = serializers.CharField(required=False, help_text="Comma-separated list of statuses")
    currency = serializers.CharField(required=False, help_text="Comma-separated list of currencies")
    provider = serializers.CharField(required=False, help_text="Comma-separated list of providers")
    dateFrom = serializers.DateField(required=False, help_text="Start date (YYYY-MM-DD)")
    dateTo = serializers.DateField(required=False, help_text="End date (YYYY-MM-DD)")
    amountMin = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, help_text="Minimum amount")
    amountMax = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, help_text="Maximum amount")
    confidenceMin = serializers.FloatField(required=False, min_value=0.0, max_value=1.0, help_text="Minimum confidence score")
    sort = serializers.ChoiceField(
        required=False,
        choices=[('date', 'Date'), ('amount', 'Amount'), ('merchant', 'Merchant'), ('confidence', 'Confidence')],
        default='date',
        help_text="Sort field"
    )
    order = serializers.ChoiceField(
        required=False,
        choices=[('asc', 'Ascending'), ('desc', 'Descending')],
        default='desc',
        help_text="Sort order"
    )
    limit = serializers.IntegerField(required=False, min_value=12, max_value=100, default=24, help_text="Page size (12-100)")
    cursor = serializers.CharField(required=False, help_text="Pagination cursor")

    def validate(self, attrs):
        """Validate the search parameters."""
        # Validate q length
        if attrs.get('q') and len(attrs['q']) < 2:
            raise serializers.ValidationError("Search query must be at least 2 characters long")
        
        # Validate date range
        if attrs.get('dateFrom') and attrs.get('dateTo'):
            if attrs['dateFrom'] > attrs['dateTo']:
                raise serializers.ValidationError("dateFrom must be less than or equal to dateTo")
        
        # Validate amount range
        if attrs.get('amountMin') and attrs.get('amountMax'):
            if attrs['amountMin'] > attrs['amountMax']:
                raise serializers.ValidationError("amountMin must be less than or equal to amountMax")
        
        # Validate confidence range
        if attrs.get('confidenceMin') is not None:
            if not 0.0 <= attrs['confidenceMin'] <= 1.0:
                raise serializers.ValidationError("confidenceMin must be between 0.0 and 1.0")
        
        return attrs


class ReceiptSearchItemSerializer(serializers.Serializer):
    """
    Serializer for individual receipt items in search results.
    """
    id = serializers.CharField()
    merchant = serializers.CharField()
    date = serializers.DateField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField()
    status = serializers.CharField()
    confidence = serializers.FloatField()
    provider = serializers.CharField()
    thumbnailUrl = serializers.CharField()
    has_transaction = serializers.BooleanField(required=False)


class ReceiptSearchPageInfoSerializer(serializers.Serializer):
    """
    Serializer for pagination information.
    """
    nextCursor = serializers.CharField(allow_null=True, help_text="Next page cursor")
    prevCursor = serializers.CharField(allow_null=True, help_text="Previous page cursor")
    hasNext = serializers.BooleanField(help_text="Whether there's a next page")
    hasPrev = serializers.BooleanField(help_text="Whether there's a previous page")


class ReceiptSearchResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt search response.
    """
    items = ReceiptSearchItemSerializer(many=True, help_text="List of receipts")
    pageInfo = ReceiptSearchPageInfoSerializer(help_text="Pagination information")
    totalCount = serializers.IntegerField(allow_null=True, help_text="Total count (may be null for performance)")


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


# Sprint 2.2 – Transactions & Category suggestion
class CategorySuggestQuerySerializer(serializers.Serializer):
    receiptId = serializers.UUIDField(required=False)
    merchant = serializers.CharField(required=False, allow_blank=True)


class TransactionCreateSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField(max_length=10, required=False, default='GBP')
    type = serializers.ChoiceField(choices=['income', 'expense'])
    transaction_date = serializers.DateField()
    receipt_id = serializers.UUIDField(required=False)
    category = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than 0')
        return value


class TransactionUpdateSerializer(serializers.Serializer):
    description = serializers.CharField(max_length=255, required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    currency = serializers.CharField(max_length=10, required=False)
    type = serializers.ChoiceField(choices=['income', 'expense'], required=False)
    transaction_date = serializers.DateField(required=False)
    category = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError('Amount must be greater than 0')
        return value

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


# US-015: Client Management
class ClientSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(required=False, allow_blank=True)
    company_name = serializers.CharField(max_length=255, required=False, allow_blank=True)


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