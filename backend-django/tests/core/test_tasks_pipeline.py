from __future__ import annotations

import pytest
from celery import exceptions as celery_exceptions

from core import tasks


def test_run_data_pipeline_task(monkeypatch):
    class DummySignature:
        def __init__(self, name: str, args: tuple, kwargs: dict):
            self.name = name
            self.args = args
            self.kwargs = kwargs
            self.options: dict = {}

        def set(self, **options):
            self.options.update(options)
            return self

    def fake_collect_s(*args, **kwargs):
        return DummySignature("collect", args, kwargs)

    def fake_normalize_s(*args, **kwargs):
        return DummySignature("normalize", args, kwargs)

    def fake_persist_s(*args, **kwargs):
        return DummySignature("persist", args, kwargs)

    def fake_link_s(*args, **kwargs):
        return DummySignature("link", args, kwargs)

    monkeypatch.setattr(tasks.collect_asset_data, "s", fake_collect_s)
    monkeypatch.setattr(tasks.normalize_asset_data, "s", fake_normalize_s)
    monkeypatch.setattr(tasks.persist_asset_data, "s", fake_persist_s)
    monkeypatch.setattr(tasks.link_asset_data, "s", fake_link_s)

    captured = {}

    class DummyWorkflow:
        def __init__(self, args, kwargs):
            self.signatures = args
            self.kwargs = kwargs
            self.options = {}

        def set(self, **options):
            self.options.update(options)
            return self

        def freeze(self, *args, **kwargs):  # pragma: no cover - Celery stub
            return self

        def delay(self, *args, **kwargs):  # pragma: no cover - Celery stub
            return None

    def fake_chain(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return DummyWorkflow(args, kwargs)

    monkeypatch.setattr(tasks, "chain", fake_chain)

    with pytest.raises(celery_exceptions.Ignore):
        tasks.run_data_pipeline.run(asset_id=1)

    collected_names = tuple(
        (sig.name, sig.args, sig.kwargs) for sig in captured["args"]
    )
    assert collected_names == (
        ("collect", (), {"asset_id": 1}),
        ("normalize", (), {}),
        ("persist", (), {}),
        ("link", (), {}),
    )
    assert captured["kwargs"] == {}
