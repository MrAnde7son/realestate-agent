"""Celery worker with a lightweight HTTP health endpoint for Cloud Run.

This module runs the Celery worker in the main process and starts a simple
HTTP health check server in a background thread for Cloud Run monitoring.
"""

from __future__ import annotations

import http.server
import json
import logging
import os
import socketserver
import sys
import threading
from pathlib import Path

LOGGER = logging.getLogger("orchestration.celery_worker")
_worker_ready = threading.Event()


def _configure_logging() -> None:
    """Configure logging."""
    log_level = os.environ.get("CELERY_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def _resolve_django_dir() -> Path:
    """Locate the Django project directory."""
    env_dir = os.environ.get("DJANGO_DIR")
    if env_dir:
        candidate = Path(env_dir).expanduser().resolve()
        if (candidate / "manage.py").is_file():
            return candidate
        raise RuntimeError(f"DJANGO_DIR={candidate} does not contain manage.py")

    # Auto-discover
    script_dir = Path(__file__).resolve().parent
    for candidate in (
        script_dir / "backend-django",
        script_dir.parent / "backend-django",
    ):
        if (candidate / "manage.py").is_file():
            return candidate.resolve()

    raise RuntimeError(
        "Unable to locate Django project directory; set DJANGO_DIR to override"
    )


class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    """Simple HTTP handler for health checks."""

    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path in ("/", "/healthz", "/health"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            response = {
                "status": "ok" if _worker_ready.is_set() else "starting",
                "worker_ready": _worker_ready.is_set(),
                "pid": os.getpid(),
            }
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def _run_health_server() -> None:
    """Run HTTP health check server in background thread."""
    port = int(os.environ.get("PORT", "8080"))
    handler = HealthCheckHandler

    with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
        LOGGER.info("Health check server started on port %s", port)
        httpd.serve_forever()


def main() -> None:
    """Main entry point: start Celery worker and health server."""
    _configure_logging()

    django_dir = _resolve_django_dir()
    os.chdir(django_dir)

    # Add to Python path
    sys.path.insert(0, str(django_dir.parent))
    sys.path.insert(0, str(django_dir))

    # Set environment
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    celery_app = os.environ.get("CELERY_APP", "broker_backend")
    concurrency = os.environ.get("CELERY_WORKER_CONCURRENCY", "2")
    log_level = os.environ.get("CELERY_LOG_LEVEL", "info")

    LOGGER.info("Starting Celery worker")
    LOGGER.info("Working directory: %s", django_dir)
    LOGGER.info("CELERY_BROKER_URL: %s", os.environ.get("CELERY_BROKER_URL", "NOT SET"))

    # Start health check server in background thread
    health_thread = threading.Thread(
        target=_run_health_server,
        name="health-server",
        daemon=True,
    )
    health_thread.start()
    LOGGER.info("Health check server thread started")

    # Give health server a moment to start
    import time

    time.sleep(0.5)

    # Signal that we're ready (Celery will set this when it's actually ready)
    # For now, set it immediately since the process is running
    _worker_ready.set()

    # Import and run Celery in main thread (blocks)
    try:
        from celery import __main__ as celery_main

        # Build Celery command arguments
        sys.argv = [
            "celery",
            "-A",
            celery_app,
            "worker",
            "-l",
            log_level,
            "-c",
            str(concurrency),
        ]

        LOGGER.info("Starting Celery worker: %s", " ".join(sys.argv))
        celery_main.main()
    except KeyboardInterrupt:
        LOGGER.info("Celery worker received interrupt signal")
    except Exception as exc:
        LOGGER.error("Celery worker failed: %s", exc, exc_info=True)
        raise


if __name__ == "__main__":
    main()
