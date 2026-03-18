"""
WSGI config for PythonAnywhere.
"""
import os
import sys

# Add your project to path — replace YOURNAME
path = '/home/YOURNAME/unitracker/backend'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings_pythonanywhere'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
