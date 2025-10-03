"""Top-level test package initialisation helpers.

This module originally just added the project root to :mod:`sys.path` so that
tests could import application modules.  Once we split the backend Django tests
into the ``backend-django/tests`` directory, Pytest began deriving their module
names as ``tests.<submodule>`` (because the directory contains an
``__init__``).  Unfortunately we already have a top-level :mod:`tests` package,
so Python tried to import :mod:`tests.core` from this package and failed.

To allow both test suites to co-exist we extend the package search path for the
``tests`` package to also include the backend Django test directory.  This way
imports such as ``tests.core.test_alert_analytics`` will resolve to the files in
``backend-django/tests`` instead of raising ``ModuleNotFoundError`` during test
collection.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Ensure ``tests`` behaves like a namespace package that also searches the
# backend Django tests directory.  Pytest imports those modules using the
# ``tests.<submodule>`` prefix, so adding this location prevents import errors.
backend_tests_dir = project_root / "backend-django" / "tests"
if backend_tests_dir.exists():
    # ``__path__`` is provided by Python for packages; we mutate it in-place to
    # keep ``pkgutil.iter_modules`` and friends working as expected.
    __path__.append(str(backend_tests_dir))
