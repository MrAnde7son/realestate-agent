"""Shared ``tests.core`` namespace setup.

Both the repository root and the Django backend maintain ``core`` test suites.
The backend lives inside ``backend-django/tests`` which cannot be imported via a
standard dotted name because of the hyphen in the path.  Pytest imports modules
using their package name (``tests.core.<module>``), so without extra handling
the backend tests would be invisible when executing ``pytest`` from the project
root.

To bridge the two locations we extend the ``tests.core`` package path so Python
also searches ``backend-django/tests/core`` when resolving imports.  This keeps
all tests accessible without duplicating files or relying on symbolic links.
"""

from __future__ import annotations

import pkgutil
from pathlib import Path

# ``pkgutil.extend_path`` preserves the default behaviour while allowing us to
# add extra lookup directories.
__path__ = pkgutil.extend_path(__path__, __name__)  # type: ignore[var-annotated]

_backend_core_tests = Path(__file__).resolve().parents[2] / "backend-django" / "tests" / "core"
_backend_core_str = str(_backend_core_tests)
if _backend_core_tests.exists() and _backend_core_str not in __path__:
    __path__.append(_backend_core_str)

