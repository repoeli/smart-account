"""
Staging settings for Smart Accounts Management System.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['staging.smartaccounts.com'])

# Security settings for staging
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 31536000
SECURE_REDIRECT_EXEMPT = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
X_FRAME_OPTIONS = 'DENY'

# Database Configuration for Staging
DATABASES = {
    'default': env.db('DATABASE_URL')
}

# Email Configuration for Staging
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_ACCESS_KEY_ID = env('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = env('AWS_SES_SECRET_ACCESS_KEY')
AWS_SES_REGION_NAME = env('AWS_SES_REGION', default='eu-west-1')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@staging.smartaccounts.com')

# Static files configuration for staging
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Media files configuration for staging
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cache configuration for staging
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery configuration for staging
CELERY_BROKER_URL = env('REDIS_URL')
CELERY_RESULT_BACKEND = env('REDIS_URL')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_EAGER_PROPAGATES = True

# OCR Configuration for Staging
OCR_PROVIDER = env('OCR_PROVIDER', default='openai_vision')
OPENAI_API_KEY = env('OPENAI_API_KEY')

# Stripe Configuration for Staging (use test keys)
STRIPE_PUBLISHABLE_KEY = env('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET')

# AWS Configuration for Staging
AWS_SES_ACCESS_KEY_ID = env('AWS_SES_ACCESS_KEY_ID')
AWS_SES_SECRET_ACCESS_KEY = env('AWS_SES_SECRET_ACCESS_KEY')
AWS_SES_REGION = env('AWS_SES_REGION', default='eu-west-1')

# Cloudinary Configuration for Staging
CLOUDINARY_CLOUD_NAME = env('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = env('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = env('CLOUDINARY_API_SECRET')

# Sentry Configuration for Staging
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True,
    environment='staging',
)

# Logging for staging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'smart_accounts': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
} 