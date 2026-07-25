"""
WSGI config for healthcare_os project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "healthcare_os.settings.dev")
application = get_wsgi_application()
