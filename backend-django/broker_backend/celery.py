
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')

app = Celery('broker_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
