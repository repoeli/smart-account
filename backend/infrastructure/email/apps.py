"""
Django app configuration for infrastructure.email.
"""

from django.apps import AppConfig


class InfrastructureEmailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.email'
    label = 'infrastructure_email'
    verbose_name = 'Infrastructure Email' 