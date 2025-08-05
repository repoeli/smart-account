"""
Django app configuration for domain.transactions.
"""

from django.apps import AppConfig


class DomainTransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'domain.transactions'
    label = 'domain_transactions'
    verbose_name = 'Domain Transactions' 