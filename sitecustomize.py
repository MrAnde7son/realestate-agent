"""Project-wide test and interactive environment bootstrap.
Ensures consistent import resolution for both PyCharm (Django/pytest runners)
and CLI (pytest/manage.py) executions without per-test path hacks.
"""
from __future__ import annotations
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # Root first

BACKEND = ROOT / "backend-django"
if BACKEND.exists() and str(BACKEND) not in sys.path:
    # Keep backend later so top-level packages (tests/, orchestration/, etc.) win
    sys.path.append(str(BACKEND))

# Default Django settings if not explicitly provided (pytest / PyCharm pytest runner)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")

