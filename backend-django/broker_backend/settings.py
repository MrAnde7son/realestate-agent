import logging
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, Mapping

import dj_database_url
from decouple import config


logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

# Add the root project directory to Python path so Django can find orchestration module
ROOT_PROJECT_DIR = BASE_DIR.parent
if str(ROOT_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_PROJECT_DIR))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,testserver').split(',')

# LLM configuration
LLM_DEFAULT_PROVIDER = os.getenv("LLM_DEFAULT_PROVIDER", "gemini")
LLM_ALLOW_OVERRIDE = os.getenv("LLM_ALLOW_OVERRIDE", "true").lower() == "true"

# Gemini / Google AI Studio
GOOGLE_API_KEY = config("GOOGLE_API_KEY", default="")
GOOGLE_MODEL = config("GOOGLE_MODEL", default="gemini-2.0-flash")
GEMINI_API_KEY = config("GEMINI_API_KEY", default="")
GEMINI_MODEL = config("GEMINI_MODEL", default="gemini-2.0-flash") 

# OpenAI
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")
OPENAI_MODEL = config("OPENAI_MODEL", default="gpt-4o-mini")

# Groq
GROQ_API_KEY = config("GROQ_API_KEY", default="")
GROQ_MODEL = config("GROQ_MODEL", default="llama-3.1-70b-versatile")

# Custom user model
AUTH_USER_MODEL = 'core.User'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'core',
    'crm',
    'imports',
    'deal_workspace'
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.APIPerformanceMiddleware',  # Track API response times
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'broker_backend.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ]
        }
    }
]

WSGI_APPLICATION = 'broker_backend.wsgi.application'
# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

# Use DATABASE_URL from environment (Render) or fallback to SQLite for development
if os.getenv('DATABASE_URL'):
    # Parse DATABASE_URL for production (Render)
    parsed_db = dj_database_url.parse(os.getenv('DATABASE_URL'))
    # If it's an SQLite URL with a relative path, anchor it to BASE_DIR to avoid accidentally
    # creating/using a different db.sqlite3 in the project root (which caused missing tables)
    if parsed_db.get('ENGINE', '').endswith('sqlite3'):
        name = parsed_db.get('NAME')
        if name and not os.path.isabs(name):
            parsed_db['NAME'] = str(BASE_DIR / name)
    DATABASES = {
        'default': parsed_db
    }
elif os.getenv('USE_POSTGRES', 'false').lower() == 'true':
    # Fallback to individual PostgreSQL environment variables
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('POSTGRES_DB', 'realestate'),
            'USER': os.getenv('POSTGRES_USER', 'postgres'),
            'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
            'HOST': os.getenv('POSTGRES_HOST', 'postgres'),
            'PORT': os.getenv('POSTGRES_PORT', '5432'),
        }
    }
else:
    # Default to SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


def _safe_str(value: Any) -> str:
    """Return a human-friendly string representation for logging."""

    if value is None:
        return "<unset>"
    return str(value)


def _describe_database(db_settings: Mapping[str, Any]) -> str:
    """Create a concise, password-free description of the configured database."""

    engine = db_settings.get('ENGINE', '') or ''
    engine_lower = engine.lower()

    if engine_lower.endswith('sqlite3'):
        name = _safe_str(db_settings.get('NAME'))
        return f"SQLite database at '{name}'"

    if 'postgres' in engine_lower:
        name = _safe_str(db_settings.get('NAME'))
        user = _safe_str(db_settings.get('USER'))
        host = _safe_str(db_settings.get('HOST'))
        port = _safe_str(db_settings.get('PORT'))
        return (
            "PostgreSQL database "
            f"'{name}' (user='{user}', host='{host}', port='{port}')"
        )

    return f"Database engine '{engine}'"


def log_database_configuration(db_settings: Mapping[str, Any]) -> None:
    """Log the active database connection in a safe and friendly format."""

    description = _describe_database(db_settings)
    logger.info("Using %s", description)


log_database_configuration(DATABASES['default'])

LANGUAGE_CODE = 'he'
TIME_ZONE = 'Asia/Jerusalem'
USE_I18N = True
USE_TZ = True

# Celery Configuration
# Only enable Celery when Redis is available
if os.getenv('USE_CELERY', 'false').lower() == 'true':
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://redis:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://redis:6379/0')
    CELERY_TIMEZONE = TIME_ZONE
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 50
    CELERY_WORKER_CONCURRENCY = int(os.getenv("CELERY_WORKER_CONCURRENCY", "2"))
    # Use threads pool instead of prefork on Apple Silicon to avoid SIGSEGV crashes
    CELERY_WORKER_POOL = 'threads'  # or 'solo' for single-threaded (safer for ARM)
    CELERY_IMPORTS = ('core.tasks', 'imports.tasks')
    from celery.schedules import crontab
    CELERY_BEAT_SCHEDULE = {
        'cleanup-demo-data': {
            'task': 'core.tasks.cleanup_demo_data',
            'schedule': crontab(hour=0, minute=0),
        },
        'alerts-daily-digest': {
            'task': 'core.tasks.alerts_daily_digest',
            'schedule': crontab(hour=8, minute=0),  # 8:00 AM Asia/Jerusalem
        },
        'rollup-analytics': {
            'task': 'core.tasks.rollup_analytics',
            'schedule': crontab(hour=1, minute=0),  # 1:00 AM daily
        },
    }
else:
    # Disable Celery for development
    CELERY_BROKER_URL = None
    CELERY_RESULT_BACKEND = None
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "core" / "static",
]

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Document storage settings
DOCUMENT_STORAGE_PATH = 'documents'
MAX_DOCUMENT_SIZE = 10 * 1024 * 1024  # 10MB

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOW_ALL_ORIGINS = DEBUG

CORS_ALLOWED_ORIGINS = [
   'https://app.nadlaner.com', 'https://nadlaner.com', 'https://api.nadlaner.com'
]

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/realestate-agent.*\.vercel\.app$",
    r"^https:\/\/.*\.?nadlaner\.com$"
]

CSRF_TRUSTED_ORIGINS = [
    'https://app.nadlaner.com',
    'https://nadlaner.com',
    'https://api.nadlaner.com',
    "https://realestate-agent*.vercel.app",
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'core.authentication.APITokenAuthentication',  # API token authentication (check first)
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_ROUTER_TRAILING_SLASH': ''
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Real Estate API',
    'DESCRIPTION': 'API schema for assets, permits and plans',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'COMPONENT_NO_READ_ONLY_REQUIRED': True,
    'ENUM_NAME_OVERRIDES': {
        'UserRoleEnum': 'core.models.User.Role',
        'PlanTypeEnum': 'core.models.PlanType.PLAN_CHOICES',
    },
    'SCHEMA_PATH_PREFIX': '/api/',
    'SERVERS': [
        {'url': 'http://localhost:8000', 'description': 'Development server'},
        {'url': 'https://api.nadlaner.com', 'description': 'Production server'},
    ],
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication and authorization'},
        {'name': 'Assets', 'description': 'Real estate asset management'},
        {'name': 'Permits', 'description': 'Building permits and approvals'},
        {'name': 'Plans', 'description': 'Urban planning and development plans'},
        {'name': 'Alerts', 'description': 'Alert rules and notifications'},
        {'name': 'Analytics', 'description': 'Usage analytics and reporting'},
        {'name': 'Support', 'description': 'Support and consultation services'},
        {'name': 'User Management', 'description': 'User profiles and settings'},
    ],
}

# JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=24),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# Google OAuth Settings
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='your-google-client-id.apps.googleusercontent.com')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='your-google-client-secret')
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

# Google OAuth URLs
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USER_INFO_URL = 'https://www.googleapis.com/oauth2/v2/userinfo'

# from celery.schedules import crontab
# CELERY_BEAT_SCHEDULE = {
#     'evaluate-alerts-hourly': {
#         'task': 'core.tasks.evaluate_alerts',
#         'schedule': 3600.0,  # every hour
#     },
# }

# URL Settings
APPEND_SLASH = False

USE_X_FORWARDED_HOST = True

# Email Configuration
EMAIL_BACKEND = 'core.email_backends.resend_backend.ResendEmailBackend'
DEFAULT_FROM_EMAIL = config('RESEND_FROM', default='no-reply@nadlaner.com')
SERVER_EMAIL = DEFAULT_FROM_EMAIL
RESEND_API_KEY = config('RESEND_API_KEY', default='')
RESEND_SANDBOX = config('RESEND_SANDBOX', default=False, cast=bool)
EMAIL_FALLBACK_TO_CONSOLE = config('EMAIL_FALLBACK_TO_CONSOLE', default=False, cast=bool)

# WhatsApp Configuration (Twilio)
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_WHATSAPP_FROM = config('TWILIO_WHATSAPP_FROM', default='whatsapp:+14155238886')
SUPPORT_SLACK_WEBHOOK = os.getenv("SUPPORT_SLACK_WEBHOOK", "")
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
