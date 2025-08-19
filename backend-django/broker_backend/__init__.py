"""Initialize the Celery application.

This project relies on Celery for background tasks, but many test runs and
environments don't actually require Celery to be installed. Importing the
``celery`` package unconditionally would therefore raise a
``ModuleNotFoundError`` during module import and prevent the rest of the
application from loading.

To make the package more robust we attempt to import the Celery application but
gracefully fall back to ``None`` if Celery isn't available. This mirrors
Django's recommended pattern for optional dependencies and keeps runtime
behaviour intact for environments where Celery is installed.
"""

try:  # pragma: no cover - exercised indirectly
    from .celery import app as celery_app
except Exception:  # Celery or its dependencies might be missing
    celery_app = None
__all__ = ('celery_app',)
