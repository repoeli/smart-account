"""
Django app configuration for application.receipts.
"""

from django.apps import AppConfig


class ApplicationReceiptsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'application.receipts'
    label = 'application_receipts'
    verbose_name = 'Application Receipts' 