"""Test utilities for the realestate-agent project.

This module provides utilities for test files and ensures proper imports.
Import this at the top of any test file to set up the Python path correctly.
"""

import sys
from pathlib import Path

def setup_project_path():
    """Add project root to Python path if not already present."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# Automatically set up path when this module is imported
setup_project_path()
