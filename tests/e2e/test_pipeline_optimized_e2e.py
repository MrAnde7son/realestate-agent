from __future__ import annotations

import contextlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import pytest

from orchestration.collectors.mavat_collector import MavatCollector
from orchestration.collectors.yad2_collector import Yad2Collector
from orchestration.data_pipeline import DataPipeline
from orchestration.location import LocationQuery


@dataclass
class FakePlan:
    plan_id: str
    title: str

    def __post_init__(self) -> None:
        self.status = "approved"
        self.authority = "Test Authority"
        self.entity_number = "123"
        self.approval_date = "2024-01-01"
        self.status_date = "2024-02-01"
        self.raw = {"id": self.plan_id, "title": self.title}


class FakeMavatClient:
    def __init__(self, plans):
        self._plans = plans
        self.calls: List[Dict[str, Any]] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def search_plans(self, block: str, city: str | None = None, **_):
        self.calls.append({"block": block, "city": city})
        return list(self._plans)


class StubYad2Collector(Yad2Collector):
    def __init__(self, listings: List[Any] | None = None):
        super().__init__(client=object())
        self.listings = list(listings or [])
        self.fetch_calls: List[str] = []

    def collect(self, location=None, **kwargs):
        """Overridden collect method that uses the stub listings."""
        query = location
        if query and query.street and query.city:
            address = f"{query.street} {query.city.replace('-', ' ')}"
            if address.strip():
                self.fetch_calls.append(address.strip())
                return list(self.listings)
        return []


@dataclass
class FakeListing:
    title: str
    address: str
    listing_id: str
    price: int = 0
    rooms: int = 0
    floor: int = 0
    size: int = 0
    total_size: int = 0
    property_type: str = "apartment"
    description: str = ""
    url: str = "https://example.test/listing"
    coordinates: tuple[float, float] = (34.78, 32.06)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "address": self.address,
            "listing_id": self.listing_id,
            "price": self.price,
            "rooms": self.rooms,
            "floor": self.floor,
            "size": self.size,
            "total_size": self.total_size,
            "property_type": self.property_type,
        }


def test_mavat_collector_formats_results_without_network_calls():
    plans = [FakePlan("123", "Tel Aviv Plan"), FakePlan("456", "Residential")]
    client = FakeMavatClient(plans)
    collector = MavatCollector(client=client)

    formatted = collector.collect(LocationQuery(block=6336, city="Tel Aviv"))

    assert formatted == [
        {
            "plan_id": "123",
            "title": "Tel Aviv Plan",
            "status": "approved",
            "authority": "Test Authority",
            "entity_number": "123",
            "approval_date": "2024-01-01",
            "status_date": "2024-02-01",
        },
        {
            "plan_id": "456",
            "title": "Residential",
            "status": "approved",
            "authority": "Test Authority",
            "entity_number": "123",
            "approval_date": "2024-01-01",
            "status_date": "2024-02-01",
        },
    ]
    assert client.calls == [{"block": 6336, "city": "Tel Aviv"}]


def test_yad2_collector_uses_location_query():
    listing = FakeListing(
        title="Cozy Apartment",
        address="רוזוב 14 תל אביב",
        listing_id="TLV-1",
    )
    collector = StubYad2Collector([listing])
    location = LocationQuery(city="תל אביב", street="רוזוב", house_number=14)

    listings = collector.collect(location)

    assert [listing.listing_id for listing in listings] == ["TLV-1"]
    assert collector.fetch_calls == [("רוזוב תל אביב")]


class DummyMetric:
    def __init__(self) -> None:
        self.records: List[tuple[str, float]] = []

    def labels(self, *args, **kwargs):
        return self

    def observe(self, value: float) -> None:  # Histogram interface
        self.records.append(("observe", float(value)))

    def inc(self, amount: float = 1) -> None:  # Counter interface
        self.records.append(("inc", float(amount)))


class DummyTracer:
    @contextlib.contextmanager
    def start_as_current_span(self, *args, **kwargs):
        yield


@pytest.fixture(autouse=True)
def isolate_pipeline(monkeypatch):
    import orchestration.data_pipeline as module

    monkeypatch.setattr(module, "start_metrics_server", lambda *a, **k: None)
    monkeypatch.setattr(module, "COLLECTOR_LATENCY", DummyMetric())
    monkeypatch.setattr(module, "COLLECTOR_SUCCESS", DummyMetric())
    monkeypatch.setattr(module, "COLLECTOR_FAILURE", DummyMetric())
    monkeypatch.setattr(module, "tracer", DummyTracer())
    monkeypatch.setattr(module, "_load_user_notifiers", lambda: [])
    monkeypatch.setattr(module, "track", lambda *a, **k: None)
    monkeypatch.setattr(module, "itm_to_wgs84", lambda x, y: (x / 1000.0, y / 1000.0))
    yield


class FakeQuery:
    """Mock query object that supports filter_by().first() pattern."""
    def __init__(self, session: "FakeSession", model_class: Any):
        self._session = session
        self._model_class = model_class
        self._filters = {}

    def filter_by(self, **kwargs):
        """Add filters to the query."""
        self._filters = kwargs
        return self

    def first(self):
        """Return first matching object from session.added or None."""
        for obj in self._session.added:
            # Check if object matches all filter criteria
            matches = True
            for key, value in self._filters.items():
                if not hasattr(obj, key) or getattr(obj, key) != value:
                    matches = False
                    break
            if matches:
                return obj
        return None


class FakeSession:
    def __init__(self):
        self.added: List[Any] = []
        self._id_counter = 1
        self.committed = False
        self.closed = False
        self.rolled_back = False

    def add(self, obj: Any) -> None:
        self.added.append(obj)

    def flush(self) -> None:
        for obj in self.added:
            if hasattr(obj, "id") and getattr(obj, "id", None) is None:
                setattr(obj, "id", self._id_counter)
                self._id_counter += 1

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True

    def query(self, model_class: Any):
        """Return a mock query object for the given model class."""
        return FakeQuery(self, model_class)
class StubGISCollector:
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.calls: List[Dict[str, Any]] = []

    def collect(self, location=None, **kwargs):
        self.calls.append({
            "block": getattr(location, "block", None),
            "parcel": getattr(location, "parcel", None),
            "street": getattr(location, "street", None),
        })
        return dict(self.payload)


class StubGovMapCollector:
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.calls: List[Dict[str, Any]] = []

    def collect(self, location=None, block=None, parcel=None, **kwargs):
        self.calls.append({
            "block": block,
            "parcel": parcel,
            "street": getattr(location, "street", None),
        })
        return dict(self.payload)


class StubGovCollector:
    def __init__(self, payload: Dict[str, Any]):
        self.payload = payload
        self.calls: List[Any] = []

    def collect(self, location: Optional[LocationQuery] = None, **kwargs):
        location = location or LocationQuery()
        self.calls.append(
            (
                getattr(location, "block", None),
                getattr(location, "parcel", None),
                getattr(location, "street", None),
            )
        )
        return dict(self.payload)


class StubRamiCollector:
    def __init__(self, plans: List[Dict[str, Any]]):
        self.plans = plans
        self.calls: List[Any] = []

    def collect(self, location: Optional[LocationQuery] = None, **kwargs):
        location = location or LocationQuery()
        self.calls.append((location.block, location.parcel))
        return list(self.plans)


class StubMavatCollector:
    def __init__(self, plans: List[Dict[str, Any]]):
        self.plans = plans
        self.calls: List[Any] = []

    def collect(self, location: Optional[LocationQuery] = None, **kwargs):
        location = location or LocationQuery()
        self.calls.append((location.block, location.parcel, location.city))
        return list(self.plans)


def _build_pipeline(session: FakeSession, listings: List[FakeListing]):
    govmap_payload = {
        "x": 180000,
        "y": 665000,
        "address": "רוזוב 14, תל אביב",
        "api_data": {
            "autocomplete": {"results": [{"id": 1}]},
            "parcel": {"properties": {"gushnumber": "6336", "parcelnumber": "7"}},
        },
        "addresses": [
            {"street": "רוזוב", "house_number": 14, "city": "תל אביב"}
        ],
    }
    gis_payload = {
        "x": 180010,
        "y": 665005,
        "block": "6336",
        "parcel": "7",
        "addresses": [
            {"street": "רוזוב", "house_number": 14, "city": "תל אביב"}
        ],
    }
    gov_payload = {
        "decisive": [{"plan": "תכנית"}],
        "transactions": [{"deal_amount": "1,450,000", "rooms": 3}],
    }
    rami_plans = [{"name": "Plan A"}]
    mavat_plans = [{"plan_id": "123", "title": "Plan B"}]

    pipeline = DataPipeline(
        db=None,
        db_session=session,
        yad2=StubYad2Collector(listings),
        gis=StubGISCollector(gis_payload),
        gov=StubGovCollector(gov_payload),
        govmap=StubGovMapCollector(govmap_payload),
        rami=StubRamiCollector(rami_plans),
        mavat=StubMavatCollector(mavat_plans),
    )
    return pipeline


def test_pipeline_combines_collector_results_with_stubs():
    session = FakeSession()
    listings = [FakeListing(title="Sunny flat", address="רוזוב 14 תל אביב", listing_id="TLV-1")]
    pipeline = _build_pipeline(session, listings)

    location = LocationQuery(city="תל אביב", street="רוזוב", house_number=14, block=6336, parcel=7)
    results = pipeline.run(location=location)

    # Listing plus enrichment payloads from the collectors
    sources = [
        r["source"] if isinstance(r, dict) else "yad2"
        for r in results
    ]
    assert "yad2" in sources
    assert {"govmap", "gis", "decisive", "transactions", "gov_rami", "mavat"}.issubset(set(sources))
    assert session.committed is True


def test_pipeline_handles_empty_listing_results():
    session = FakeSession()
    pipeline = _build_pipeline(session, listings=[])

    location = LocationQuery(city="תל אביב", street="רוזוב", house_number=14)
    results = pipeline.run(location=location)

    assert all(isinstance(entry, dict) for entry in results)
    assert {entry["source"] for entry in results} == {
        "govmap",
        "govmap_autocomplete",
        "gis",
        "decisive",
        "transactions",
        "gov_rami",
        "mavat",
    }
    assert session.committed is True
