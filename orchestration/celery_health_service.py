"""Celery worker supervisor with a lightweight FastAPI health endpoint.

This module is intended for deployment on Render's free tier where only
web services are available. It starts the Celery worker in a managed
subprocess and exposes a health-check HTTP endpoint so Render can
monitor the worker.
"""
from __future__ import annotations

import logging
import os
import signal
import subprocess
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

LOGGER = logging.getLogger("orchestration.celery_worker")
_logging_configured = False
_DJANGO_DIR: Optional[Path] = None


def _configure_logging() -> None:
    global _logging_configured
    if _logging_configured:
        return
    log_level = os.environ.get("CELERY_HEALTH_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=log_level)
    LOGGER.debug("Configured logging at level %s", log_level)
    _logging_configured = True


_worker_process: Optional[subprocess.Popen[bytes]] = None
_worker_lock = threading.Lock()

app = FastAPI(title="Celery Worker Health", version="1.0.0")


def _iter_candidate_roots() -> list[Path]:
    """Return directories that may contain the Django project."""

    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd().resolve()
    roots: list[Path] = []
    seen: set[Path] = set()

    for base in (script_dir, cwd):
        for candidate in (base, *base.parents):
            candidate = candidate.resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            roots.append(candidate)

    return roots


def _candidate_django_dirs() -> list[Path]:
    """Generate potential Django project directories from search roots."""

    candidates: list[Path] = []
    seen: set[Path] = set()

    for root in _iter_candidate_roots():
        for candidate in (root, root / "backend-django"):
            candidate = candidate.resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            candidates.append(candidate)

    return candidates


def _resolve_django_dir() -> Path:
    """Locate the Django project directory for the Celery worker."""

    global _DJANGO_DIR

    if _DJANGO_DIR is not None:
        return _DJANGO_DIR

    env_dir = os.environ.get("DJANGO_DIR")
    if env_dir:
        candidate = Path(env_dir).expanduser().resolve()
        if not (candidate / "manage.py").is_file():
            raise RuntimeError(
                f"DJANGO_DIR={candidate} does not contain manage.py"
            )
        LOGGER.debug("Using Django directory from DJANGO_DIR=%s", candidate)
        _DJANGO_DIR = candidate
        return _DJANGO_DIR

    for candidate in _candidate_django_dirs():
        if (candidate / "manage.py").is_file():
            LOGGER.debug("Auto-discovered Django directory at %s", candidate)
            _DJANGO_DIR = candidate
            return _DJANGO_DIR

    raise RuntimeError(
        "Unable to locate Django project directory; set DJANGO_DIR to override"
    )


def _spawn_worker() -> subprocess.Popen[bytes]:
    django_dir = _resolve_django_dir()
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    celery_app = env.get("CELERY_APP", "broker_backend")
    concurrency = env.get("CELERY_WORKER_CONCURRENCY", "2")
    log_level = env.get("CELERY_LOG_LEVEL", "info")

    cmd = [
        "celery",
        "--workdir",
        str(django_dir),
        "-A",
        celery_app,
        "worker",
        "-l",
        log_level,
        "-c",
        str(concurrency),
    ]

    LOGGER.info("Starting Celery worker: %s", " ".join(cmd))
    return subprocess.Popen(cmd, env=env, cwd=str(django_dir))


def ensure_worker_running() -> subprocess.Popen[bytes]:
    """Start the Celery worker if it is not already running."""
    global _worker_process

    with _worker_lock:
        if _worker_process is None or _worker_process.poll() is not None:
            _worker_process = _spawn_worker()
        return _worker_process


def _shutdown_worker(timeout: float = 15.0) -> None:
    global _worker_process

    with _worker_lock:
        process = _worker_process
        _worker_process = None

    if process is None:
        return

    if process.poll() is not None:
        LOGGER.info(
            "Celery worker already stopped (return code %s)", process.poll()
        )
        return

    LOGGER.info("Stopping Celery worker with SIGTERM")
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=timeout)
        LOGGER.info("Celery worker exited with code %s", process.returncode)
    except subprocess.TimeoutExpired:
        LOGGER.warning("Celery worker did not stop in %.1fs; killing", timeout)
        process.kill()


def _current_worker_status() -> dict[str, object]:
    process = ensure_worker_running()
    running = process.poll() is None
    return {
        "status": "ok" if running else "error",
        "worker_running": running,
        "returncode": process.returncode,
        "pid": process.pid,
    }


@app.on_event("startup")
async def _on_startup() -> None:  # pragma: no cover
    _configure_logging()
    ensure_worker_running()


@app.on_event("shutdown")
async def _on_shutdown() -> None:  # pragma: no cover
    _shutdown_worker(
        timeout=float(os.environ.get("CELERY_WORKER_SHUTDOWN_TIMEOUT", "15"))
    )


@app.get("/", tags=["health"])
@app.get("/healthz", tags=["health"])
async def healthcheck() -> JSONResponse:
    """Return worker status for Render health checks."""
    status_payload = _current_worker_status()
    http_status = (
        status.HTTP_200_OK
        if status_payload["worker_running"]
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return JSONResponse(status_code=http_status, content=status_payload)


def run() -> None:
    """Run the uvicorn server when executed as a script."""
    _configure_logging()
    port = int(os.environ.get("PORT", "10000"))
    LOGGER.info("Starting health server on port %s", port)
    import uvicorn

    uvicorn.run(
        "orchestration.celery_health_service:app",
        host="0.0.0.0",
        port=port,
        log_level=os.environ.get("UVICORN_LOG_LEVEL", "info"),
    )


if __name__ == "__main__":
    run()
