"""
Django app configuration for infrastructure.payment.
"""

from django.apps import AppConfig


class InfrastructurePaymentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.payment'
    label = 'infrastructure_payment'
    verbose_name = 'Infrastructure Payment' 