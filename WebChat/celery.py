import os
from celery import Celery

# Set default Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "WebChat.settings")

app = Celery("WebChat")

# Load settings from Django config with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks from installed apps
app.autodiscover_tasks()

# celery -A WebChat worker --loglevel=INFO -P solo