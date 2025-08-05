"""
Django app configuration for application.accounts.
"""

from django.apps import AppConfig


class ApplicationAccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'application.accounts'
    label = 'application_accounts'
    verbose_name = 'Application Accounts' 