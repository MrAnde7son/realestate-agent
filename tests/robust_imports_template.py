"""
Robust Imports Template for Test Files

Copy this code block to the top of any test file to ensure imports work
in all environments: terminal, debugger, pytest, etc.

Usage:
    1. Copy the setup_python_path() function and call
    2. Place at the top of your test file before any project imports
    3. Remove the old "import tests.test_utils" line
"""

import sys
import os
from pathlib import Path

# Robust path setup that works in all environments (terminal, debugger, pytest)
def setup_python_path():
    """Ensure the project root is in Python path."""
    # First try to import test_utils (preferred method)
    try:
        import tests.test_utils  # This sets up the Python path
        return
    except (ImportError, ModuleNotFoundError):
        pass
    
    # Fallback: manually find and add project root
    current_file = Path(__file__).resolve()
    
    # Look for project root by checking for marker files
    current_dir = current_file.parent
    max_levels = 5
    
    for _ in range(max_levels):
        # Look for specific marker files that indicate the PROJECT ROOT (not subdirs)
        # Must have BOTH a config file AND the rami package directory
        has_config = any((current_dir / marker).exists() for marker in ['pyproject.toml', 'requirements.txt', 'setup.py'])
        has_rami = (current_dir / 'rami').exists() and (current_dir / 'rami').is_dir()
        
        if has_config and has_rami:
            project_root = str(current_dir)
            if project_root not in sys.path:
                sys.path.insert(0, project_root)
                print(f"✅ Added project root to path: {project_root}")
            return
        
        parent = current_dir.parent
        if parent == current_dir:  # Reached filesystem root
            break
        current_dir = parent
    
    # Last resort: relative path from current file
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        print(f"✅ Added project root to path (fallback): {project_root}")

# Set up the path
setup_python_path()

# Now you can safely import project modules:
# from rami.rami_client import RamiClient
# from gis.gis_client import TelAvivGS
# etc.
