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
import time
from contextlib import asynccontextmanager
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


_worker_process: Optional[subprocess.Popen[str]] = None
_worker_lock = threading.Lock()
_worker_startup_error: Optional[str] = None
_worker_start_time: Optional[float] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    _configure_logging()
    LOGGER.info("Application startup: ensuring Celery worker is running")
    try:
        ensure_worker_running()
        LOGGER.info("Celery worker startup initiated")
    except Exception as exc:
        global _worker_startup_error
        _worker_startup_error = str(exc)
        LOGGER.error("Failed to start Celery worker: %s", exc, exc_info=True)
    
    yield
    
    # Shutdown
    LOGGER.info("Application shutdown: stopping Celery worker")
    _shutdown_worker(
        timeout=float(os.environ.get("CELERY_WORKER_SHUTDOWN_TIMEOUT", "15"))
    )


app = FastAPI(
    title="Celery Worker Health",
    version="1.0.0",
    lifespan=lifespan,
)


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


def _spawn_worker() -> subprocess.Popen[str]:
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
    # Capture stdout and stderr so we can see Celery output in logs
    return subprocess.Popen(
        cmd,
        env=env,
        cwd=str(django_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stderr into stdout
        text=True,
        bufsize=1,  # Line buffered
    )


def _log_worker_output(process: subprocess.Popen[str]) -> None:
    """Log Celery worker output in a background thread."""
    def log_output():
        if process.stdout:
            try:
                # Read initial output immediately to catch startup errors
                LOGGER.info("Starting to capture Celery worker output")
                for line in iter(process.stdout.readline, ''):
                    if line:
                        # Strip and log the line
                        cleaned = line.rstrip()
                        if cleaned:  # Only log non-empty lines
                            LOGGER.info("Celery: %s", cleaned)
            except Exception as exc:
                LOGGER.warning("Error reading Celery output: %s", exc, exc_info=True)
            finally:
                LOGGER.info("Stopped capturing Celery worker output")
    
    thread = threading.Thread(target=log_output, daemon=True, name="celery-output-logger")
    thread.start()
    LOGGER.debug("Started Celery output logging thread")


def ensure_worker_running() -> subprocess.Popen[str]:
    """Start the Celery worker if it is not already running."""
    global _worker_process, _worker_startup_error, _worker_start_time

    with _worker_lock:
        if _worker_process is None or _worker_process.poll() is not None:
            if _worker_process is not None:
                return_code = _worker_process.poll()
                LOGGER.warning(
                    "Previous Celery worker process exited with code %s, restarting",
                    return_code,
                )
            _worker_process = _spawn_worker()
            _worker_start_time = time.time()
            # Start logging worker output in background
            _log_worker_output(_worker_process)
            # Give it a moment to start and check for immediate failures
            time.sleep(0.5)
            if _worker_process.poll() is not None:
                error_msg = f"Celery worker process exited immediately with code {_worker_process.poll()}"
                _worker_startup_error = error_msg
                LOGGER.error(error_msg)
            else:
                _worker_startup_error = None
                LOGGER.info("Celery worker process started successfully (PID: %s)", _worker_process.pid)
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
    try:
        process = ensure_worker_running()
        running = process.poll() is None
        status_info = {
            "status": "ok" if running else "error",
            "worker_running": running,
            "returncode": process.returncode,
            "pid": process.pid,
        }
        if _worker_startup_error:
            status_info["startup_error"] = _worker_startup_error
        return status_info
    except Exception as exc:
        LOGGER.error("Error checking worker status: %s", exc, exc_info=True)
        return {
            "status": "error",
            "worker_running": False,
            "error": str(exc),
        }


@app.get("/", tags=["health"])
@app.get("/healthz", tags=["health"])
async def healthcheck() -> JSONResponse:
    """Return worker status for Cloud Run health checks.
    
    During the first 60 seconds after startup, returns 200 OK even if the
    Celery worker isn't fully ready yet, to allow time for initialization.
    """
    status_payload = _current_worker_status()
    worker_running = status_payload.get("worker_running", False)
    
    # Allow grace period of 60 seconds for worker to start up
    startup_grace_period = 60.0
    is_in_grace_period = (
        _worker_start_time is not None
        and (time.time() - _worker_start_time) < startup_grace_period
    )
    
    # Return 200 if worker is running, or if we're in grace period and process exists
    if worker_running or (is_in_grace_period and _worker_process is not None):
        http_status = status.HTTP_200_OK
        if is_in_grace_period and not worker_running:
            status_payload["status"] = "starting"
            status_payload["grace_period"] = True
    else:
        http_status = status.HTTP_503_SERVICE_UNAVAILABLE
    
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
