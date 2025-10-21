from __future__ import annotations

from typing import Optional
from unittest.mock import patch

from core import tasks
from core.models import Asset
from orchestration.location import LocationQuery


class DummyPipeline:
    def __init__(self):
        self.calls = []

    def run(
        self,
        location: Optional[LocationQuery] = None,
        *,
        max_pages: int = 1,
        asset_id: Optional[int] = None,
    ):
        # Record a single tuple of the call arguments
        self.calls.append((location, max_pages, asset_id))
        return [42]


def test_run_data_pipeline_task(monkeypatch):
    asset = Asset(
        id=1,
        scope_type="address",
        city="City",
        street="Main",
        number=5,
    )
    # Mock ORM get & save so we don't hit DB
    monkeypatch.setattr(Asset.objects, "get", lambda id: asset)
    monkeypatch.setattr(asset, "save", lambda *args, **kwargs: None)

    dummy = DummyPipeline()

    # Patch the DataPipeline class used inside the task implementation
    with patch("orchestration.data_pipeline.DataPipeline", return_value=dummy):
        # Call the underlying function via .run (Celery Task wraps it)
        result = tasks.run_data_pipeline.run(asset_id=1, max_pages=1)

    assert result == [42]
    # Expect the pipeline to be invoked with asset's address fields
    expected_location = LocationQuery(city="City", street="Main", house_number=5)
    assert dummy.calls == [(expected_location, 1, 1)]
