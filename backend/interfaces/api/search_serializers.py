"""
Serializers for receipt search and cursor pagination.
"""

from rest_framework import serializers


class ReceiptSearchRequestSerializer(serializers.Serializer):
    """
    Serializer for receipt search request parameters.
    """
    accountId = serializers.UUIDField(help_text="Required: Account ID to scope the query")
    q = serializers.CharField(required=False, min_length=2, help_text="Search query (min 2 chars)")
    status = serializers.CharField(required=False, help_text="Comma-separated status values: processed,failed")
    currency = serializers.CharField(required=False, help_text="Comma-separated currency codes: GBP,USD")
    provider = serializers.CharField(required=False, help_text="Comma-separated provider names: cloudinary")
    dateFrom = serializers.DateField(required=False, help_text="Start date (YYYY-MM-DD)")
    dateTo = serializers.DateField(required=False, help_text="End date (YYYY-MM-DD)")
    amountMin = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, help_text="Minimum amount")
    amountMax = serializers.DecimalField(required=False, max_digits=10, decimal_places=2, help_text="Maximum amount")
    confidenceMin = serializers.FloatField(required=False, min_value=0.0, max_value=1.0, help_text="Minimum confidence (0-1)")
    sort = serializers.ChoiceField(
        choices=['date', 'amount', 'merchant', 'confidence'],
        default='date',
        help_text="Sort field"
    )
    order = serializers.ChoiceField(
        choices=['asc', 'desc'],
        default='desc',
        help_text="Sort order"
    )
    limit = serializers.IntegerField(
        default=24,
        min_value=12,
        max_value=100,
        help_text="Page size (12-100)"
    )
    cursor = serializers.CharField(required=False, help_text="Cursor for pagination")

    def validate(self, data):
        """Validate date and amount ranges."""
        date_from = data.get('dateFrom')
        date_to = data.get('dateTo')
        amount_min = data.get('amountMin')
        amount_max = data.get('amountMax')

        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("dateFrom must be less than or equal to dateTo")

        if amount_min and amount_max and amount_min > amount_max:
            raise serializers.ValidationError("amountMin must be less than or equal to amountMax")

        return data


class ReceiptSearchItemSerializer(serializers.Serializer):
    """
    Serializer for individual receipt items in search results.
    """
    id = serializers.CharField(help_text="Receipt ID")
    merchant = serializers.CharField(help_text="Merchant name")
    date = serializers.DateField(help_text="Receipt date")
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, help_text="Total amount")
    currency = serializers.CharField(help_text="Currency code")
    status = serializers.CharField(help_text="Processing status")
    confidence = serializers.FloatField(help_text="OCR confidence score")
    provider = serializers.CharField(help_text="Storage provider")
    thumbnailUrl = serializers.CharField(help_text="Thumbnail URL")


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
