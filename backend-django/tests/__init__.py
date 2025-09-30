"""Test package placeholder used by Django-specific test runner."""

import pytest

pytest.skip(
    "backend-django/tests are executed via the Django app's test runner",
    allow_module_level=True,
)
