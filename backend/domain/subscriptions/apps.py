"""
Django app configuration for domain.subscriptions.
"""

from django.apps import AppConfig


class DomainSubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'domain.subscriptions'
    label = 'domain_subscriptions'
    verbose_name = 'Domain Subscriptions' 