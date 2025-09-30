"""Placeholder module to satisfy pytest discovery for backend document tests."""

import pytest

pytest.skip("backend document tests are executed via the backend-django test suite", allow_module_level=True)
