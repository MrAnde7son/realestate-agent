"""Test utilities for the realestate-agent project.

This module provides utilities for test files and ensures proper imports.
Import this at the top of any test file to set up the Python path correctly.

Usage:
    # Preferred: Import the module (sets up path automatically)
    import tests.utils.test_utils

    # Or call the function directly
    from tests.utils.test_utils import setup_project_path
    setup_project_path()
"""

import sys
from pathlib import Path


def setup_project_path(start_file=None):
    """
    Add project root to Python path if not already present.

    This function works in all environments:
    - Terminal execution: python tests/.../test_file.py
    - VS Code debugger: F5 debugging with breakpoints
    - Pytest: pytest tests/
    - CI/CD: Automated testing pipelines

    Args:
        start_file: Optional file path to start searching from.
                    If None, uses the location of this module.
    """
    # Determine starting point for search
    if start_file:
        current_file = Path(start_file).resolve()
        current_dir = current_file.parent
    else:
        # Get the directory of this file (tests/utils/)
        current_dir = Path(__file__).resolve().parent.parent

    # Try to find project root by looking for specific marker files
    max_levels = 5  # Prevent infinite loops

    for _ in range(max_levels):
        # Look for specific marker files that indicate the PROJECT ROOT (not subdirs)
        # Must have BOTH a config file AND a key package directory
        has_config = any(
            (current_dir / marker).exists()
            for marker in ["pyproject.toml", "requirements.txt", "setup.py"]
        )
        # Check for multiple indicators (not just rami)
        has_packages = any(
            (current_dir / pkg).exists() and (current_dir / pkg).is_dir()
            for pkg in ["rami", "gov", "yad2", "gis", "orchestration"]
        )

        if has_config and has_packages:
            project_root = current_dir
            break

        parent = current_dir.parent
        if parent == current_dir:  # Reached filesystem root
            break
        current_dir = parent
    else:
        # Fallback: relative path from tests/utils/ (go up 2 levels)
        project_root = Path(__file__).resolve().parent.parent.parent

    # Convert to absolute path string
    project_root_str = str(project_root.resolve())

    # Add to sys.path if not already there
    if project_root_str not in sys.path:
        sys.path.insert(0, project_root_str)
        print(f"✅ Added project root to Python path: {project_root_str}")

    # Also add the current working directory if it looks like project root
    cwd = Path.cwd().resolve()
    cwd_has_config = any(
        (cwd / marker).exists()
        for marker in ["pyproject.toml", "requirements.txt", "setup.py"]
    )
    cwd_has_packages = any(
        (cwd / pkg).exists() and (cwd / pkg).is_dir()
        for pkg in ["rami", "gov", "yad2", "gis", "orchestration"]
    )

    if cwd_has_config and cwd_has_packages:
        cwd_str = str(cwd)
        if cwd_str not in sys.path:
            sys.path.insert(0, cwd_str)
            print(f"✅ Added current working directory to Python path: {cwd_str}")


# Alias for backward compatibility
setup_python_path = setup_project_path


# Automatically set up path when this module is imported
setup_project_path()
