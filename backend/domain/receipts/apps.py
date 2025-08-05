"""
Django app configuration for domain.receipts.
"""

from django.apps import AppConfig


class DomainReceiptsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'domain.receipts'
    label = 'domain_receipts'
    verbose_name = 'Domain Receipts' 