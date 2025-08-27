"""Global test configuration for the realestate-agent project.

This conftest.py file is automatically loaded by pytest and ensures that
all test files can import modules from the project root without needing
to manually modify sys.path in each test file.
"""

import os
import sys
import pytest

# Add project root to Python path for all tests
project_root = os.path.abspath(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add backend-django to path for Django tests
backend_path = os.path.join(project_root, 'backend-django')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Add package paths for non-Django tests
mavat_path = os.path.join(project_root, "mavat")
if mavat_path not in sys.path:
    sys.path.insert(0, mavat_path)

orchestration_path = os.path.join(project_root, "orchestration")
if orchestration_path not in sys.path:
    sys.path.insert(0, orchestration_path)

# Only setup Django if we're running Django tests
def pytest_configure(config):
    """Configure Django only when needed."""
    # Check if we're running Django tests
    if any('backend-django' in str(item) for item in config.getini('testpaths')):
        try:
            import django
            from django.core.management import call_command
            
            # Configure Django for testing
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')
            django.setup()
            call_command("migrate", run_syncdb=True, verbosity=0)
            
            # Configure Django settings for testing
            from django.conf import settings
            settings.ALLOWED_HOSTS = ['testserver', 'localhost', '127.0.0.1']
            settings.DEBUG = True
        except ImportError:
            # Django not available, skip Django setup
            pass

# Common fixtures for all tests
@pytest.fixture
def mock_requests_session():
    """Create a mock requests session for testing."""
    from unittest.mock import Mock
    session = Mock()
    session.headers = {}
    session.headers.update = Mock()
    return session


@pytest.fixture
def sample_lookup_response():
    """Sample lookup table response from the API."""
    return [
        {
            "type": "4",
            "result": [
                {"CODE": "5", "DESCRIPTION": "Tel Aviv"},
                {"CODE": "6", "DESCRIPTION": "Haifa"}
            ]
        },
        {
            "type": "5",
            "result": [
                {"CODE": "5000", "DESCRIPTION": "Tel Aviv-Yafo"},
                {"CODE": "6000", "DESCRIPTION": "Haifa"}
            ]
        },
        {
            "type": "7",
            "result": [
                {"CODE": "461", "DESCRIPTION": "Hayarkon"},
                {"CODE": "462", "DESCRIPTION": "Dizengoff"}
            ]
        }
    ]


@pytest.fixture
def sample_search_response():
    """Sample search response from the API."""
    return [
        {
            "type": "1",
            "result": {
                "dtResults": [
                    {
                        "PLAN_ID": "12345",
                        "ENTITY_NAME": "Sample Plan",
                        "INTERNET_SHORT_STATUS": "Approved",
                        "AUTH_NAME": "Sample Authority",
                        "ENTITY_LOCATION": "Sample Location",
                        "ENTITY_NUMBER": "Yosh/ 51/ 51",
                        "APP_DATE": "08/01/1992",
                        "INTERNET_STATUS_DATE": "08/01/1992"
                    }
                ]
            }
        }
    ]
