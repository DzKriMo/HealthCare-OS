"""
Celery application for Healthcare OS.
"""
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "healthcare_os.settings.dev")

app = Celery("healthcare_os")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
