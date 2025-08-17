"""Global test configuration for the realestate-agent project.

This conftest.py file is automatically loaded by pytest and ensures that
all test files can import modules from the project root without needing
to manually modify sys.path in each test file.
"""

import sys
from pathlib import Path

# Add project root to Python path so all tests can import project modules
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
