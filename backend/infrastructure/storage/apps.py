"""
Django app configuration for infrastructure.storage.
"""

from django.apps import AppConfig


class InfrastructureStorageConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.storage'
    label = 'infrastructure_storage'
    verbose_name = 'Infrastructure Storage' 