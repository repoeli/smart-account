"""
Base Django settings for Smart Accounts Management System.
Following Clean Architecture principles with DDD patterns.
"""

import os
from pathlib import Path
from datetime import timedelta

import environ

# Initialize environment variables
env = environ.Env()
# Explicitly load backend/.env so local configuration is always picked up
try:
    environ.Env.read_env(str(Path(__file__).resolve().parent.parent.parent / '.env'))
except Exception:
    # Fallback to default lookup
    environ.Env.read_env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')

# Application definition
# Summary cache TTL (seconds) for transactions summary endpoint
SUMMARY_CACHE_TTL = int(os.environ.get('SUMMARY_CACHE_TTL', '60'))
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'django_extensions',
]

LOCAL_APPS = [
    # Domain Layer - Core business logic
    'domain.accounts',
    'domain.receipts',
    'domain.transactions',
    'domain.subscriptions',
    
    # Application Layer - Use cases and application services
    'application.accounts',
    'application.receipts',
    'application.transactions',
    'application.subscriptions',
    
    # Infrastructure Layer - External services and data persistence
    'infrastructure.database',
    'infrastructure.storage',
    'infrastructure.email',
    'infrastructure.payment',
    'infrastructure.ocr',
    
    # Interface Layer - REST APIs and web interfaces
    'interfaces.api',
    'interfaces.web',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'smart_accounts.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'smart_accounts.wsgi.application'

# Database
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgresql://smart_accounts:password@localhost:5432/smart_accounts_dev')
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-gb'
TIME_ZONE = 'Europe/London'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'infrastructure_database.User'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=env.int('JWT_REFRESH_TOKEN_LIFETIME', default=1440)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('JWT_SECRET_KEY', default=SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:3000',
    'http://127.0.0.1:3000',
])

CORS_ALLOW_CREDENTIALS = True

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Smart Accounts Management API',
    'DESCRIPTION': 'A comprehensive financial management API for self-employed individuals and accounting companies',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1/',
}

# OCR/Storage configuration (env-driven)
# Support both our canonical names and the user's provided names for compatibility
OCR_ENGINE_DEFAULT = env("OCR_ENGINE_DEFAULT", default=env("OCR_PROVIDER_DEFAULT", default="paddle"))
OCR_TIMEOUT_SECONDS = env.int("OCR_TIMEOUT_SECONDS", default=env.int("PADDLE_TIMEOUT_SECONDS", default=25))
MAX_RECEIPT_MB = env.int("MAX_RECEIPT_MB", default=env.int("OCR_MAX_IMAGE_MB", default=10))

# External Paddle FastAPI service
_paddle_base = env("PADDLE_API_BASE", default="http://127.0.0.1:8089")
PADDLE_OCR_URL = env("PADDLE_OCR_URL", default=f"{_paddle_base}/ocr/receipt")
PADDLE_OCR_URL_BY_URL = env("PADDLE_OCR_URL_BY_URL", default=f"{_paddle_base}/ocr/receipt-by-url")

# OpenAI
OPENAI_API_KEY = env("OPENAI_API_KEY", default=None)
OPENAI_VISION_MODEL = env("OPENAI_VISION_MODEL", default="gpt-4o-mini")
FALLBACK_TO_PADDLE = env.bool("FALLBACK_TO_PADDLE", default=True)

# Cloudinary (support both RECEIPTS_FOLDER and legacy UPLOAD_FOLDER env names)
CLOUDINARY_CLOUD_NAME = env("CLOUDINARY_CLOUD_NAME", default=None)
CLOUDINARY_API_KEY = env("CLOUDINARY_API_KEY", default=None)
CLOUDINARY_API_SECRET = env("CLOUDINARY_API_SECRET", default=None)
CLOUDINARY_RECEIPTS_FOLDER = env(
    "CLOUDINARY_RECEIPTS_FOLDER",
    default=env("CLOUDINARY_UPLOAD_FOLDER", default="receipts"),
)

# Public base URL used to build absolute URLs for locally stored media
PUBLIC_BASE_URL = env("PUBLIC_BASE_URL", default="http://127.0.0.1:8000")
# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
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
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True) 