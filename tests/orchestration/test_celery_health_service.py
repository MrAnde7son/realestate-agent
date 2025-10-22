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


def test_spawn_worker_requires_django_dir(monkeypatch):
    module = importlib.reload(celery_service)
    monkeypatch.delenv("DJANGO_DIR", raising=False)

    with pytest.raises(RuntimeError):
        module._spawn_worker()


def test_spawn_worker_uses_configured_directory(monkeypatch, tmp_path):
    module = importlib.reload(celery_service)
    django_dir = tmp_path / "backend"
    monkeypatch.setenv("DJANGO_DIR", str(django_dir))

    captured = {}

    def fake_popen(cmd, env=None, cwd=None):
        captured["cmd"] = cmd
        captured["env"] = env
        captured["cwd"] = cwd
        return DummyProcess(returncode=None)

    monkeypatch.setattr(module.subprocess, "Popen", fake_popen)

    proc = module._spawn_worker()

    assert isinstance(proc, DummyProcess)
    assert captured["cwd"] == str(django_dir.resolve())
    workdir_index = captured["cmd"].index("--workdir")
    assert captured["cmd"][workdir_index + 1] == str(django_dir.resolve())
