"""
Repository implementations for Smart Accounts Management System.
Implements repository interfaces using Django ORM.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q

from domain.accounts.entities import User as DomainUser, BusinessProfile, UserType, UserStatus, SubscriptionTier
from domain.accounts.repositories import UserRepository
from domain.receipts.entities import (
    Receipt as DomainReceipt, ReceiptStatus, ReceiptType, 
    FileInfo, OCRData, ReceiptMetadata
)
from domain.receipts.repositories import ReceiptRepository
from domain.common.entities import Email, PhoneNumber, Address
from .models import User, Receipt

UserModel = get_user_model()


class DjangoUserRepository(UserRepository):
    """Django ORM implementation of UserRepository."""
    
    def save(self, user: DomainUser) -> DomainUser:
        """Save or update a user."""
        with transaction.atomic():
            try:
                # Try to find existing user
                django_user = UserModel.objects.get(id=user.id)
                # Update existing user
                django_user.email = user.email.address
                django_user.first_name = user.first_name
                django_user.last_name = user.last_name
                django_user.user_type = user.user_type.value
                django_user.status = user.status.value
                django_user.company_name = user.business_profile.company_name
                django_user.business_type = user.business_profile.business_type
                django_user.phone = user.phone.number if user.phone else None
                django_user.subscription_tier = user.subscription_tier.value
                django_user.is_verified = user.is_verified
                django_user.verified_at = user.verified_at
                django_user.last_login = user.last_login
                django_user.timezone = user.timezone
                django_user.language = user.language
                django_user.notification_preferences = user.notification_preferences
                
                # Update address if available
                if user.business_profile.address:
                    django_user.address_street = user.business_profile.address.street
                    django_user.address_city = user.business_profile.address.city
                    django_user.address_postal_code = user.business_profile.address.postal_code
                    django_user.address_country = user.business_profile.address.country
                
                django_user.save()
                
            except UserModel.DoesNotExist:
                # Create new user
                django_user = UserModel.objects.create(
                    id=user.id,
                    email=user.email.address,
                    password=user.password_hash,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    user_type=user.user_type.value,
                    status=user.status.value,
                    company_name=user.business_profile.company_name,
                    business_type=user.business_profile.business_type,
                    phone=user.phone.number if user.phone else None,
                    subscription_tier=user.subscription_tier.value,
                    is_verified=user.is_verified,
                    verified_at=user.verified_at,
                    last_login=user.last_login,
                    timezone=user.timezone,
                    language=user.language,
                    notification_preferences=user.notification_preferences,
                    address_street=user.business_profile.address.street if user.business_profile.address else None,
                    address_city=user.business_profile.address.city if user.business_profile.address else None,
                    address_postal_code=user.business_profile.address.postal_code if user.business_profile.address else None,
                    address_country=user.business_profile.address.country if user.business_profile.address else 'UK'
                )
            
            # Return domain user
            return self._to_domain_user(django_user)
    
    def find_by_id(self, user_id: str) -> Optional[DomainUser]:
        """Find a user by ID."""
        try:
            django_user = UserModel.objects.get(id=user_id)
            return self._to_domain_user(django_user)
        except UserModel.DoesNotExist:
            return None
    
    def find_by_email(self, email: str) -> Optional[DomainUser]:
        """Find a user by email."""
        try:
            django_user = UserModel.objects.get(email=email)
            return self._to_domain_user(django_user)
        except UserModel.DoesNotExist:
            return None
    
    def find_all(self, limit: int = 100, offset: int = 0) -> List[DomainUser]:
        """Find all users with pagination."""
        django_users = UserModel.objects.all()[offset:offset + limit]
        return [self._to_domain_user(user) for user in django_users]
    
    def delete(self, user_id: str) -> bool:
        """Delete a user by ID."""
        try:
            django_user = UserModel.objects.get(id=user_id)
            django_user.delete()
            return True
        except UserModel.DoesNotExist:
            return False
    
    def _to_domain_user(self, django_user: UserModel) -> DomainUser:
        """Convert Django user to domain user."""
        # Create address
        address = Address(
            street=django_user.address_street or '',
            city=django_user.address_city or '',
            postal_code=django_user.address_postal_code or '',
            country=django_user.address_country or 'UK'
        ) if django_user.address_street else None
        
        # Create business profile
        business_profile = BusinessProfile(
            company_name=django_user.company_name,
            business_type=django_user.business_type,
            address=address
        )
        
        # Create email and phone
        email = Email(django_user.email)
        phone = PhoneNumber(django_user.phone) if django_user.phone else None
        
        # Create domain user
        return DomainUser(
            id=str(django_user.id),
            email=email,
            password_hash=django_user.password,
            first_name=django_user.first_name,
            last_name=django_user.last_name,
            user_type=UserType(django_user.user_type),
            business_profile=business_profile,
            phone=phone,
            subscription_tier=django_user.subscription_tier,
            is_verified=django_user.is_verified,
            verified_at=django_user.verified_at,
            last_login=django_user.last_login,
            timezone=django_user.timezone,
            language=django_user.language,
            notification_preferences=django_user.notification_preferences
        )
    
    # Additional abstract method implementations
    def get_by_email(self, email: str) -> Optional[DomainUser]:
        """Get user by email address."""
        return self.find_by_email(email)
    
    def get_by_company_name(self, company_name: str) -> List[DomainUser]:
        """Get users by company name."""
        django_users = UserModel.objects.filter(company_name__icontains=company_name)
        return [self._to_domain_user(user) for user in django_users]
    
    def get_by_user_type(self, user_type: UserType) -> List[DomainUser]:
        """Get users by user type."""
        django_users = UserModel.objects.filter(user_type=user_type.value)
        return [self._to_domain_user(user) for user in django_users]
    
    def get_by_status(self, status: UserStatus) -> List[DomainUser]:
        """Get users by status."""
        django_users = UserModel.objects.filter(status=status.value)
        return [self._to_domain_user(user) for user in django_users]
    
    def get_by_subscription_tier(self, tier: SubscriptionTier) -> List[DomainUser]:
        """Get users by subscription tier."""
        django_users = UserModel.objects.filter(subscription_tier=tier.value)
        return [self._to_domain_user(user) for user in django_users]
    
    def get_verified_users(self) -> List[DomainUser]:
        """Get all verified users."""
        django_users = UserModel.objects.filter(is_verified=True)
        return [self._to_domain_user(user) for user in django_users]
    
    def get_unverified_users(self) -> List[DomainUser]:
        """Get all unverified users."""
        django_users = UserModel.objects.filter(is_verified=False)
        return [self._to_domain_user(user) for user in django_users]
    
    def get_active_users(self) -> List[DomainUser]:
        """Get all active users."""
        django_users = UserModel.objects.filter(status='active')
        return [self._to_domain_user(user) for user in django_users]
    
    def get_users_created_between(self, start_date: datetime, end_date: datetime) -> List[DomainUser]:
        """Get users created between two dates."""
        django_users = UserModel.objects.filter(created_at__range=(start_date, end_date))
        return [self._to_domain_user(user) for user in django_users]
    
    def get_users_with_last_login_before(self, date: datetime) -> List[DomainUser]:
        """Get users who haven't logged in since a specific date."""
        django_users = UserModel.objects.filter(last_login__lt=date)
        return [self._to_domain_user(user) for user in django_users]
    
    def count_by_user_type(self, user_type: UserType) -> int:
        """Count users by user type."""
        return UserModel.objects.filter(user_type=user_type.value).count()
    
    def count_by_status(self, status: UserStatus) -> int:
        """Count users by status."""
        return UserModel.objects.filter(status=status.value).count()
    
    def count_by_subscription_tier(self, tier: SubscriptionTier) -> int:
        """Count users by subscription tier."""
        return UserModel.objects.filter(subscription_tier=tier.value).count()
    
    def email_exists(self, email: str) -> bool:
        """Check if email address already exists."""
        return UserModel.objects.filter(email=email).exists()
    
    def company_name_exists(self, company_name: str) -> bool:
        """Check if company name already exists."""
        return UserModel.objects.filter(company_name=company_name).exists()
    
    def exists(self, user_id: str) -> bool:
        """Check if user exists."""
        return UserModel.objects.filter(id=user_id).exists()
    
    def get_all(self) -> List[DomainUser]:
        """Get all users."""
        django_users = UserModel.objects.all()
        return [self._to_domain_user(user) for user in django_users]
    
    def get_by_id(self, user_id: str) -> Optional[DomainUser]:
        """Get user by ID."""
        return self.find_by_id(user_id)
    
    def add(self, user: DomainUser) -> DomainUser:
        """Add a new user."""
        return self.save(user)
    
    def update(self, user: DomainUser) -> DomainUser:
        """Update an existing user."""
        return self.save(user)


class DjangoReceiptRepository(ReceiptRepository):
    """Django ORM implementation of ReceiptRepository."""
    
    def save(self, receipt: DomainReceipt) -> DomainReceipt:
        """Save or update a receipt."""
        with transaction.atomic():
            try:
                # Try to find existing receipt
                django_receipt = Receipt.objects.get(id=receipt.id)
                # Update existing receipt
                django_receipt.user_id = receipt.user.id
                django_receipt.filename = receipt.file_info.filename
                django_receipt.file_size = receipt.file_info.file_size
                django_receipt.mime_type = receipt.file_info.mime_type
                django_receipt.file_url = receipt.file_info.file_url
                django_receipt.status = receipt.status.value
                django_receipt.receipt_type = receipt.receipt_type.value
                django_receipt.processed_at = receipt.processed_at
                django_receipt.updated_at = receipt.updated_at
                
                # Update OCR data
                if receipt.ocr_data:
                    django_receipt.ocr_data = {
                        'merchant_name': receipt.ocr_data.merchant_name,
                        'total_amount': str(receipt.ocr_data.total_amount) if receipt.ocr_data.total_amount else None,
                        'currency': receipt.ocr_data.currency,
                        'date': receipt.ocr_data.date.isoformat() if receipt.ocr_data.date else None,
                        'vat_amount': str(receipt.ocr_data.vat_amount) if receipt.ocr_data.vat_amount else None,
                        'vat_number': receipt.ocr_data.vat_number,
                        'receipt_number': receipt.ocr_data.receipt_number,
                        'items': receipt.ocr_data.items,
                        'confidence_score': receipt.ocr_data.confidence_score,
                        'raw_text': receipt.ocr_data.raw_text
                    }
                
                # Update metadata
                if receipt.metadata:
                    django_receipt.metadata = {
                        'category': receipt.metadata.category,
                        'tags': receipt.metadata.tags,
                        'notes': receipt.metadata.notes,
                        'is_business_expense': receipt.metadata.is_business_expense,
                        'tax_deductible': receipt.metadata.tax_deductible,
                        'custom_fields': receipt.metadata.custom_fields
                    }
                
                django_receipt.save()
                
            except Receipt.DoesNotExist:
                # Create new receipt
                django_receipt = Receipt.objects.create(
                    id=receipt.id,
                    user_id=receipt.user.id,
                    filename=receipt.file_info.filename,
                    file_size=receipt.file_info.file_size,
                    mime_type=receipt.file_info.mime_type,
                    file_url=receipt.file_info.file_url,
                    status=receipt.status.value,
                    receipt_type=receipt.receipt_type.value,
                    processed_at=receipt.processed_at,
                    created_at=receipt.created_at,
                    updated_at=receipt.updated_at,
                    ocr_data={
                        'merchant_name': receipt.ocr_data.merchant_name,
                        'total_amount': str(receipt.ocr_data.total_amount) if receipt.ocr_data.total_amount else None,
                        'currency': receipt.ocr_data.currency,
                        'date': receipt.ocr_data.date.isoformat() if receipt.ocr_data.date else None,
                        'vat_amount': str(receipt.ocr_data.vat_amount) if receipt.ocr_data.vat_amount else None,
                        'vat_number': receipt.ocr_data.vat_number,
                        'receipt_number': receipt.ocr_data.receipt_number,
                        'items': receipt.ocr_data.items,
                        'confidence_score': receipt.ocr_data.confidence_score,
                        'raw_text': receipt.ocr_data.raw_text
                    } if receipt.ocr_data else {},
                    metadata={
                        'category': receipt.metadata.category,
                        'tags': receipt.metadata.tags,
                        'notes': receipt.metadata.notes,
                        'is_business_expense': receipt.metadata.is_business_expense,
                        'tax_deductible': receipt.metadata.tax_deductible,
                        'custom_fields': receipt.metadata.custom_fields
                    } if receipt.metadata else {}
                )
            
            # Return domain receipt
            return self._to_domain_receipt(django_receipt)
    
    def find_by_id(self, receipt_id: str) -> Optional[DomainReceipt]:
        """Find a receipt by ID."""
        try:
            django_receipt = Receipt.objects.get(id=receipt_id)
            return self._to_domain_receipt(django_receipt)
        except Receipt.DoesNotExist:
            return None
    
    def find_by_user(self, user: DomainUser, limit: int = 100, offset: int = 0) -> List[DomainReceipt]:
        """Find receipts by user with pagination."""
        django_receipts = Receipt.objects.filter(user_id=user.id)[offset:offset + limit]
        return [self._to_domain_receipt(receipt) for receipt in django_receipts]
    
    def find_by_status(self, user: DomainUser, status: ReceiptStatus, limit: int = 100, offset: int = 0) -> List[DomainReceipt]:
        """Find receipts by status for a specific user."""
        django_receipts = Receipt.objects.filter(
            user_id=user.id, 
            status=status.value
        )[offset:offset + limit]
        return [self._to_domain_receipt(receipt) for receipt in django_receipts]
    
    def find_by_type(self, user: DomainUser, receipt_type: ReceiptType, limit: int = 100, offset: int = 0) -> List[DomainReceipt]:
        """Find receipts by type for a specific user."""
        django_receipts = Receipt.objects.filter(
            user_id=user.id, 
            receipt_type=receipt_type.value
        )[offset:offset + limit]
        return [self._to_domain_receipt(receipt) for receipt in django_receipts]
    
    def find_by_date_range(self, user: DomainUser, start_date, end_date, limit: int = 100, offset: int = 0) -> List[DomainReceipt]:
        """Find receipts within a date range for a specific user."""
        django_receipts = Receipt.objects.filter(
            user_id=user.id,
            created_at__range=[start_date, end_date]
        )[offset:offset + limit]
        return [self._to_domain_receipt(receipt) for receipt in django_receipts]
    
    def find_by_merchant(self, user: DomainUser, merchant_name: str, limit: int = 100, offset: int = 0) -> List[DomainReceipt]:
        """Find receipts by merchant name for a specific user."""
        django_receipts = Receipt.objects.filter(
            user_id=user.id,
            ocr_data__merchant_name__icontains=merchant_name
        )[offset:offset + limit]
        return [self._to_domain_receipt(receipt) for receipt in django_receipts]
    
    def find_by_amount_range(self, user: DomainUser, min_amount: float, max_amount: float, limit: int = 100, offset: int = 0) -> List[DomainReceipt]:
        """Find receipts within an amount range for a specific user."""
        django_receipts = Receipt.objects.filter(
            user_id=user.id,
            ocr_data__total_amount__range=[min_amount, max_amount]
        )[offset:offset + limit]
        return [self._to_domain_receipt(receipt) for receipt in django_receipts]
    
    def search_receipts(self, user: DomainUser, query: str, limit: int = 100, offset: int = 0) -> List[DomainReceipt]:
        """Search receipts by text query for a specific user."""
        django_receipts = Receipt.objects.filter(
            user_id=user.id
        ).filter(
            Q(filename__icontains=query) |
            Q(ocr_data__merchant_name__icontains=query) |
            Q(ocr_data__raw_text__icontains=query) |
            Q(metadata__notes__icontains=query)
        )[offset:offset + limit]
        return [self._to_domain_receipt(receipt) for receipt in django_receipts]
    
    def delete(self, receipt_id: str) -> bool:
        """Delete a receipt by ID."""
        try:
            django_receipt = Receipt.objects.get(id=receipt_id)
            django_receipt.delete()
            return True
        except Receipt.DoesNotExist:
            return False
    
    def count_by_user(self, user: DomainUser) -> int:
        """Count total receipts for a user."""
        return Receipt.objects.filter(user_id=user.id).count()
    
    def count_by_status(self, user: DomainUser, status: ReceiptStatus) -> int:
        """Count receipts by status for a user."""
        return Receipt.objects.filter(user_id=user.id, status=status.value).count()
    
    def get_processing_receipts(self) -> List[DomainReceipt]:
        """Get all receipts that are currently being processed."""
        django_receipts = Receipt.objects.filter(status='processing')
        return [self._to_domain_receipt(receipt) for receipt in django_receipts]
    
    def get_failed_receipts(self) -> List[DomainReceipt]:
        """Get all receipts that failed processing."""
        django_receipts = Receipt.objects.filter(status='failed')
        return [self._to_domain_receipt(receipt) for receipt in django_receipts]
    
    def _to_domain_receipt(self, django_receipt: Receipt) -> DomainReceipt:
        """Convert Django receipt to domain receipt."""
        # Get user (simplified - in real implementation, you'd inject user repository)
        try:
            django_user = UserModel.objects.get(id=django_receipt.user_id)
            # Create minimal domain user for receipt
            user = DomainUser(
                id=str(django_user.id),
                email=Email(django_user.email),
                password_hash=django_user.password,
                first_name=django_user.first_name,
                last_name=django_user.last_name,
                user_type=UserType(django_user.user_type),
                business_profile=BusinessProfile(
                    company_name=django_user.company_name,
                    business_type=django_user.business_type
                )
            )
        except UserModel.DoesNotExist:
            # Handle case where user doesn't exist
            user = None
        
        # Create file info
        file_info = FileInfo(
            filename=django_receipt.filename,
            file_size=django_receipt.file_size,
            mime_type=django_receipt.mime_type,
            file_url=django_receipt.file_url
        )
        
        # Create OCR data
        ocr_data = None
        if django_receipt.ocr_data:
            ocr_data = OCRData(
                merchant_name=django_receipt.ocr_data.get('merchant_name'),
                total_amount=Decimal(django_receipt.ocr_data['total_amount']) if django_receipt.ocr_data.get('total_amount') else None,
                currency=django_receipt.ocr_data.get('currency', 'GBP'),
                date=datetime.fromisoformat(django_receipt.ocr_data['date']) if django_receipt.ocr_data.get('date') else None,
                vat_amount=Decimal(django_receipt.ocr_data['vat_amount']) if django_receipt.ocr_data.get('vat_amount') else None,
                vat_number=django_receipt.ocr_data.get('vat_number'),
                receipt_number=django_receipt.ocr_data.get('receipt_number'),
                items=django_receipt.ocr_data.get('items', []),
                confidence_score=django_receipt.ocr_data.get('confidence_score'),
                raw_text=django_receipt.ocr_data.get('raw_text')
            )
        
        # Create metadata
        metadata = None
        if django_receipt.metadata:
            metadata = ReceiptMetadata(
                category=django_receipt.metadata.get('category'),
                tags=django_receipt.metadata.get('tags', []),
                notes=django_receipt.metadata.get('notes'),
                is_business_expense=django_receipt.metadata.get('is_business_expense', False),
                tax_deductible=django_receipt.metadata.get('tax_deductible', False),
                custom_fields=django_receipt.metadata.get('custom_fields', {})
            )
        
        # Create domain receipt
        return DomainReceipt(
            id=str(django_receipt.id),
            user=user,
            file_info=file_info,
            status=ReceiptStatus(django_receipt.status),
            receipt_type=ReceiptType(django_receipt.receipt_type),
            ocr_data=ocr_data,
            metadata=metadata,
            created_at=django_receipt.created_at,
            updated_at=django_receipt.updated_at,
            processed_at=django_receipt.processed_at
        ) 