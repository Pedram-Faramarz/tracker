"""
Settings for PythonAnywhere deployment.
"""
from .settings import *

DEBUG = False

# Replace YOURNAME with your PythonAnywhere username
ALLOWED_HOSTS = ['YOURNAME.pythonanywhere.com']

# Static files served by PythonAnywhere
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Disable whitenoise root (PythonAnywhere serves static directly)
WHITENOISE_ROOT = None

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
