"""
Django app configuration for interfaces.api.
"""

from django.apps import AppConfig


class InterfacesApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interfaces.api'
    label = 'interfaces_api'
    verbose_name = 'Interfaces API' 