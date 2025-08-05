"""
API serializers for the Smart Accounts Management System.
Defines serializers for request/response data transformation.
"""

import os
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError

from infrastructure.database.models import User
from infrastructure.ocr.services import OCRMethod


class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    """
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(min_length=8, write_only=True)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    company_name = serializers.CharField(max_length=255)
    business_type = serializers.CharField(max_length=100)
    phone = serializers.CharField(max_length=20)
    address_country = serializers.CharField(max_length=3, default='GB')
    timezone = serializers.CharField(max_length=50, default='Europe/London')
    language = serializers.CharField(max_length=10, default='en')
    subscription_tier = serializers.CharField(max_length=20, default='basic')
    
    def validate(self, attrs):
        """Validate registration data."""
        # Check if passwords match
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        
        # Check if user already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError("User with this email already exists")
        
        return attrs
    
    def validate_password(self, value):
        """Validate password strength."""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase letter, one lowercase letter, and one digit
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError("Password must contain at least one digit")
        
        return value


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    """
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate login credentials."""
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid email or password")
            
            if not user.is_verified:
                raise serializers.ValidationError("Please verify your email address before logging in")
            
            if not user.is_active:
                raise serializers.ValidationError("Account is deactivated")
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Must include email and password")
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data.
    """
    id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    user_type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'company_name',
            'business_type', 'phone', 'user_type', 'status', 'subscription_tier',
            'is_verified', 'address_street', 'address_city', 'address_postal_code',
            'address_country', 'timezone', 'language', 'notification_preferences',
            'created_at', 'last_login'
        ]
        read_only_fields = [
            'id', 'email', 'user_type', 'status', 'is_verified',
            'created_at', 'last_login'
        ]


class UserProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating user profile.
    """
    first_name = serializers.CharField(max_length=150, required=False)
    last_name = serializers.CharField(max_length=150, required=False)
    phone = serializers.CharField(max_length=20, required=False)
    address_street = serializers.CharField(max_length=255, required=False, allow_blank=True)
    address_city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    address_postal_code = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address_country = serializers.CharField(max_length=3, required=False)
    timezone = serializers.CharField(max_length=50, required=False)
    language = serializers.CharField(max_length=10, required=False)
    notification_preferences = serializers.JSONField(required=False)
    
    def validate_notification_preferences(self, value):
        """Validate notification preferences."""
        if value is not None:
            allowed_keys = ['email_notifications', 'sms_notifications', 'receipt_reminders']
            for key in value.keys():
                if key not in allowed_keys:
                    raise serializers.ValidationError(f"Invalid notification preference: {key}")
            
            for key, val in value.items():
                if not isinstance(val, bool):
                    raise serializers.ValidationError(f"Notification preference {key} must be a boolean")
        
        return value


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(max_length=255)


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request.
    """
    email = serializers.EmailField(max_length=254)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation.
    """
    token = serializers.CharField(max_length=255)
    password = serializers.CharField(min_length=8, write_only=True)
    password_confirm = serializers.CharField(min_length=8, write_only=True)
    
    def validate(self, attrs):
        """Validate password reset data."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        
        # Validate password strength
        password = attrs['password']
        if len(password) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            raise serializers.ValidationError("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            raise serializers.ValidationError("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            raise serializers.ValidationError("Password must contain at least one digit")
        
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer with additional user data.
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validate and return token with user data."""
        data = super().validate(attrs)
        
        # Add user data to response
        data['user_id'] = str(self.user.id)
        data['email'] = self.user.email
        data['first_name'] = self.user.first_name
        data['last_name'] = self.user.last_name
        data['user_type'] = self.user.user_type
        data['is_verified'] = self.user.is_verified
        
        return data


class UserResponseSerializer(serializers.Serializer):
    """
    Serializer for user response data.
    """
    id = serializers.UUIDField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    user_type = serializers.CharField()
    is_verified = serializers.BooleanField()
    message = serializers.CharField(required=False)
    requires_verification = serializers.BooleanField(required=False)
    access_token = serializers.CharField(required=False)
    refresh_token = serializers.CharField(required=False)
    expires_in = serializers.IntegerField(required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """
    Serializer for error responses.
    """
    error = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(required=False)


# Receipt Serializers
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
        # Check file size (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 10MB")
        
        # Check file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf', 'image/tiff', 'image/bmp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(f"File type not supported. Allowed types: {', '.join(allowed_types)}")
        
        # Check file extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.tiff', '.bmp']
        file_ext = os.path.splitext(value.name)[1].lower()
        if file_ext not in allowed_extensions:
            raise serializers.ValidationError(f"File extension not supported. Allowed extensions: {', '.join(allowed_extensions)}")
        
        return value


class ReceiptListSerializer(serializers.Serializer):
    """
    Serializer for receipt list response.
    """
    id = serializers.UUIDField()
    filename = serializers.CharField()
    status = serializers.CharField()
    receipt_type = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    file_url = serializers.URLField()
    ocr_data = serializers.DictField(required=False)
    metadata = serializers.DictField(required=False)


class ReceiptDetailSerializer(serializers.Serializer):
    """
    Serializer for receipt detail response.
    """
    id = serializers.UUIDField()
    filename = serializers.CharField()
    file_size = serializers.IntegerField()
    mime_type = serializers.CharField()
    file_url = serializers.URLField()
    status = serializers.CharField()
    receipt_type = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    processed_at = serializers.DateTimeField(required=False)
    ocr_data = serializers.DictField(required=False)
    metadata = serializers.DictField(required=False)


class ReceiptUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating receipt metadata.
    """
    category = serializers.CharField(max_length=100, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    is_business_expense = serializers.BooleanField(required=False, default=False)
    tax_deductible = serializers.BooleanField(required=False, default=False)
    custom_fields = serializers.DictField(required=False)
    
    def validate_tags(self, value):
        """Validate tags."""
        if value:
            for tag in value:
                if len(tag.strip()) == 0:
                    raise serializers.ValidationError("Tags cannot be empty")
                if len(tag) > 50:
                    raise serializers.ValidationError("Tags must be 50 characters or less")
        return value
    
    def validate_notes(self, value):
        """Validate notes."""
        if value and len(value.strip()) > 1000:
            raise serializers.ValidationError("Notes must be 1000 characters or less")
        return value


class ReceiptUploadResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt upload response.
    """
    success = serializers.BooleanField()
    receipt_id = serializers.UUIDField()
    file_url = serializers.URLField()
    status = serializers.CharField()
    ocr_processed = serializers.BooleanField()
    ocr_data = serializers.DictField(required=False)
    ocr_error = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    validation_errors = serializers.ListField(required=False)
    upload_error = serializers.CharField(required=False)


class ReceiptListResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt list response.
    """
    success = serializers.BooleanField()
    receipts = ReceiptListSerializer(many=True)
    total_count = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    error = serializers.CharField(required=False)


class ReceiptDetailResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt detail response.
    """
    success = serializers.BooleanField()
    receipt = ReceiptDetailSerializer()
    error = serializers.CharField(required=False)


class ReceiptUpdateResponseSerializer(serializers.Serializer):
    """
    Serializer for receipt update response.
    """
    success = serializers.BooleanField()
    receipt_id = serializers.UUIDField()
    message = serializers.CharField()
    error = serializers.CharField(required=False)
    validation_errors = serializers.ListField(required=False) 