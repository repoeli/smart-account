"""
User Management Repository Interfaces for Smart Accounts Management System.
Following the Repository pattern from Domain-Driven Design.
"""

from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from domain.common.repositories import AggregateRepository, Specification, PaginationParams, PaginatedResult
from .entities import User, UserType, UserStatus, SubscriptionTier


class UserRepository(AggregateRepository[User]):
    """Repository interface for User aggregate."""
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        pass
    
    @abstractmethod
    def get_by_company_name(self, company_name: str) -> List[User]:
        """Get users by company name."""
        pass
    
    @abstractmethod
    def get_by_user_type(self, user_type: UserType) -> List[User]:
        """Get users by user type."""
        pass
    
    @abstractmethod
    def get_by_status(self, status: UserStatus) -> List[User]:
        """Get users by status."""
        pass
    
    @abstractmethod
    def get_by_subscription_tier(self, tier: SubscriptionTier) -> List[User]:
        """Get users by subscription tier."""
        pass
    
    @abstractmethod
    def get_verified_users(self) -> List[User]:
        """Get all verified users."""
        pass
    
    @abstractmethod
    def get_unverified_users(self) -> List[User]:
        """Get all unverified users."""
        pass
    
    @abstractmethod
    def get_active_users(self) -> List[User]:
        """Get all active users."""
        pass
    
    @abstractmethod
    def get_users_created_between(self, start_date: datetime, end_date: datetime) -> List[User]:
        """Get users created between two dates."""
        pass
    
    @abstractmethod
    def get_users_with_last_login_before(self, date: datetime) -> List[User]:
        """Get users who haven't logged in since a specific date."""
        pass
    
    @abstractmethod
    def count_by_user_type(self, user_type: UserType) -> int:
        """Count users by user type."""
        pass
    
    @abstractmethod
    def count_by_status(self, status: UserStatus) -> int:
        """Count users by status."""
        pass
    
    @abstractmethod
    def count_by_subscription_tier(self, tier: SubscriptionTier) -> int:
        """Count users by subscription tier."""
        pass
    
    @abstractmethod
    def email_exists(self, email: str) -> bool:
        """Check if email address already exists."""
        pass
    
    @abstractmethod
    def company_name_exists(self, company_name: str) -> bool:
        """Check if company name already exists."""
        pass


class UserQueryRepository(UserRepository):
    """User repository with advanced query capabilities."""
    
    @abstractmethod
    def find_by_specification(self, specification: Specification) -> List[User]:
        """Find users that satisfy a specification."""
        pass
    
    @abstractmethod
    def find_by_criteria(self, criteria: Dict[str, Any]) -> List[User]:
        """Find users by criteria."""
        pass
    
    @abstractmethod
    def find_paginated(
        self,
        pagination: PaginationParams,
        specification: Optional[Specification] = None,
        order_by: Optional[str] = None
    ) -> PaginatedResult:
        """Find users with pagination."""
        pass
    
    @abstractmethod
    def search_users(
        self,
        query: str,
        user_type: Optional[UserType] = None,
        status: Optional[UserStatus] = None,
        limit: int = 20
    ) -> List[User]:
        """Search users by name, email, or company name."""
        pass


# User Specifications
class UserSpecification(Specification):
    """Base specification for User entities."""
    
    def is_satisfied_by(self, user: User) -> bool:
        """Check if a user satisfies this specification."""
        pass


class UserByEmailSpecification(UserSpecification):
    """Specification to find user by email."""
    
    def __init__(self, email: str):
        self.email = email.lower()
    
    def is_satisfied_by(self, user: User) -> bool:
        return str(user.email).lower() == self.email


class UserByTypeSpecification(UserSpecification):
    """Specification to find users by type."""
    
    def __init__(self, user_type: UserType):
        self.user_type = user_type
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.user_type == self.user_type


class UserByStatusSpecification(UserSpecification):
    """Specification to find users by status."""
    
    def __init__(self, status: UserStatus):
        self.status = status
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.status == self.status


class UserBySubscriptionTierSpecification(UserSpecification):
    """Specification to find users by subscription tier."""
    
    def __init__(self, tier: SubscriptionTier):
        self.tier = tier
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.subscription_tier == self.tier


class VerifiedUserSpecification(UserSpecification):
    """Specification to find verified users."""
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.is_verified


class ActiveUserSpecification(UserSpecification):
    """Specification to find active users."""
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.is_active()


class UserCreatedAfterSpecification(UserSpecification):
    """Specification to find users created after a date."""
    
    def __init__(self, date: datetime):
        self.date = date
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.created_at >= self.date


class UserCreatedBeforeSpecification(UserSpecification):
    """Specification to find users created before a date."""
    
    def __init__(self, date: datetime):
        self.date = date
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.created_at <= self.date


class UserByCompanyNameSpecification(UserSpecification):
    """Specification to find users by company name."""
    
    def __init__(self, company_name: str):
        self.company_name = company_name.lower()
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.business_profile.company_name.lower() == self.company_name


class UserByBusinessTypeSpecification(UserSpecification):
    """Specification to find users by business type."""
    
    def __init__(self, business_type: str):
        self.business_type = business_type.lower()
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.business_profile.business_type.lower() == self.business_type


class UserWithVATNumberSpecification(UserSpecification):
    """Specification to find users with VAT number."""
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.business_profile.vat_number is not None


class UserWithTaxIdSpecification(UserSpecification):
    """Specification to find users with tax ID."""
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.business_profile.tax_id is not None


class UserByTimezoneSpecification(UserSpecification):
    """Specification to find users by timezone."""
    
    def __init__(self, timezone: str):
        self.timezone = timezone
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.timezone == self.timezone


class UserByLanguageSpecification(UserSpecification):
    """Specification to find users by language."""
    
    def __init__(self, language: str):
        self.language = language
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.language == self.language


class UserWithPhoneSpecification(UserSpecification):
    """Specification to find users with phone number."""
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.phone is not None


class UserLastLoginAfterSpecification(UserSpecification):
    """Specification to find users who logged in after a date."""
    
    def __init__(self, date: datetime):
        self.date = date
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.last_login is not None and user.last_login >= self.date


class UserLastLoginBeforeSpecification(UserSpecification):
    """Specification to find users who logged in before a date."""
    
    def __init__(self, date: datetime):
        self.date = date
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.last_login is not None and user.last_login <= self.date


class UserNeverLoggedInSpecification(UserSpecification):
    """Specification to find users who have never logged in."""
    
    def is_satisfied_by(self, user: User) -> bool:
        return user.last_login is None 