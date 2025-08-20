"""Global test configuration for the realestate-agent project.

This conftest.py file is automatically loaded by pytest and ensures that
all test files can import modules from the project root without needing
to manually modify sys.path in each test file.
"""

import os
import sys
import pytest

# Add project root to Python path
sys.path.insert(0, os.path.abspath('backend-django'))

# Configure Django for testing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')

# Import and setup Django
import django
django.setup()

# Configure Django settings for testing
from django.conf import settings
settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
settings.DEBUG = True
