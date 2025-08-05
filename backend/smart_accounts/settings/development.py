"""
Development settings for Smart Accounts Management System.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Development-specific apps
INSTALLED_APPS += [
    'debug_toolbar',
]

# Development-specific middleware
MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Debug Toolbar Configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Email Configuration for Development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_USE_TLS = False

# Database Configuration for Development
# Using PostgreSQL from Docker container
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'smart_accounts_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',  # Default PostgreSQL password
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# CORS Configuration for Development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Static files configuration for development
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files configuration for development
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Logging for development
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}

# Cache configuration for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Celery configuration for development
CELERY_BROKER_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# OCR Configuration for Development
OCR_PROVIDER = env('OCR_PROVIDER', default='openai_vision')
OPENAI_API_KEY = env('OPENAI_API_KEY', default='your-openai-api-key')

# Stripe Configuration for Development
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY', default='pk_test_your-stripe-key')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='sk_test_your-stripe-key')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='whsec_your-webhook-secret')

# AWS Configuration for Development
AWS_SES_ACCESS_KEY_ID = env('AWS_SES_ACCESS_KEY_ID', default='your-ses-access-key')
AWS_SES_SECRET_ACCESS_KEY = env('AWS_SES_SECRET_ACCESS_KEY', default='your-ses-secret-key')
AWS_SES_REGION = env('AWS_SES_REGION', default='eu-west-1')

# Cloudinary Configuration for Development
CLOUDINARY_CLOUD_NAME = env('CLOUDINARY_CLOUD_NAME', default='your-cloud-name')
CLOUDINARY_API_KEY = env('CLOUDINARY_API_KEY', default='your-api-key')
CLOUDINARY_API_SECRET = env('CLOUDINARY_API_SECRET', default='your-api-secret') 