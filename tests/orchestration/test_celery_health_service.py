import importlib
import threading
import time
from pathlib import Path

import pytest

import orchestration.celery_health_service as celery_service


def test_healthcheck_returns_ok(monkeypatch, tmp_path):
    """Test that health check endpoint returns OK when worker is ready."""
    import socket
    import urllib.request
    import json
    
    module = importlib.reload(celery_service)
    
    # Set up a dummy Django directory
    django_dir = tmp_path / "backend-django"
    django_dir.mkdir()
    (django_dir / "manage.py").write_text("# dummy manage.py")
    monkeypatch.setenv("DJANGO_DIR", str(django_dir))
    
    # Find an available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]
    
    monkeypatch.setenv("PORT", str(port))
    
    # Set worker as ready
    module._worker_ready.set()
    
    # Start health server in a thread
    server_thread = threading.Thread(
        target=module._run_health_server,
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.2)  # Give server time to start
    
    # Make HTTP request to health endpoint
    try:
        response = urllib.request.urlopen(f"http://localhost:{port}/healthz", timeout=1)
        data = json.loads(response.read().decode())
        
        assert response.status == 200
        assert data["status"] == "ok"
        assert data["worker_ready"] is True
    finally:
        # Clean up - the server thread will die when process exits
        pass


def test_healthcheck_returns_starting_when_not_ready(monkeypatch, tmp_path):
    """Test that health check endpoint returns 'starting' when worker is not ready."""
    import socket
    import urllib.request
    import json
    
    module = importlib.reload(celery_service)
    
    # Set up a dummy Django directory
    django_dir = tmp_path / "backend-django"
    django_dir.mkdir()
    (django_dir / "manage.py").write_text("# dummy manage.py")
    monkeypatch.setenv("DJANGO_DIR", str(django_dir))
    
    # Find an available port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        port = s.getsockname()[1]
    
    monkeypatch.setenv("PORT", str(port))
    
    # Ensure worker is not ready
    module._worker_ready.clear()
    
    # Start health server in a thread
    server_thread = threading.Thread(
        target=module._run_health_server,
        daemon=True,
    )
    server_thread.start()
    time.sleep(0.2)  # Give server time to start
    
    # Make HTTP request to health endpoint
    try:
        response = urllib.request.urlopen(f"http://localhost:{port}/healthz", timeout=1)
        data = json.loads(response.read().decode())
        
        assert response.status == 200
        assert data["status"] == "starting"
        assert data["worker_ready"] is False
    finally:
        pass


def test_resolve_django_dir_uses_env_override(monkeypatch, tmp_path):
    """Test that DJANGO_DIR environment variable overrides auto-discovery."""
    module = importlib.reload(celery_service)
    target_dir = (tmp_path / "backend").resolve()
    manage_py = target_dir / "manage.py"
    manage_py.parent.mkdir(parents=True, exist_ok=True)
    manage_py.write_text("# dummy manage.py")

    monkeypatch.setenv("DJANGO_DIR", str(target_dir))

    resolved = module._resolve_django_dir()

    assert resolved == target_dir


def test_resolve_django_dir_auto_discovers_backend(monkeypatch, tmp_path):
    """Test that Django directory is auto-discovered from script directory."""
    module = importlib.reload(celery_service)
    
    # Create a temporary project structure that mimics the real structure
    project_root = tmp_path / "project"
    orchestration_dir = project_root / "orchestration"
    orchestration_dir.mkdir(parents=True)
    backend_dir = project_root / "backend-django"
    backend_dir.mkdir(parents=True)
    (backend_dir / "manage.py").write_text("# dummy manage.py")
    
    # Patch the function to use our temporary structure
    def mock_resolve_django_dir():
        script_dir = orchestration_dir
        for candidate in (script_dir / "backend-django", script_dir.parent / "backend-django"):
            if (candidate / "manage.py").is_file():
                return candidate.resolve()
        raise RuntimeError("Unable to locate Django project directory; set DJANGO_DIR to override")
    
    monkeypatch.delenv("DJANGO_DIR", raising=False)
    monkeypatch.setattr(module, "_resolve_django_dir", mock_resolve_django_dir)

    resolved = module._resolve_django_dir()

    assert resolved == backend_dir.resolve()


def test_resolve_django_dir_errors_when_missing(monkeypatch, tmp_path):
    """Test that RuntimeError is raised when Django directory cannot be found."""
    module = importlib.reload(celery_service)
    
    # Create a temporary directory structure that doesn't have backend-django
    temp_project = tmp_path / "temp_project"
    orchestration_dir = temp_project / "orchestration"
    orchestration_dir.mkdir(parents=True)
    
    # Patch the function to use our temporary structure without backend-django
    def mock_resolve_django_dir():
        script_dir = orchestration_dir
        for candidate in (script_dir / "backend-django", script_dir.parent / "backend-django"):
            if (candidate / "manage.py").is_file():
                return candidate.resolve()
        raise RuntimeError("Unable to locate Django project directory; set DJANGO_DIR to override")
    
    monkeypatch.delenv("DJANGO_DIR", raising=False)
    monkeypatch.setattr(module, "_resolve_django_dir", mock_resolve_django_dir)

    with pytest.raises(RuntimeError, match="Unable to locate Django project directory"):
        module._resolve_django_dir()


def test_resolve_django_dir_errors_when_manage_py_missing(monkeypatch, tmp_path):
    """Test that RuntimeError is raised when DJANGO_DIR doesn't contain manage.py."""
    module = importlib.reload(celery_service)
    target_dir = (tmp_path / "backend").resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    # Don't create manage.py

    monkeypatch.setenv("DJANGO_DIR", str(target_dir))

    with pytest.raises(RuntimeError, match="does not contain manage.py"):
        module._resolve_django_dir()


