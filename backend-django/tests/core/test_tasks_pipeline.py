from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from core import tasks
from core.models import Asset
from core.tasks import PIPELINE_CACHE_KEY
from orchestration.data_pipeline import CollectedPipelineData


class DummyPipeline:
    def __init__(self, collected: CollectedPipelineData):
        self.collected = collected
        self.collect_calls: List[Tuple[Any, ...]] = []
        self.persist_calls: List[Tuple[CollectedPipelineData, List[Any], Optional[int]]] = []
        self.link_calls: List[Tuple[int, CollectedPipelineData, List[Dict[str, Any]], List[Any]]] = []

    def collect_sources(self, **kwargs):
        self.collect_calls.append(tuple(kwargs.items()))
        return self.collected

    def persist_collected_data(self, collected, *, notifiers=None, asset_id=None):
        self.persist_calls.append((collected, notifiers or [], asset_id))
        return ([{"source": "yad2", "data": {"listing_id": "1"}}], [101])

    def link_asset(self, asset_id, collected, normalized, results):
        self.link_calls.append((asset_id, collected, normalized, results))


def test_run_data_pipeline_task(monkeypatch):
    asset = Asset(
        id=1,
        scope_type="address",
        city="City",
        street="Main",
        number=5,
        meta={},
    )

    monkeypatch.setattr(Asset.objects, "get", lambda id: asset)
    monkeypatch.setattr(asset, "save", lambda *args, **kwargs: None)
    monkeypatch.setattr(tasks, "track", lambda *args, **kwargs: None)

    collected = CollectedPipelineData(
        location={"city": "City", "street": "Main", "house_number": 5},
        listings=[{"listing_id": "1", "price": 100}],
    )
    dummy = DummyPipeline(collected)

    monkeypatch.setattr(
        "orchestration.data_pipeline.DataPipeline",
        lambda: dummy,
    )
    monkeypatch.setattr(
        "orchestration.data_pipeline._load_user_notifiers",
        lambda: [],
    )
    monkeypatch.setattr(
        "orchestration.data_pipeline._normalize_listings",
        lambda listings: listings,
    )

    result = tasks.run_data_pipeline.run(1, max_pages=2)

    assert result["asset_id"] == 1
    assert result["max_pages"] == 2
    assert result["listings_count"] == 1
    assert result["normalized_count"] == 1
    assert result["persisted_listing_ids"] == [101]
    assert result["status"] == "done"
    assert "completed_at" in result

    # Asset status should be updated and cache cleared
    assert asset.status == "done"
    assert asset.last_enrich_error is None
    assert PIPELINE_CACHE_KEY not in asset.meta

    # Pipeline should be invoked for collect/persist/link
    assert dummy.collect_calls
    assert dummy.persist_calls == [(collected, [], 1)]
    assert dummy.link_calls
