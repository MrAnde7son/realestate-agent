from django.apps import AppConfig
import os


class CrmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm'
    verbose_name = 'CRM'
    path = os.path.dirname(os.path.abspath(__file__))