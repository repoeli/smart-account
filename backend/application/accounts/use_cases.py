"""
Application layer use cases for user management.
Implements the application services following Clean Architecture principles.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import uuid

from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from domain.accounts.entities import User, UserType, UserStatus, SubscriptionTier
from domain.accounts.repositories import UserRepository
from domain.accounts.services import UserDomainService
from infrastructure.email.services import EmailService


class UserRegistrationUseCase:
    """
    Use case for user registration.
    Handles the business logic for creating new user accounts.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        user_domain_service: UserDomainService,
        email_service: EmailService
    ):
        self.user_repository = user_repository
        self.user_domain_service = user_domain_service
        self.email_service = email_service
    
    def execute(self, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute user registration use case.
        
        Args:
            registration_data: Dictionary containing user registration data
            
        Returns:
            Dictionary with registration result
            
        Raises:
            ValidationError: If registration data is invalid
            ValueError: If user already exists
        """
        # Validate input data
        self._validate_registration_data(registration_data)
        
        # Check if user already exists
        if self.user_repository.get_by_email(registration_data['email']):
            raise ValueError("User with this email already exists")
        
        # Create user entity
        user = self._create_user_entity(registration_data)
        
        # Save user to repository
        saved_user = self.user_repository.save(user)
        
        # Send verification email
        self._send_verification_email(saved_user)
        
        return {
            'user_id': str(saved_user.id),
            'email': saved_user.email.address,
            'message': 'Registration successful. Please check your email for verification.',
            'requires_verification': True
        }
    
    def _validate_registration_data(self, data: Dict[str, Any]) -> None:
        """Validate registration data."""
        # Basic required fields for all users
        required_fields = ['email', 'password', 'first_name', 'last_name']
        
        for field in required_fields:
            if not data.get(field):
                raise ValidationError(f"{field} is required")
        
        # Validate user type specific fields
        user_type = data.get('user_type', 'individual')
        if user_type in ('business', 'accounting_company'):
            business_required_fields = ['company_name', 'business_type']
            for field in business_required_fields:
                if not data.get(field):
                    raise ValidationError(f"{field} is required for business accounts")
        
        # Validate email format
        if not self.user_domain_service.is_valid_email(data['email']):
            raise ValidationError("Invalid email format")
        
        # Validate password strength using domain service
        from domain.accounts.services import PasswordService
        password_result = PasswordService.validate_password(data['password'])
        if not password_result.is_valid:
            raise ValidationError(f"Invalid password: {'; '.join(password_result.errors)}")
    
    def _create_user_entity(self, data: Dict[str, Any]) -> User:
        """Create User entity from registration data."""
        from domain.accounts.entities import BusinessProfile, NotificationPreferences
        from domain.common.entities import Email, PhoneNumber
        
        # Determine user type
        user_type_str = data.get('user_type', 'individual')
        user_type = (
            UserType.ACCOUNTING_COMPANY
            if user_type_str in ('business', 'accounting_company')
            else UserType.INDIVIDUAL
        )
        
        # Create email value object
        email = Email(data['email'])
        
        # Create phone value object if provided
        phone = None
        if data.get('phone'):
            phone = PhoneNumber(data['phone'])
        
        # Create business profile 
        if user_type == UserType.ACCOUNTING_COMPANY:
            business_profile = BusinessProfile(
                company_name=data.get('company_name', ''),
                business_type=data.get('business_type', ''),
                tax_id=data.get('tax_id', ''),
                vat_number=data.get('vat_number', '')
            )
        else:
            # For individual users, create an empty business profile with placeholder values
            business_profile = BusinessProfile(
                company_name='-',  # Placeholder for individual users
                business_type='-',  # Placeholder for individual users
                tax_id=data.get('tax_id', ''),
                vat_number=data.get('vat_number', '')
            )
        
        # Create notification preferences
        notification_preferences = NotificationPreferences(
            email_notifications=True,
            sms_notifications=False,
            push_notifications=True,
            marketing_emails=False,
            receipt_processing_alerts=True,
            payment_reminders=True,
            tax_deadline_reminders=True
        )
        
        return User(
            email=email,
            password_hash=make_password(data['password']),
            first_name=data['first_name'],
            last_name=data['last_name'],
            user_type=user_type,
            business_profile=business_profile,
            phone=phone,
            status=UserStatus.PENDING_VERIFICATION,
            subscription_tier=SubscriptionTier.BASIC,
            notification_preferences=notification_preferences,
            timezone=data.get('timezone', 'Europe/London'),
            language=data.get('language', 'en')
        )
    
    def _send_verification_email(self, user: User) -> None:
        """Send verification email to user.""" 
        from django.conf import settings
        from django.utils import timezone
        
        # Check if auto-verification is enabled for development
        if getattr(settings, 'AUTO_VERIFY_DEVELOPMENT_USERS', False):
            # Auto-verify the user immediately
            user.status = UserStatus.ACTIVE
            user.is_verified = True
            user.verified_at = timezone.now()
            self.user_repository.save(user)
            print(f"🚀 Auto-verified user: {user.email.address} (AUTO_VERIFY_DEVELOPMENT_USERS=True)")
            return
        
        verification_token = self.user_domain_service.generate_verification_token(user)
        
        self.email_service.send_verification_email(
            to_email=user.email.address,
            user_name=f"{user.first_name} {user.last_name}",
            verification_token=verification_token
        )


class UserLoginUseCase:
    """
    Use case for user login.
    Handles authentication and session management.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        user_domain_service: UserDomainService
    ):
        self.user_repository = user_repository
        self.user_domain_service = user_domain_service
    
    def execute(self, email: str, password: str) -> Dict[str, Any]:
        """
        Execute user login use case.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dictionary with login result and JWT token
            
        Raises:
            ValueError: If credentials are invalid
            ValidationError: If account is locked or not verified
        """
        # Get user by email
        user = self.user_repository.get_by_email(email)
        if not user:
            raise ValueError("Invalid credentials")
        
        # Check if account is locked
        if self.user_domain_service.is_account_locked(user):
            raise ValidationError("Account is temporarily locked due to failed login attempts")
        
        # Verify password
        if not self.user_domain_service.verify_password(user, password):
            # Record failed login attempt
            self.user_domain_service.record_failed_login(user)
            raise ValueError("Invalid credentials")
        
        # Check if account is verified
        if not user.is_verified:
            raise ValidationError("Please verify your email address before logging in")
        
        # Reset failed login attempts on successful login
        self.user_domain_service.reset_failed_login_attempts(user)
        
        # Update last login
        from django.utils import timezone
        user.last_login = timezone.now()
        self.user_repository.save(user)
        
        # Generate JWT token
        token_data = self.user_domain_service.generate_jwt_token(user)
        
        return {
            'user_id': str(user.id),
            'email': user.email.address,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type.value,
            'access_token': token_data['access_token'],
            'refresh_token': token_data['refresh_token'],
            'expires_in': token_data['expires_in']
        }


class EmailVerificationUseCase:
    """
    Use case for email verification.
    Handles email verification token validation.
    """
    
    def __init__(
        self,
        user_repository: UserRepository,
        user_domain_service: UserDomainService
    ):
        self.user_repository = user_repository
        self.user_domain_service = user_domain_service
    
    def execute(self, token: str) -> Dict[str, Any]:
        """
        Execute email verification use case.
        
        Args:
            token: Verification token from email
            
        Returns:
            Dictionary with verification result
            
        Raises:
            ValueError: If token is invalid or expired
        """
        # Validate token
        user_id = self.user_domain_service.validate_verification_token(token)
        if not user_id:
            raise ValueError("Invalid or expired verification token")
        
        # Get user
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Verify user
        from django.utils import timezone
        user.is_verified = True
        user.verified_at = timezone.now()
        user.status = UserStatus.ACTIVE
        
        # Save user
        self.user_repository.save(user)
        
        return {
            'success': True,
            'user_id': str(user.id),
            'email': user.email.address,
            'message': 'Email verified successfully. You can now log in to your account.',
            'verified': True
        }


class UserProfileUseCase:
    """
    Use case for user profile management.
    Handles profile viewing and updating.
    """
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    def get_profile(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Get user profile.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dictionary with user profile data
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Map domain user to API shape expected by frontend
        return {
            'id': str(user.id),
            'email': user.email.address,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_type': user.user_type.value,
            'status': user.status.value,
            'subscription_tier': user.subscription_tier.value if hasattr(user.subscription_tier, 'value') else user.subscription_tier,
            'is_verified': user.is_verified,
            'phone': user.phone.number if user.phone else None,
            'business_profile': {
                'company_name': getattr(user.business_profile, 'company_name', None),
                'company_registration': None,
                'vat_number': None,
                'address': {
                    'street': getattr(getattr(user.business_profile, 'address', None), 'street', ''),
                    'city': getattr(getattr(user.business_profile, 'address', None), 'city', ''),
                    'postal_code': getattr(getattr(user.business_profile, 'address', None), 'postal_code', ''),
                    'country': getattr(getattr(user.business_profile, 'address', None), 'country', 'UK'),
                } if getattr(user.business_profile, 'address', None) else None,
            },
            'timezone': user.timezone,
            'language': user.language,
            'notification_preferences': user.notification_preferences.to_dict() if hasattr(user, 'notification_preferences') else {},
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
            'last_login': user.last_login.isoformat() if user.last_login else None,
        }
    
    def update_profile(self, user_id: uuid.UUID, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update user profile.
        
        Args:
            user_id: User's ID
            profile_data: Dictionary with profile data to update
            
        Returns:
            Dictionary with updated profile data
        """
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Update allowed fields
        allowed_fields = [
            'first_name', 'last_name', 'phone', 'address_street',
            'address_city', 'address_postal_code', 'address_country',
            'timezone', 'language', 'notification_preferences'
        ]
        
        for field in allowed_fields:
            if field in profile_data:
                setattr(user, field, profile_data[field])
        
        user.updated_at = timezone.now()
        updated_user = self.user_repository.save(user)
        
        return self.get_profile(updated_user.id) 