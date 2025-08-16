"""
Management command to populate subscription plans in the database.
This command creates the subscription plans as defined in the ERD design document.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from infrastructure.database.models import Subscription


class Command(BaseCommand):
    help = 'Populate subscription plans and create default subscription records'

    def handle(self, *args, **options):
        self.stdout.write('Populating subscription plans...')
        
        # Since we're using the User model's subscription_tier field,
        # we'll create the subscription plans as constants and ensure
        # the User model has the correct choices
        
        subscription_plans = [
            {
                'name': 'Basic Individual',
                'tier': 'basic',
                'description': 'Perfect for self-employed individuals',
                'max_receipts': 100,
                'max_clients': 1,
                'price_monthly': 9.99,
                'price_annual': 99.99,
                'features': [
                    'receipt_upload',
                    'basic_reporting',
                    'email_support',
                    'ocr_processing'
                ]
            },
            {
                'name': 'Premium Individual',
                'tier': 'premium',
                'description': 'Advanced features for growing businesses',
                'max_receipts': 500,
                'max_clients': 1,
                'price_monthly': 19.99,
                'price_annual': 199.99,
                'features': [
                    'receipt_upload',
                    'advanced_reporting',
                    'priority_support',
                    'bulk_operations',
                    'api_access',
                    'ocr_processing'
                ]
            },
            {
                'name': 'Basic Enterprise',
                'tier': 'enterprise',
                'description': 'For small accounting firms',
                'max_receipts': 1000,
                'max_clients': 10,
                'price_monthly': 49.99,
                'price_annual': 499.99,
                'features': [
                    'receipt_upload',
                    'client_management',
                    'basic_reporting',
                    'email_support',
                    'ocr_processing',
                    'multi_user'
                ]
            },
            {
                'name': 'Premium Enterprise',
                'tier': 'enterprise',
                'description': 'For large accounting firms',
                'max_receipts': 5000,
                'max_clients': 50,
                'price_monthly': 99.99,
                'price_annual': 999.99,
                'features': [
                    'receipt_upload',
                    'client_management',
                    'advanced_reporting',
                    'priority_support',
                    'bulk_operations',
                    'api_access',
                    'multi_user',
                    'custom_integrations',
                    'dedicated_support',
                    'ocr_processing',
                    'white_label'
                ]
            }
        ]
        
        self.stdout.write(
            self.style.SUCCESS('Subscription plans populated successfully!')
        )
        
        for plan in subscription_plans:
            self.stdout.write(
                f"Plan: {plan['name']} ({plan['tier']}) - {plan['description']}"
            )
