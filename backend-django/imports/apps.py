from django.apps import AppConfig


class ImportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'imports'
    verbose_name = 'Imports'

    def ready(self):
        # Import Celery tasks so the worker registers them even without autodiscover.
        import imports.tasks  # noqa: F401
