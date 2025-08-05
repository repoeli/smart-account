"""
Django app configuration for infrastructure.database.
"""

from django.apps import AppConfig


class DatabaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.database'
    label = 'infrastructure_database'
    verbose_name = 'Database Infrastructure' 