"""
Django settings for Smart Accounts Management System.
"""

import os

# Set the Django settings module based on environment
DJANGO_ENV = os.environ.get('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    from .production import *
elif DJANGO_ENV == 'staging':
    from .staging import *
else:
    from .development import *
