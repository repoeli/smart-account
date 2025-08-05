"""
Django app configuration for infrastructure.ocr.
"""

from django.apps import AppConfig


class InfrastructureOcrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'infrastructure.ocr'
    label = 'infrastructure_ocr'
    verbose_name = 'Infrastructure OCR' 