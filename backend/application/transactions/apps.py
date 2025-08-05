"""
Django app configuration for application.transactions.
"""

from django.apps import AppConfig


class ApplicationTransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'application.transactions'
    label = 'application_transactions'
    verbose_name = 'Application Transactions' 