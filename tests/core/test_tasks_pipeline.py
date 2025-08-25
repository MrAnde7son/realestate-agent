import pytest

from core import tasks
from core.models import Asset


class DummyPipeline:
    def __init__(self):
        self.calls = []

    def run(self, address, number, max_pages=1):
        self.calls.append((address, number, max_pages))
        return [42]


def test_run_data_pipeline_task(monkeypatch):
    asset = Asset(scope_type='address', city='City', street='Main', number=5)
    monkeypatch.setattr(Asset.objects, 'get', lambda id: asset)
    dummy = DummyPipeline()
    monkeypatch.setattr(tasks, 'DataPipeline', lambda: dummy)

    result = tasks.run_data_pipeline.run(1)

    assert result == [42]
    assert dummy.calls == [('Main', 5, 1)]
