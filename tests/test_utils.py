"""Test utilities for the realestate-agent project.

This module provides utilities for test files and ensures proper imports.
Import this at the top of any test file to set up the Python path correctly.
"""

import sys
from pathlib import Path


def setup_project_path():
    """Add project root to Python path if not already present."""
    # Get the directory of this file (tests/)
    tests_dir = Path(__file__).parent.resolve()
    
    # Project root is one level up from tests/
    project_root = tests_dir.parent
    
    # Also try to find project root by looking for specific marker files
    current_dir = Path(__file__).resolve().parent
    max_levels = 5  # Prevent infinite loops
    
    for _ in range(max_levels):
        # Look for specific marker files that indicate the PROJECT ROOT (not subdirs)
        # Must have BOTH a config file AND the rami package directory
        has_config = any((current_dir / marker).exists() for marker in ['pyproject.toml', 'requirements.txt', 'setup.py'])
        has_rami = (current_dir / 'rami').exists() and (current_dir / 'rami').is_dir()
        
        if has_config and has_rami:
            project_root = current_dir
            break
        
        parent = current_dir.parent
        if parent == current_dir:  # Reached filesystem root
            break
        current_dir = parent
    
    # Convert to absolute path string
    project_root_str = str(project_root.resolve())
    
    # Add to sys.path if not already there
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
        print(f"✅ Added project root to Python path: {project_root_str}")
    
    # Also add the current working directory if it looks like project root
    cwd = Path.cwd().resolve()
    cwd_has_config = any((cwd / marker).exists() for marker in ['pyproject.toml', 'requirements.txt', 'setup.py'])
    cwd_has_rami = (cwd / 'rami').exists() and (cwd / 'rami').is_dir()
    
    if cwd_has_config and cwd_has_rami:
        cwd_str = str(cwd)
        if cwd_str not in sys.path:
            sys.path.insert(0, cwd_str)
            print(f"✅ Added current working directory to Python path: {cwd_str}")

# Automatically set up path when this module is imported
setup_project_path()
