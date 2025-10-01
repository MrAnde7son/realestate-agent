#!/usr/bin/env python3
"""Determine which CI test suites should run based on modified paths."""
from __future__ import annotations

import os
from typing import Iterable


def _collect_changed_files() -> list[str]:
    env_value = os.environ.get("CHANGED_FILES", "")
    return [line.strip() for line in env_value.splitlines() if line.strip()]


def _write_outputs(outputs: Iterable[tuple[str, bool]]) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        raise RuntimeError("GITHUB_OUTPUT is not defined")

    with open(output_path, "a", encoding="utf-8") as handle:
        for key, value in outputs:
            handle.write(f"{key}={'true' if value else 'false'}\n")


def main() -> None:
    files = _collect_changed_files()

    backend = False
    crm = False
    data_pipeline = False
    broker_ui = False
    shared = False

    backend_dirs = {"backend-django", "utils", "db", "scripts"}
    crm_dirs = {"crm"}
    data_pipeline_dirs = {
        "orchestration",
        "yad2",
        "mavat",
        "gov",
        "gis",
        "govmap",
        "rami",
    }

    backend_test_dirs = {"core", "db", "utils", "e2e"}
    crm_test_dirs = {"crm"}
    data_pipeline_test_dirs = {
        "data",
        "gis",
        "gov",
        "govmap",
        "mavat",
        "yad2",
        "orchestration",
        "rami",
    }

    shared_files = {
        "pyproject.toml",
        "pytest.ini",
        "pytest-ci.ini",
        "requirements.txt",
        "setup.py",
        "setup_assets.py",
    }

    for path in files:
        parts = path.split("/") if path else []
        top = parts[0] if parts else ""

        if path in shared_files or path.startswith("tests/conftest.py") or path.startswith("tests/__init__"):
            shared = True
            continue

        if top == "realestate-broker-ui":
            broker_ui = True
            continue

        if top == "backend-django":
            if len(parts) > 1 and parts[1] == "crm":
                crm = True
            else:
                backend = True
            continue

        if top == "tests":
            if len(parts) == 1:
                shared = True
                continue
            second = parts[1]
            if second in backend_test_dirs:
                backend = True
            elif second in crm_test_dirs:
                crm = True
            elif second in data_pipeline_test_dirs:
                data_pipeline = True
            else:
                shared = True
            continue

        if top in crm_dirs:
            crm = True
            continue

        if top in data_pipeline_dirs:
            data_pipeline = True
            continue

        if top in backend_dirs or path.endswith(".py"):
            backend = True

    if shared:
        backend = crm = data_pipeline = True

    python_required = backend or crm or data_pipeline

    _write_outputs(
        (
            ("python", python_required),
            ("backend", backend),
            ("crm", crm),
            ("data_pipeline", data_pipeline),
            ("broker_ui", broker_ui),
        )
    )


if __name__ == "__main__":
    main()
