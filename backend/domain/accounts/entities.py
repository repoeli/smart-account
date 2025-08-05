"""
User Management Domain Entities for Smart Accounts Management System.
Following Domain-Driven Design patterns with Clean Architecture principles.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from domain.common.entities import (
    AggregateRoot, ValueObject, DomainEvent, Email, PhoneNumber, Address
)


class UserType(Enum):
    """User type enumeration."""
    INDIVIDUAL = "individual"
    ACCOUNTING_COMPANY = "accounting_company"


class UserStatus(Enum):
    """User status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class SubscriptionTier(Enum):
    """Subscription tier enumeration."""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class BusinessProfile(ValueObject):
    """Value object for business profile information."""
    
    company_name: str
    business_type: str
    tax_id: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[Address] = None
    
    def __post_init__(self):
        if not self.company_name.strip():
            raise ValueError("Company name cannot be empty")
        if not self.business_type.strip():
            raise ValueError("Business type cannot be empty")
    
    def _get_equality_components(self) -> tuple:
        return (
            self.company_name,
            self.business_type,
            self.tax_id,
            self.vat_number,
            self.address
        )


@dataclass
class NotificationPreferences(ValueObject):
    """Value object for notification preferences."""
    
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    marketing_emails: bool = False
    receipt_processing_alerts: bool = True
    payment_reminders: bool = True
    tax_deadline_reminders: bool = True
    
    def _get_equality_components(self) -> tuple:
        return (
            self.email_notifications,
            self.sms_notifications,
            self.push_notifications,
            self.marketing_emails,
            self.receipt_processing_alerts,
            self.payment_reminders,
            self.tax_deadline_reminders
        )


class UserCreatedEvent(DomainEvent):
    """Domain event for user creation."""
    
    def __init__(self, user_id: str, email: str, user_type: UserType, company_name: str):
        super().__init__()
        self.user_id = user_id
        self.email = email
        self.user_type = user_type
        self.company_name = company_name


class UserVerifiedEvent(DomainEvent):
    """Domain event for user verification."""
    
    def __init__(self, user_id: str, verified_at: datetime):
        super().__init__()
        self.user_id = user_id
        self.verified_at = verified_at


class UserProfileUpdatedEvent(DomainEvent):
    """Domain event for user profile updates."""
    
    def __init__(self, user_id: str, updated_fields: List[str]):
        super().__init__()
        self.user_id = user_id
        self.updated_fields = updated_fields


class UserSubscriptionChangedEvent(DomainEvent):
    """Domain event for subscription changes."""
    
    def __init__(self, user_id: str, new_tier: SubscriptionTier, changed_at: datetime, old_tier: Optional[SubscriptionTier] = None):
        super().__init__()
        self.user_id = user_id
        self.new_tier = new_tier
        self.changed_at = changed_at
        self.old_tier = old_tier


class User(AggregateRoot):
    """
    User aggregate root for Smart Accounts Management System.
    
    This aggregate manages user identity, authentication, and business profile
    information. It enforces business rules around user registration, verification,
    and subscription management.
    """
    
    def __init__(
        self,
        email: Email,
        password_hash: str,
        first_name: str,
        last_name: str,
        user_type: UserType,
        business_profile: BusinessProfile,
        id: Optional[str] = None,
        phone: Optional[PhoneNumber] = None,
        status: UserStatus = UserStatus.PENDING_VERIFICATION,
        subscription_tier: SubscriptionTier = SubscriptionTier.BASIC,
        notification_preferences: Optional[NotificationPreferences] = None,
        timezone: str = "Europe/London",
        language: str = "en",
        is_verified: bool = False,
        verified_at: Optional[datetime] = None,
        last_login: Optional[datetime] = None
    ):
        super().__init__(id)
        
        # Validate required fields
        if not first_name.strip():
            raise ValueError("First name cannot be empty")
        if not last_name.strip():
            raise ValueError("Last name cannot be empty")
        if not password_hash:
            raise ValueError("Password hash cannot be empty")
        
        # Core user information
        self._email = email
        self._password_hash = password_hash
        self._first_name = first_name.strip()
        self._last_name = last_name.strip()
        self._user_type = user_type
        self._business_profile = business_profile
        self._phone = phone
        self._status = status
        self._subscription_tier = subscription_tier
        self._notification_preferences = notification_preferences or NotificationPreferences()
        self._timezone = timezone
        self._language = language
        self._is_verified = is_verified
        self._verified_at = verified_at
        self._last_login = last_login
        
        # Add domain event for user creation
        self.add_domain_event(UserCreatedEvent(
            user_id=self.id,
            email=str(email),
            user_type=user_type,
            company_name=business_profile.company_name
        ))
    
    # Properties
    @property
    def email(self) -> Email:
        """Get user email."""
        return self._email
    
    @property
    def password_hash(self) -> str:
        """Get password hash."""
        return self._password_hash
    
    @property
    def first_name(self) -> str:
        """Get first name."""
        return self._first_name
    
    @property
    def last_name(self) -> str:
        """Get last name."""
        return self._last_name
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self._first_name} {self._last_name}".strip()
    
    @property
    def user_type(self) -> UserType:
        """Get user type."""
        return self._user_type
    
    @property
    def business_profile(self) -> BusinessProfile:
        """Get business profile."""
        return self._business_profile
    
    @property
    def phone(self) -> Optional[PhoneNumber]:
        """Get phone number."""
        return self._phone
    
    @property
    def status(self) -> UserStatus:
        """Get user status."""
        return self._status
    
    @property
    def subscription_tier(self) -> SubscriptionTier:
        """Get subscription tier."""
        return self._subscription_tier
    
    @property
    def notification_preferences(self) -> NotificationPreferences:
        """Get notification preferences."""
        return self._notification_preferences
    
    @property
    def timezone(self) -> str:
        """Get timezone."""
        return self._timezone
    
    @property
    def language(self) -> str:
        """Get language."""
        return self._language
    
    @property
    def is_verified(self) -> bool:
        """Check if user is verified."""
        return self._is_verified
    
    @property
    def verified_at(self) -> Optional[datetime]:
        """Get verification timestamp."""
        return self._verified_at
    
    @property
    def last_login(self) -> Optional[datetime]:
        """Get last login timestamp."""
        return self._last_login
    
    # Business methods
    def verify(self) -> None:
        """Verify the user account."""
        if self._is_verified:
            raise ValueError("User is already verified")
        
        self._is_verified = True
        self._verified_at = datetime.utcnow()
        self._status = UserStatus.ACTIVE
        
        self.add_domain_event(UserVerifiedEvent(
            user_id=self.id,
            verified_at=self._verified_at
        ))
    
    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[PhoneNumber] = None,
        business_profile: Optional[BusinessProfile] = None,
        timezone: Optional[str] = None,
        language: Optional[str] = None
    ) -> None:
        """Update user profile information."""
        updated_fields = []
        
        if first_name is not None:
            if not first_name.strip():
                raise ValueError("First name cannot be empty")
            self._first_name = first_name.strip()
            updated_fields.append("first_name")
        
        if last_name is not None:
            if not last_name.strip():
                raise ValueError("Last name cannot be empty")
            self._last_name = last_name.strip()
            updated_fields.append("last_name")
        
        if phone is not None:
            self._phone = phone
            updated_fields.append("phone")
        
        if business_profile is not None:
            self._business_profile = business_profile
            updated_fields.append("business_profile")
        
        if timezone is not None:
            self._timezone = timezone
            updated_fields.append("timezone")
        
        if language is not None:
            self._language = language
            updated_fields.append("language")
        
        if updated_fields:
            self.add_domain_event(UserProfileUpdatedEvent(
                user_id=self.id,
                updated_fields=updated_fields
            ))
    
    def update_subscription_tier(self, new_tier: SubscriptionTier) -> None:
        """Update user subscription tier."""
        if new_tier == self._subscription_tier:
            return
        
        old_tier = self._subscription_tier
        self._subscription_tier = new_tier
        
        self.add_domain_event(UserSubscriptionChangedEvent(
            user_id=self.id,
            old_tier=old_tier,
            new_tier=new_tier,
            changed_at=datetime.utcnow()
        ))
    
    def update_notification_preferences(self, preferences: NotificationPreferences) -> None:
        """Update notification preferences."""
        self._notification_preferences = preferences
    
    def record_login(self) -> None:
        """Record user login."""
        self._last_login = datetime.utcnow()
    
    def activate(self) -> None:
        """Activate user account."""
        if self._status == UserStatus.ACTIVE:
            return
        
        self._status = UserStatus.ACTIVE
    
    def deactivate(self) -> None:
        """Deactivate user account."""
        if self._status == UserStatus.INACTIVE:
            return
        
        self._status = UserStatus.INACTIVE
    
    def suspend(self) -> None:
        """Suspend user account."""
        if self._status == UserStatus.SUSPENDED:
            return
        
        self._status = UserStatus.SUSPENDED
    
    def change_password(self, new_password_hash: str) -> None:
        """Change user password."""
        if not new_password_hash:
            raise ValueError("Password hash cannot be empty")
        
        self._password_hash = new_password_hash
    
    def is_active(self) -> bool:
        """Check if user account is active."""
        return self._status == UserStatus.ACTIVE
    
    def can_access_feature(self, feature_name: str) -> bool:
        """Check if user can access a specific feature based on subscription tier."""
        if not self.is_active():
            return False
        
        # Define feature access rules based on subscription tier
        feature_access = {
            SubscriptionTier.BASIC: [
                "receipt_upload",
                "basic_reporting",
                "email_support"
            ],
            SubscriptionTier.PREMIUM: [
                "receipt_upload",
                "advanced_reporting",
                "priority_support",
                "bulk_operations",
                "api_access"
            ],
            SubscriptionTier.ENTERPRISE: [
                "receipt_upload",
                "advanced_reporting",
                "priority_support",
                "bulk_operations",
                "api_access",
                "multi_user",
                "custom_integrations",
                "dedicated_support"
            ]
        }
        
        return feature_name in feature_access.get(self._subscription_tier, [])
    
    def get_receipt_limit(self) -> int:
        """Get receipt upload limit based on subscription tier."""
        limits = {
            SubscriptionTier.BASIC: 100,
            SubscriptionTier.PREMIUM: 1000,
            SubscriptionTier.ENTERPRISE: -1  # Unlimited
        }
        return limits.get(self._subscription_tier, 100)
    
    def __str__(self) -> str:
        return f"User({self.id}, {self.email}, {self.full_name})" 