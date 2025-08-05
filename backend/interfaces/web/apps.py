"""
Django app configuration for interfaces.web.
"""

from django.apps import AppConfig


class InterfacesWebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'interfaces.web'
    label = 'interfaces_web'
    verbose_name = 'Interfaces Web' 