"""Global test configuration for the realestate-agent project.

This conftest.py file is automatically loaded by pytest and ensures that
all test files can import modules from the project root without needing
to manually modify sys.path in each test file.
"""

import os
import sys

import pytest


# Store the original system paths
original_sys_path = list(sys.path)

# Clear and rebuild the Python path to ensure correct order
sys.path[:] = []

# Add backend-django to path for Django tests (using symbolic link) - MUST BE FIRST
# to avoid conflicts with other 'core' modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
backend_path = os.path.abspath(os.path.join(project_root, 'backend-django'))
sys.path.append(backend_path)

# Add back the original system paths FIRST to ensure system packages are found
sys.path.extend(original_sys_path)

# Add project root AFTER system paths to avoid conflicts with system packages
sys.path.append(project_root)

# Add package paths for non-Django tests (after system paths to avoid conflicts)
mavat_path = os.path.abspath(os.path.join(project_root, "mavat"))
sys.path.append(mavat_path)

orchestration_path = os.path.abspath(os.path.join(project_root, "orchestration"))
sys.path.append(orchestration_path)

yad2_path = os.path.abspath(os.path.join(project_root, "yad2"))
sys.path.append(yad2_path)

gov_path = os.path.abspath(os.path.join(project_root, "gov"))
sys.path.append(gov_path)

db_path = os.path.abspath(os.path.join(project_root, "db"))
sys.path.append(db_path)

# Add utils directory
utils_path = os.path.abspath(os.path.join(project_root, "utils"))
sys.path.append(utils_path)

# Debug: Print the paths being added
print("=== CONFTEST.PY DEBUG ===")
print("Project root:", project_root)
print("Backend path:", backend_path)
print("Backend exists:", os.path.exists(backend_path))
print("Python path after setup:")
for i, path in enumerate(sys.path[:10]):  # Show first 10 paths
    print("  {}: {}".format(i, path))
print("=========================")

# Set up Django only when needed
def pytest_configure(config):
    """Configure pytest with custom markers and Django."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "mavat: marks tests for Mavat collector"
    )
    config.addinivalue_line(
        "markers", "yad2: marks tests for Yad2 scraper"
    )
    config.addinivalue_line(
        "markers", "nadlan: marks tests for Nadlan scraper"
    )
    config.addinivalue_line(
        "markers", "decisive: marks tests for Decisive appraisal"
    )
    config.addinivalue_line(
        "markers", "gis: marks tests for GIS client"
    )
    config.addinivalue_line(
        "markers", "rami: marks tests for RAMI client"
    )
    config.addinivalue_line(
        "markers", "govmap: marks tests for GovMap client and collector"
    )
    
    # Set up Django
    try:
        import django
        from django.core.management import call_command

        # Set environment variables for Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')
        os.environ.setdefault('SECRET_KEY', 'test-secret-key-for-testing')
        os.environ.setdefault('DEBUG', 'True')
        
        # Set DYLD_LIBRARY_PATH for WeasyPrint on Apple Silicon
        if os.name == 'posix' and os.uname().machine == 'arm64':
            os.environ['DYLD_LIBRARY_PATH'] = '/opt/homebrew/lib'
        
        # Configure Django for testing
        django.setup()
        
        # Run migrations for test database
        try:
            call_command("migrate", run_syncdb=True, verbosity=0)
        except Exception:
            # If migrations fail, continue - this might be expected in test environment
            pass
            
        print("Django setup completed successfully")
            
    except ImportError as e:
        # Django not available, skip Django setup
        print("Django not available: {}".format(e))
    except Exception as e:
        print("Django setup failed: {}".format(e))

# Common fixtures for all tests
@pytest.fixture
def mock_requests_session():
    """Create a mock requests session for testing."""
    from unittest.mock import Mock
    session = Mock()
    session.headers = Mock()
    session.headers.update = Mock()
    return session


@pytest.fixture
def sample_lookup_response():
    """Sample lookup table response from the API."""
    return [
        {
            "type": "District",
            "result": [
                {"CODE": "5", "DESCRIPTION": "Tel Aviv"},
                {"CODE": "6", "DESCRIPTION": "Haifa"}
            ]
        },
        {
            "type": "CityCounty",
            "result": [
                {"CODE": "5000", "DESCRIPTION": "Tel Aviv-Yafo"},
                {"CODE": "6000", "DESCRIPTION": "Haifa"}
            ]
        },
        {
            "type": "Street",
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
