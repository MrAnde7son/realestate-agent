"""Test package bootstrap utilities.

This module guarantees that all test suites can be discovered regardless of
whether they live in the top-level ``tests/`` directory or inside the Django
backend (``backend-django/tests``).  The PyPI ``pytest`` runner imports modules
using their dotted path, so directories with hyphens would normally break
module resolution (``backend-django`` is not a valid Python package name).

By explicitly adjusting ``sys.path`` and extending ``tests.__path__`` we make
the backend test suite available under the shared ``tests`` namespace without
requiring symbolic links or duplicate files.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import pkgutil


def _ensure_project_root() -> Path:
    """Return the absolute project root and ensure it is on ``sys.path``."""

    project_root = Path(__file__).resolve().parent.parent
    root_str = str(project_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return project_root


PROJECT_ROOT = _ensure_project_root()

# Allow ``import tests.*`` to resolve modules from both the repository test
# suite and the Django backend's dedicated ``backend-django/tests`` directory.
__path__ = pkgutil.extend_path(__path__, __name__)  # type: ignore[var-annotated]

backend_tests_dir = PROJECT_ROOT / "backend-django" / "tests"
backend_tests_str = str(backend_tests_dir)
if backend_tests_dir.exists() and backend_tests_str not in __path__:
    __path__.append(backend_tests_str)
