"""
Django app configuration for domain.accounts.
"""

from django.apps import AppConfig


class DomainAccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'domain.accounts'
    label = 'domain_accounts'
    verbose_name = 'Domain Accounts' 