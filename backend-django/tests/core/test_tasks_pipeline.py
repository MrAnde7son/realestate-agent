from __future__ import annotations

from typing import Optional
from unittest.mock import patch

from core import tasks
from core.models import Asset


class DummyPipeline:
    def __init__(self):
        self.calls = []

    def run(
        self,
        city: str,
        street: str,
        house_number: int,
        max_pages: int = 1,
        asset_id: Optional[int] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
    ):
        # Record a single tuple of the call arguments
        self.calls.append((city, street, house_number, max_pages, asset_id, block, parcel))
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
        result = tasks.run_data_pipeline.run(1, max_pages=1)

    assert result == [42]
    # Expect the pipeline to be invoked with asset's address fields
    assert dummy.calls == [("City", "Main", 5, 1, 1, "", "")]
