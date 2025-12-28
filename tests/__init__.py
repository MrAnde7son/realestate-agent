"""Test package initialization.

This ensures the project root is in the Python path for all test modules.
"""

# Use the centralized path setup utility
from tests.utils.test_utils import setup_project_path  # noqa: F401
