"""Integration tests for Handasa permit fallback in the data pipeline."""

from typing import Optional

from orchestration.data_pipeline import DataPipeline
from orchestration.location import LocationQuery
from orchestration.collectors import (
    GISCollector,
    GovCollector,
    GovMapCollector,
    RamiCollector,
    MavatCollector,
    Yad2Collector,
)


class DummyYad2(Yad2Collector):
    def collect(self, location: Optional[LocationQuery] = None, max_pages: int = 1):  # type: ignore[override]
        return []


class GISNoPermits(GISCollector):
    def collect(  # type: ignore[override]
        self,
        location: Optional[LocationQuery] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
    ):
        return {
            "blocks": [{"ms_gush": "10"}],
            "parcels": [{"ms_chelka": "20"}],
            "permits": [],
            "block": "10",
            "parcel": "20",
        }


class DummyGov(GovCollector):
    def collect(self, block, parcel, location: Optional[LocationQuery] = None, **kwargs):  # type: ignore[override]
        return {"decisive": [], "transactions": []}


class DummyRami(RamiCollector):
    def collect(self, block=None, parcel=None, **kwargs):  # type: ignore[override]
        return []


class DummyGovMap(GovMapCollector):
    def collect(self, location: Optional[LocationQuery] = None, block: Optional[str] = None, parcel: Optional[str] = None):  # type: ignore[override]
        return {"block": block or "10", "parcel": parcel or "20", "address": "Fake 10"}


class DummyMavat(MavatCollector):
    def collect(self, block=None, parcel=None, city=None):  # type: ignore[override]
        return []


class StubHandasa:
    def __init__(self, permits):
        self.permits = permits

    def collect(self, *, block: str, parcel: str):
        return list(self.permits)


def test_pipeline_uses_handasa_permits_when_gis_empty():
    pipeline = DataPipeline(
        yad2=DummyYad2(),
        gis=GISNoPermits(),
        gov=DummyGov(),
        govmap=DummyGovMap(),
        rami=DummyRami(),
        mavat=DummyMavat(),
    )
    pipeline.handasa = StubHandasa([
        {
            "permission_num": "H-1",
            "koteret": "Handasa Permit",
            "url_hadmaya": "https://example.com/permit.pdf",
        }
    ])

    results = pipeline.run("", "Fake", 1, asset_id=42)
    gis_payload = next(
        item["data"]
        for item in results
        if isinstance(item, dict) and item.get("source") == "gis"
    )

    assert gis_payload["permits"][0]["permission_num"] == "H-1"
    assert gis_payload.get("permits_source") == "handasa"
