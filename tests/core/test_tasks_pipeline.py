from __future__ import annotations

from unittest.mock import patch

from core import tasks
from core.models import Asset


class DummyPipeline:
    def __init__(self):
        self.calls = []

    def run(self, address, number, max_pages=1, asset_id=None):
        self.calls.append((address, number, max_pages, asset_id))
        return [42]


def test_run_data_pipeline_task(monkeypatch):
    asset = Asset(id=1, scope_type='address', city='City', street='Main', number=5)
    monkeypatch.setattr(Asset.objects, 'get', lambda id: asset)
    monkeypatch.setattr(asset, 'save', lambda *args, **kwargs: None)
    dummy = DummyPipeline()
    
    # Mock the orchestration import at the module level where it's imported from
    with patch('orchestration.data_pipeline.DataPipeline', return_value=dummy):
        result = tasks.run_data_pipeline.run(1)

    assert result == [42]
    assert dummy.calls == [('Main', 5, 1, 1)]
