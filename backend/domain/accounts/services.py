"""
User Management Domain Services for Smart Accounts Management System.
Following Domain-Driven Design patterns with Clean Architecture principles.
"""

import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Tuple
from dataclasses import dataclass

from .entities import User, UserType, UserStatus, SubscriptionTier, BusinessProfile
from domain.common.entities import Email, PhoneNumber, Address


@dataclass
class PasswordValidationResult:
    """Result of password validation."""
    
    is_valid: bool
    errors: list[str]
    strength_score: int  # 0-100


@dataclass
class EmailVerificationToken:
    """Email verification token."""
    
    token: str
    user_id: str
    email: str
    expires_at: datetime
    is_used: bool = False
    
    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if token is valid and not used."""
        return not self.is_expired() and not self.is_used


class PasswordService:
    """Domain service for password management."""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash a password using bcrypt-like approach.
        
        Args:
            password: Plain text password
            salt: Optional salt (if not provided, one will be generated)
            
        Returns:
            Tuple of (hashed_password, salt)
        """
        if not salt:
            salt = secrets.token_hex(16)
        
        # Combine password and salt
        combined = password + salt
        
        # Create hash using SHA-256
        hash_obj = hashlib.sha256()
        hash_obj.update(combined.encode('utf-8'))
        hashed_password = hash_obj.hexdigest()
        
        return hashed_password, salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password to verify
            hashed_password: Stored hash
            salt: Salt used for hashing
            
        Returns:
            True if password matches, False otherwise
        """
        expected_hash, _ = PasswordService.hash_password(password, salt)
        return expected_hash == hashed_password
    
    @staticmethod
    def validate_password(password: str) -> PasswordValidationResult:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            PasswordValidationResult with validation details
        """
        errors = []
        strength_score = 0
        
        # Check minimum length
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        else:
            strength_score += 20
        
        # Check for uppercase letters
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        else:
            strength_score += 20
        
        # Check for lowercase letters
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        else:
            strength_score += 20
        
        # Check for numbers
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        else:
            strength_score += 20
        
        # Check for special characters
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        else:
            strength_score += 20
        
        # Check for common patterns
        common_patterns = [
            'password', '123456', 'qwerty', 'admin', 'user',
            'letmein', 'welcome', 'monkey', 'dragon'
        ]
        
        password_lower = password.lower()
        for pattern in common_patterns:
            if pattern in password_lower:
                errors.append("Password contains common patterns that are not allowed")
                strength_score = max(0, strength_score - 30)
                break
        
        # Check for repeated characters
        if re.search(r'(.)\1{2,}', password):
            errors.append("Password contains too many repeated characters")
            strength_score = max(0, strength_score - 20)
        
        # Check for sequential characters
        if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password_lower):
            errors.append("Password contains sequential characters")
            strength_score = max(0, strength_score - 20)
        
        is_valid = len(errors) == 0 and strength_score >= 60
        
        return PasswordValidationResult(
            is_valid=is_valid,
            errors=errors,
            strength_score=min(100, strength_score)
        )


class EmailVerificationService:
    """Domain service for email verification."""
    
    @staticmethod
    def generate_verification_token(user_id: str, email: str, expiry_hours: int = 24) -> EmailVerificationToken:
        """
        Generate an email verification token.
        
        Args:
            user_id: User ID
            email: Email address to verify
            expiry_hours: Hours until token expires
            
        Returns:
            EmailVerificationToken
        """
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        return EmailVerificationToken(
            token=token,
            user_id=user_id,
            email=email,
            expires_at=expires_at
        )
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid format, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


class UserRegistrationService:
    """Domain service for user registration validation."""
    
    @staticmethod
    def validate_registration_data(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        company_name: str,
        business_type: str,
        user_type: UserType
    ) -> Tuple[bool, list[str]]:
        """
        Validate user registration data.
        
        Args:
            email: Email address
            password: Password
            first_name: First name
            last_name: Last name
            company_name: Company name
            business_type: Business type
            user_type: User type
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate email
        if not EmailVerificationService.validate_email_format(email):
            errors.append("Invalid email format")
        
        # Validate password
        password_result = PasswordService.validate_password(password)
        if not password_result.is_valid:
            errors.extend(password_result.errors)
        
        # Validate names
        if not first_name.strip():
            errors.append("First name is required")
        elif len(first_name.strip()) < 2:
            errors.append("First name must be at least 2 characters")
        
        if not last_name.strip():
            errors.append("Last name is required")
        elif len(last_name.strip()) < 2:
            errors.append("Last name must be at least 2 characters")
        
        # Validate user type specific requirements
        if user_type == UserType.ACCOUNTING_COMPANY:
            # Validate company information for business users only
            if not company_name.strip():
                errors.append("Company name is required")
            elif len(company_name.strip()) < 2:
                errors.append("Company name must be at least 2 characters")
            elif len(company_name.strip()) < 5:
                errors.append("Accounting company name must be at least 5 characters")
            
            if not business_type.strip():
                errors.append("Business type is required")
        
        is_valid = len(errors) == 0
        
        return is_valid, errors
    
    @staticmethod
    def create_user(
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        company_name: str,
        business_type: str,
        user_type: UserType,
        phone: Optional[str] = None,
        address: Optional[Address] = None,
        tax_id: Optional[str] = None,
        vat_number: Optional[str] = None
    ) -> User:
        """
        Create a new user with validated data.
        
        Args:
            email: Email address
            password: Plain text password
            first_name: First name
            last_name: Last name
            company_name: Company name
            business_type: Business type
            user_type: User type
            phone: Optional phone number
            address: Optional address
            tax_id: Optional tax ID
            vat_number: Optional VAT number
            
        Returns:
            New User instance
            
        Raises:
            ValueError: If validation fails
        """
        # Validate input data
        is_valid, errors = UserRegistrationService.validate_registration_data(
            email, password, first_name, last_name, company_name, business_type, user_type
        )
        
        if not is_valid:
            raise ValueError(f"Invalid registration data: {'; '.join(errors)}")
        
        # Hash password
        hashed_password, _ = PasswordService.hash_password(password)
        
        # Create business profile
        business_profile = BusinessProfile(
            company_name=company_name.strip(),
            business_type=business_type.strip(),
            tax_id=tax_id,
            vat_number=vat_number,
            address=address
        )
        
        # Create phone number if provided
        phone_number = None
        if phone:
            phone_number = PhoneNumber(phone)
        
        # Create email object
        email_obj = Email(email)
        
        # Determine initial subscription tier
        initial_tier = SubscriptionTier.BASIC
        
        # Create user
        user = User(
            email=email_obj,
            password_hash=hashed_password,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            user_type=user_type,
            business_profile=business_profile,
            phone=phone_number
        )
        
        return user


class UserProfileService:
    """Domain service for user profile management."""
    
    @staticmethod
    def validate_profile_update(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company_name: Optional[str] = None,
        business_type: Optional[str] = None
    ) -> Tuple[bool, list[str]]:
        """
        Validate profile update data.
        
        Args:
            first_name: New first name
            last_name: New last name
            company_name: New company name
            business_type: New business type
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if first_name is not None:
            if not first_name.strip():
                errors.append("First name cannot be empty")
            elif len(first_name.strip()) < 2:
                errors.append("First name must be at least 2 characters")
        
        if last_name is not None:
            if not last_name.strip():
                errors.append("Last name cannot be empty")
            elif len(last_name.strip()) < 2:
                errors.append("Last name must be at least 2 characters")
        
        if company_name is not None:
            if not company_name.strip():
                errors.append("Company name cannot be empty")
            elif len(company_name.strip()) < 2:
                errors.append("Company name must be at least 2 characters")
        
        if business_type is not None:
            if not business_type.strip():
                errors.append("Business type cannot be empty")
        
        is_valid = len(errors) == 0
        
        return is_valid, errors
    
    @staticmethod
    def update_user_profile(
        user: User,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        company_name: Optional[str] = None,
        business_type: Optional[str] = None,
        tax_id: Optional[str] = None,
        vat_number: Optional[str] = None,
        address: Optional[Address] = None,
        timezone: Optional[str] = None,
        language: Optional[str] = None
    ) -> None:
        """
        Update user profile with validated data.
        
        Args:
            user: User to update
            first_name: New first name
            last_name: New last name
            phone: New phone number
            company_name: New company name
            business_type: New business type
            tax_id: New tax ID
            vat_number: New VAT number
            address: New address
            timezone: New timezone
            language: New language
            
        Raises:
            ValueError: If validation fails
        """
        # Validate input data
        is_valid, errors = UserProfileService.validate_profile_update(
            first_name, last_name, company_name, business_type
        )
        
        if not is_valid:
            raise ValueError(f"Invalid profile data: {'; '.join(errors)}")
        
        # Create new business profile if needed
        business_profile = None
        if any([company_name, business_type, tax_id, vat_number, address]):
            current_profile = user.business_profile
            business_profile = BusinessProfile(
                company_name=company_name or current_profile.company_name,
                business_type=business_type or current_profile.business_type,
                tax_id=tax_id or current_profile.tax_id,
                vat_number=vat_number or current_profile.vat_number,
                address=address or current_profile.address
            )
        
        # Create phone number if provided
        phone_number = None
        if phone:
            phone_number = PhoneNumber(phone)
        
        # Update user profile
        user.update_profile(
            first_name=first_name,
            last_name=last_name,
            phone=phone_number,
            business_profile=business_profile,
            timezone=timezone,
            language=language
        )


class UserSubscriptionService:
    """Domain service for user subscription management."""
    
    @staticmethod
    def can_upgrade_subscription(user: User, new_tier: SubscriptionTier) -> bool:
        """
        Check if user can upgrade to a new subscription tier.
        
        Args:
            user: Current user
            new_tier: New subscription tier
            
        Returns:
            True if upgrade is allowed, False otherwise
        """
        # Define upgrade paths
        upgrade_paths = {
            SubscriptionTier.BASIC: [SubscriptionTier.PREMIUM, SubscriptionTier.ENTERPRISE],
            SubscriptionTier.PREMIUM: [SubscriptionTier.ENTERPRISE],
            SubscriptionTier.ENTERPRISE: []
        }
        
        current_tier = user.subscription_tier
        allowed_upgrades = upgrade_paths.get(current_tier, [])
        
        return new_tier in allowed_upgrades
    
    @staticmethod
    def can_downgrade_subscription(user: User, new_tier: SubscriptionTier) -> bool:
        """
        Check if user can downgrade to a new subscription tier.
        
        Args:
            user: Current user
            new_tier: New subscription tier
            
        Returns:
            True if downgrade is allowed, False otherwise
        """
        # Define downgrade paths
        downgrade_paths = {
            SubscriptionTier.ENTERPRISE: [SubscriptionTier.PREMIUM, SubscriptionTier.BASIC],
            SubscriptionTier.PREMIUM: [SubscriptionTier.BASIC],
            SubscriptionTier.BASIC: []
        }
        
        current_tier = user.subscription_tier
        allowed_downgrades = downgrade_paths.get(current_tier, [])
        
        return new_tier in allowed_downgrades
    
    @staticmethod
    def get_subscription_features(tier: SubscriptionTier) -> list[str]:
        """
        Get features available for a subscription tier.
        
        Args:
            tier: Subscription tier
            
        Returns:
            List of feature names
        """
        features = {
            SubscriptionTier.BASIC: [
                "receipt_upload",
                "basic_reporting",
                "email_support",
                "mobile_app_access"
            ],
            SubscriptionTier.PREMIUM: [
                "receipt_upload",
                "advanced_reporting",
                "priority_support",
                "bulk_operations",
                "api_access",
                "mobile_app_access",
                "custom_categories",
                "export_formats"
            ],
            SubscriptionTier.ENTERPRISE: [
                "receipt_upload",
                "advanced_reporting",
                "priority_support",
                "bulk_operations",
                "api_access",
                "mobile_app_access",
                "custom_categories",
                "export_formats",
                "multi_user",
                "custom_integrations",
                "dedicated_support",
                "white_label",
                "advanced_analytics"
            ]
        }
        
        return features.get(tier, [])
    
    @staticmethod
    def get_subscription_limits(tier: SubscriptionTier) -> dict[str, int]:
        """
        Get usage limits for a subscription tier.
        
        Args:
            tier: Subscription tier
            
        Returns:
            Dictionary of limit types and values
        """
        limits = {
            SubscriptionTier.BASIC: {
                "receipts_per_month": 100,
                "api_calls_per_month": 1000,
                "storage_gb": 1,
                "users": 1
            },
            SubscriptionTier.PREMIUM: {
                "receipts_per_month": 1000,
                "api_calls_per_month": 10000,
                "storage_gb": 10,
                "users": 5
            },
            SubscriptionTier.ENTERPRISE: {
                "receipts_per_month": -1,  # Unlimited
                "api_calls_per_month": -1,  # Unlimited
                "storage_gb": 100,
                "users": -1  # Unlimited
            }
        }
        
        return limits.get(tier, {})


class UserDomainService:
    """
    Main domain service for user management operations.
    Provides a unified interface for user-related domain operations.
    """
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email format is valid."""
        return EmailVerificationService.validate_email_format(email)
    
    @staticmethod
    def is_valid_password(password: str) -> bool:
        """Check if password meets security requirements."""
        result = PasswordService.validate_password(password)
        return result.is_valid
    
    @staticmethod
    def verify_password(user: User, password: str) -> bool:
        """Verify user password."""
        # Use Django's password verification with the correct attribute
        from django.contrib.auth.hashers import check_password
        return check_password(password, user.password_hash)
    
    @staticmethod
    def validate_user_registration(user: User) -> None:
        """Validate user registration data."""
        is_valid, errors = UserRegistrationService.validate_registration_data(
            user.email.address,
            "password_placeholder",  # Password is already hashed at this point
            user.first_name,
            user.last_name,
            user.business_profile.company_name,
            user.business_profile.business_type,
            user.user_type
        )
        
        if not is_valid:
            raise ValueError(f"Invalid registration data: {'; '.join(errors)}")
    
    @staticmethod
    def generate_verification_token(user: User) -> str:
        """Generate email verification token."""
        token_obj = EmailVerificationService.generate_verification_token(
            str(user.id),
            user.email.address
        )
        return token_obj.token
    
    @staticmethod
    def validate_verification_token(token: str) -> Optional[str]:
        """Validate verification token and return user ID."""
        # This would need to be implemented with token storage/validation
        # For now, we'll use a placeholder
        # In a real implementation, this would check against stored tokens
        return None
    
    @staticmethod
    def is_account_locked(user: User) -> bool:
        """Check if user account is locked due to failed login attempts."""
        # This would need to be implemented with failed login tracking
        # For now, we'll use a placeholder
        return False
    
    @staticmethod
    def record_failed_login(user: User) -> None:
        """Record a failed login attempt."""
        # This would need to be implemented with failed login tracking
        # For now, we'll use a placeholder
        pass
    
    @staticmethod
    def reset_failed_login_attempts(user: User) -> None:
        """Reset failed login attempts counter."""
        # This would need to be implemented with failed login tracking
        # For now, we'll use a placeholder
        pass
    
    @staticmethod
    def generate_jwt_token(user: User) -> dict[str, any]:
        """Generate JWT token for user."""
        # This would need to be implemented with JWT token generation
        # For now, we'll use a placeholder
        return {
            'access_token': 'placeholder_access_token',
            'refresh_token': 'placeholder_refresh_token',
            'expires_in': 3600
        } 