
import os
from pathlib import Path

# Load .env file before Django/Celery initialization
try:
    from dotenv import load_dotenv
    # Look for .env file in backend-django directory
    backend_django_dir = Path(__file__).resolve().parent.parent
    env_file = backend_django_dir / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    # python-dotenv not available, skip
    pass

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')

app = Celery('broker_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
