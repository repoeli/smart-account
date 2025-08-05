"""
Django app configuration for application.subscriptions.
"""

from django.apps import AppConfig


class ApplicationSubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'application.subscriptions'
    label = 'application_subscriptions'
    verbose_name = 'Application Subscriptions' 