"""
Django Models for Smart Accounts Management System.
Following Clean Architecture principles with proper separation from domain entities.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone


class User(AbstractUser):
    """
    Django User model for Smart Accounts Management System.
    
    This model extends Django's AbstractUser and maps to our domain User entity.
    It handles the persistence layer while keeping domain logic separate.
    """
    
    # Override default ID to use UUID
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Override username to use email
    username = None
    email = models.EmailField(unique=True, db_index=True)
    
    # User type and status
    USER_TYPE_CHOICES = [
        ('individual', 'Individual'),
        ('accounting_company', 'Accounting Company'),
    ]
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='individual')
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('pending_verification', 'Pending Verification'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_verification')
    
    # Business information
    company_name = models.CharField(max_length=255)
    business_type = models.CharField(max_length=100)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    vat_number = models.CharField(max_length=50, blank=True, null=True)
    
    # Address information
    address_street = models.TextField(blank=True, null=True)
    address_city = models.CharField(max_length=100, blank=True, null=True)
    address_postal_code = models.CharField(max_length=20, blank=True, null=True)
    address_country = models.CharField(max_length=100, default='UK')
    
    # Phone number with UK format validation
    phone_regex = RegexValidator(
        regex=r'^\+44\s?\d{10,11}$',
        message="Phone number must be in UK format: +44 XXXXXXXXXX"
    )
    phone = models.CharField(validators=[phone_regex], max_length=20, blank=True, null=True)
    
    # Subscription information
    SUBSCRIPTION_TIER_CHOICES = [
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ]
    subscription_tier = models.CharField(
        max_length=20, 
        choices=SUBSCRIPTION_TIER_CHOICES, 
        default='basic'
    )
    # Stripe linkage (US-013/US-014): optional and filled via webhook processing
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    subscription_status = models.CharField(max_length=50, blank=True, null=True)
    subscription_price_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Verification and login tracking
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    last_login = models.DateTimeField(blank=True, null=True)
    
    # Preferences
    timezone = models.CharField(max_length=50, default='Europe/London')
    language = models.CharField(max_length=10, default='en')
    
    # Notification preferences (stored as JSON)
    notification_preferences = models.JSONField(default=dict)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Django User fields we don't use
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    # Meta
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['status']),
            models.Index(fields=['subscription_tier']),
            models.Index(fields=['company_name']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_verified']),
        ]
    
    # Authentication fields
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    def __str__(self):
        return f"{self.email} ({self.get_full_name()})"
    
    def get_full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        """Return the user's short name."""
        return self.first_name
    
    @property
    def is_account_active(self):
        """Check if user account is active (different from Django's is_active)."""
        return self.status == 'active'
    
    def can_access_feature(self, feature_name: str) -> bool:
        """Check if user can access a specific feature based on subscription tier."""
        if not self.is_account_active:
            return False
        
        # Define feature access rules based on subscription tier
        feature_access = {
            'basic': [
                'receipt_upload',
                'basic_reporting',
                'email_support'
            ],
            'premium': [
                'receipt_upload',
                'advanced_reporting',
                'priority_support',
                'bulk_operations',
                'api_access'
            ],
            'enterprise': [
                'receipt_upload',
                'advanced_reporting',
                'priority_support',
                'bulk_operations',
                'api_access',
                'multi_user',
                'custom_integrations',
                'dedicated_support'
            ]
        }
        
        return feature_name in feature_access.get(self.subscription_tier, [])
    
    def get_receipt_limit(self) -> int:
        """Get receipt upload limit based on subscription tier."""
        limits = {
            'basic': 100,
            'premium': 1000,
            'enterprise': -1  # Unlimited
        }
        return limits.get(self.subscription_tier, 100)


class EmailVerificationToken(models.Model):
    """
    Model for storing email verification tokens.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=255, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_tokens')
    email = models.EmailField()
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'email_verification_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_used']),
        ]
    
    def __str__(self):
        return f"Token for {self.email} (expires: {self.expires_at})"
    
    @property
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid and not used."""
        return not self.is_expired and not self.is_used


class PasswordResetToken(models.Model):
    """
    Model for storing password reset tokens.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    token = models.CharField(max_length=255, unique=True, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'password_reset_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['is_used']),
        ]
    
    def __str__(self):
        return f"Password reset token for {self.user.email} (expires: {self.expires_at})"
    
    @property
    def is_expired(self):
        """Check if token is expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if token is valid and not used."""
        return not self.is_expired and not self.is_used


class UserAuditLog(models.Model):
    """
    Model for tracking user-related audit events.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audit_logs')
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_audit_logs'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['event_type']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.event_type} for {self.user.email} at {self.created_at}"


class UserSession(models.Model):
    """
    Model for tracking user sessions.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=255, unique=True, db_index=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
            models.Index(fields=['is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} (active: {self.is_active})"
    
    @property
    def is_expired(self):
        """Check if session is expired."""
        return timezone.now() > self.expires_at


class Receipt(models.Model):
    """
    Django Receipt model for Smart Accounts Management System.
    
    This model handles the persistence layer for receipts while keeping domain logic separate.
    """
    
    # Primary key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # User relationship
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receipts')
    
    # File information
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    file_url = models.URLField(max_length=500)
    
    # Receipt status and type
    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('failed', 'Failed'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    
    TYPE_CHOICES = [
        ('purchase', 'Purchase'),
        ('expense', 'Expense'),
        ('invoice', 'Invoice'),
        ('bill', 'Bill'),
        ('other', 'Other'),
    ]
    receipt_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='purchase')
    
    # OCR extracted data (stored as JSON)
    ocr_data = models.JSONField(default=dict, blank=True)
    
    # Metadata (stored as JSON)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Error information for failed processing
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'receipts'
        verbose_name = 'Receipt'
        verbose_name_plural = 'Receipts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['receipt_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['processed_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Receipt {self.id} - {self.filename} ({self.status})"
    
    @property
    def is_processed(self):
        """Check if receipt has been processed."""
        return self.status == 'processed'
    
    @property
    def is_failed(self):
        """Check if receipt processing failed."""
        return self.status == 'failed'
    
    @property
    def total_amount(self):
        """Get total amount from OCR data."""
        return self.ocr_data.get('total_amount') if self.ocr_data else None
    
    @property
    def merchant_name(self):
        """Get merchant name from OCR data."""
        return self.ocr_data.get('merchant_name') if self.ocr_data else None
    
    @property
    def receipt_date(self):
        """Get receipt date from OCR data."""
        date_str = self.ocr_data.get('date') if self.ocr_data else None
        if date_str:
            try:
                from django.utils.dateparse import parse_datetime
                return parse_datetime(date_str)
            except:
                return None
        return None 


class Folder(models.Model):
    """
    Folder model for organizing receipts (US-006).
    Supports user-created, system, and smart folders. Metadata stored as JSON.
    """

    FOLDER_TYPE_CHOICES = [
        ('system', 'System'),
        ('user', 'User'),
        ('smart', 'Smart'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=255)
    folder_type = models.CharField(max_length=10, choices=FOLDER_TYPE_CHOICES, default='user')
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'folders'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['parent']),
            models.Index(fields=['user', 'name']),
        ]
        ordering = ['name', 'created_at']

    def __str__(self):
        return f"Folder {self.name} ({self.folder_type})"


class FolderReceipt(models.Model):
    """
    Join table mapping receipts to folders (many-to-many via explicit model).
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, related_name='folder_receipts')
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, related_name='receipt_folders')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'folder_receipts'
        constraints = [
            models.UniqueConstraint(fields=['folder', 'receipt'], name='uniq_folder_receipt'),
        ]
        indexes = [
            models.Index(fields=['folder']),
            models.Index(fields=['receipt']),
        ]


class Transaction(models.Model):
    """
    Django Transaction model (Sprint 2.2).
    Minimal fields to support creating a transaction from a receipt.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    receipt = models.ForeignKey(Receipt, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=10, default='GBP')
    type = models.CharField(max_length=10, choices=[('income', 'income'), ('expense', 'expense')])
    transaction_date = models.DateField()
    category = models.CharField(max_length=100, blank=True, null=True)
    # Optional association to Client (US-015)
    client = models.ForeignKey('Client', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'transactions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['transaction_date']),
            models.Index(fields=['type']),
            models.Index(fields=['category']),
            models.Index(fields=['client']),
        ]
        ordering = ['-transaction_date', '-created_at']

    def __str__(self):
        return f"Transaction {self.id} {self.type} {self.amount} {self.currency}"


class Client(models.Model):
    """
    Client entity for accounting companies to manage their customers (US-015).
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    vat_number = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients'
        indexes = [
            models.Index(fields=['owner']),
            models.Index(fields=['name']),
            models.Index(fields=['status']),
        ]
        ordering = ['name', 'created_at']

    def __str__(self):
        return f"Client {self.id} {self.name}"


class ClientUser(models.Model):
    """
    Join table to associate multiple users with a single client (US-016).
    This allows clients to have multiple contacts or stakeholders.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='client_users')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_clients')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'client_users'
        unique_together = ('client', 'user')
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['user']),
        ]

class Category(models.Model):
    """
    Category model for organizing receipts and transactions (US-006).
    Supports hierarchical categories.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        unique_together = ('user', 'name', 'parent')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['parent']),
            models.Index(fields=['name']),
        ]
        ordering = ['name']

    def __str__(self):
        return f"Category {self.name} for user {self.user.email}"


class Subscription(models.Model):
    """
    Subscription model for managing user plans and billing (US-013/US-014).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    stripe_subscription_id = models.CharField(max_length=255, unique=True)
    stripe_customer_id = models.CharField(max_length=255, unique=True)
    plan = models.CharField(max_length=50, choices=User.SUBSCRIPTION_TIER_CHOICES, default='basic')
    status = models.CharField(max_length=20, default='active')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'subscriptions'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['stripe_subscription_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Subscription for {self.user.email} - Plan: {self.plan} ({self.status})"


class ApplicationSettings(models.Model):
    """
    Stores application-wide admin-configurable settings (non-secrets) as JSON.
    Singleton row; use .get_solo() to retrieve or create.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    data = models.JSONField(default=dict, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_settings')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'application_settings'

    def __str__(self):
        return f"ApplicationSettings {self.id}"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create(data={})
        return obj