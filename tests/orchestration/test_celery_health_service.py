import importlib
import signal

import pytest

from fastapi.testclient import TestClient

import orchestration.celery_health_service as celery_service


class DummyProcess:
    def __init__(self, returncode=None, pid=4321):
        self._returncode = returncode
        self.pid = pid
        self.sent_signals = []
        self.wait_called = False

    def poll(self):
        return self._returncode

    @property
    def returncode(self):
        return self._returncode

    def send_signal(self, sig):
        self.sent_signals.append(sig)
        if self._returncode is None:
            # Simulate clean shutdown when asked to terminate
            self._returncode = 0

    def wait(self, timeout=None):
        self.wait_called = True
        return self._returncode

    def kill(self):
        self.sent_signals.append("KILL")
        self._returncode = -9


def reload_service(monkeypatch, spawn_sequence):
    module = importlib.reload(celery_service)

    sequence_iter = iter(spawn_sequence)

    def fake_spawn():
        return next(sequence_iter)

    monkeypatch.setattr(module, "_spawn_worker", fake_spawn)
    return module


def test_healthcheck_returns_ok(monkeypatch):
    dummy_proc = DummyProcess(returncode=None)
    module = reload_service(monkeypatch, [dummy_proc])

    with TestClient(module.app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["worker_running"] is True


def test_healthcheck_recovers_dead_worker(monkeypatch):
    crashed = DummyProcess(returncode=1)
    healthy = DummyProcess(returncode=None)
    module = reload_service(monkeypatch, [crashed, healthy])

    with TestClient(module.app) as client:
        response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json()["worker_running"] is True


def test_shutdown_terminates_worker(monkeypatch):
    dummy_proc = DummyProcess(returncode=None)
    module = reload_service(monkeypatch, [dummy_proc])

    with TestClient(module.app) as client:
        client.get("/healthz")

    assert signal.SIGTERM in dummy_proc.sent_signals
    assert dummy_proc.wait_called


def test_resolve_django_dir_uses_env_override(monkeypatch, tmp_path):
    module = importlib.reload(celery_service)
    target_dir = (tmp_path / "backend").resolve()
    manage_py = target_dir / "manage.py"
    manage_py.parent.mkdir(parents=True, exist_ok=True)
    manage_py.write_text("# dummy manage.py")

    monkeypatch.setenv("DJANGO_DIR", str(target_dir))

    resolved = module._resolve_django_dir()

    assert resolved == target_dir


def test_resolve_django_dir_auto_discovers_backend(monkeypatch, tmp_path):
    module = importlib.reload(celery_service)
    project_root = tmp_path / "project"
    backend_dir = project_root / "backend-django"
    backend_dir.mkdir(parents=True)
    (backend_dir / "manage.py").write_text("# dummy manage.py")

    def fake_roots():
        return [project_root]

    monkeypatch.delenv("DJANGO_DIR", raising=False)
    monkeypatch.setattr(module, "_iter_candidate_roots", fake_roots)

    resolved = module._resolve_django_dir()

    assert resolved == backend_dir.resolve()


def test_resolve_django_dir_errors_when_missing(monkeypatch):
    module = importlib.reload(celery_service)

    def fake_roots():
        return []

    monkeypatch.delenv("DJANGO_DIR", raising=False)
    monkeypatch.setattr(module, "_iter_candidate_roots", fake_roots)

    with pytest.raises(RuntimeError):
        module._resolve_django_dir()


def test_spawn_worker_uses_resolved_directory(monkeypatch, tmp_path):
    module = importlib.reload(celery_service)
    django_dir = (tmp_path / "backend").resolve()

    monkeypatch.setattr(module, "_resolve_django_dir", lambda: django_dir)

    captured = {}

    def fake_popen(cmd, env=None, cwd=None):
        captured["cmd"] = cmd
        captured["env"] = env
        captured["cwd"] = cwd
        return DummyProcess(returncode=None)

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)

    proc = module._spawn_worker()

    assert isinstance(proc, DummyProcess)
    assert captured["cwd"] == str(django_dir)
    workdir_index = captured["cmd"].index("--workdir")
    assert captured["cmd"][workdir_index + 1] == str(django_dir)
