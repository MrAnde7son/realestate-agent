import os
from pathlib import Path

# Load .env file before Django/Celery initialization
# Note: override=False ensures shell environment variables take precedence
try:
    from dotenv import load_dotenv

    # Look for .env file in multiple locations:
    # 1. Project root directory (where .env is typically located)
    # 2. backend-django directory (fallback)
    backend_django_dir = Path(__file__).resolve().parent.parent
    project_root = backend_django_dir.parent

    # Try project root first (most common location)
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file, override=False, verbose=False)
    else:
        # Fallback to backend-django directory
        env_file = backend_django_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=False, verbose=False)
except ImportError:
    # python-dotenv not available, skip
    pass

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")

app = Celery("broker_backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
