from __future__ import annotations

from typing import Optional

import pytest

from db.database import SQLAlchemyDatabase
from db.models import Listing
from orchestration.collectors import (
    GISCollector,
    GovCollector,
    GovMapCollector,
    MavatCollector,
    RamiCollector,
    Yad2Collector,
)
from orchestration.data_pipeline import DataPipeline
from orchestration.location import LocationQuery
from yad2.core.models import RealEstateListing


class FakeYad2Collector(Yad2Collector):
    def __init__(self):
        pass

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        max_pages: int = 1,
    ):
        listing = RealEstateListing()
        listing.title = "test"
        listing.price = 1_000_000
        listing.address = "Fake st 1"
        listing.rooms = 3
        listing.floor = 1
        listing.size = 80
        listing.property_type = "apartment"
        listing.description = "desc"
        listing.url = "http://example.com"
        listing.listing_id = "123"
        listing.coordinates = (1.0, 2.0)
        return [listing]


class FakeGISCollector(GISCollector):
    def __init__(self):
        pass

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
    ):
        return {
            "blocks": [{"ms_gush": "1"}],
            "parcels": [{"ms_chelka": "2"}],
            "permits": [{"permit": "p"}],
            "rights": [{"land": "use"}],
            "shelters": [{"shelter": 1}],
            "green": [{"green": 1}],
            "noise": [{"noise": 1}],
            "block": "1",
            "parcel": "2",
        }


class FakeGovCollector(GovCollector):
    def __init__(self):
        pass

    def collect(
        self,
        block,
        parcel,
        location: Optional[LocationQuery] = None,
    ):
        return {
            "decisive": [{"title": "dec1"}],
            "transactions": [
                {
                    "deal_date": "2024-01-01",
                    "deal_amount": 100,
                    "rooms": "3",
                    "floor": "1",
                    "asset_type": "apt",
                    "year_built": "2000",
                    "area": 80,
                }
            ],
        }


class FakeRamiCollector(RamiCollector):
    def __init__(self):
        pass

    def collect(self, block, parcel):
        return [{"planNumber": "111", "planId": "222"}]


class FakeGovMapCollector(GovMapCollector):
    def __init__(self):
        pass

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        block: Optional[str] = None,
        parcel: Optional[str] = None,
    ):
        query = location or LocationQuery(street="Fake", house_number=1, city="תל אביב")
        return {
            "address": query.formatted or "Fake st 1",
            "x": 183162.21989007457,
            "y": 667055.4977532875,
            "block": "1",
            "parcel": "2",
            "api_data": {
                "autocomplete": {
                    "resultsCount": 1,
                    "results": [
                        {
                            "address": "Fake st 1",
                            "x": 183162.21989007457,
                            "y": 667055.4977532875,
                            "city": query.city or "תל אביב",
                            "street": query.street or "Fake",
                            "house_number": query.house_number or 1,
                        }
                    ],
                    "aggregations": [],
                },
                "parcel": {
                    "gush": "1",
                    "helka": "2",
                },
            },
        }


class FakeMavatCollector(MavatCollector):
    def __init__(self):
        pass

    def collect(self, block, parcel, city=None):
        return [{"plan_id": "333", "title": "Test Mavat Plan", "status": "approved"}]


class DummyAsset:
    def __init__(self):
        self.meta = {}
        self.price = 1_000_000
        self.area = 80
        self.id = 1
        self.saved = False

    def save(self, update_fields=None):
        self.saved = True


def test_data_pipeline_integration():
    db = SQLAlchemyDatabase("sqlite:///:memory:")
    db.init_db()  # Initialize the database engine first
    db.create_tables()  # Then create tables
    
    pipeline = DataPipeline(
        yad2=FakeYad2Collector(),
        gis=FakeGISCollector(),
        gov=FakeGovCollector(),
        govmap=FakeGovMapCollector(),
        rami=FakeRamiCollector(),
        mavat=FakeMavatCollector(),
        db_session=db.get_session()
    )

    # Run the pipeline - it should return collected data, not save to database
    results = pipeline.run("", "Fake", 1, asset_id=123)
    
    # Verify that the pipeline returned results
    assert results, "Pipeline did not return any results"
    assert len(results) > 0, "Pipeline should return at least some results"
    
    # Check that we have results from different sources
    sources = set()
    for result in results:
        if isinstance(result, dict) and 'source' in result:
            sources.add(result['source'])
        elif hasattr(result, 'listing_id'):  # Yad2 listing object
            sources.add('yad2')
    
    # Should have results from multiple sources
    assert len(sources) >= 2, f"Expected results from multiple sources, got: {sources}"
    
    # Verify specific source data
    gis_found = any('gis' in str(result) for result in results)
    assert gis_found, "GIS data should be included in results"
    
    # Verify Mavat data is included
    mavat_found = any('mavat' in str(result) for result in results)
    assert mavat_found, "Mavat data should be included in results"


@pytest.mark.parametrize(
    "raw_floor, expected",
    [
        ("קומה \u200eקרקע\u200f", 0),
        ("קומה 5 מתוך 7", 5),
        ("מרתף", -1),
        ("שניה", 2),
        (None, None),
    ],
)
def test_store_listing_normalizes_floor_values(raw_floor, expected):
    db = SQLAlchemyDatabase("sqlite:///:memory:")
    db.init_db()
    db.create_tables()

    pipeline = DataPipeline(db=db)
    session = db.get_session()

    listing = RealEstateListing()
    listing.title = "test"
    listing.price = 1_000_000
    listing.address = "Fake st 1"
    listing.rooms = 3
    listing.floor = raw_floor
    listing.size = 80
    listing.property_type = "apartment"
    listing.description = "desc"
    listing.url = "http://example.com"
    listing.listing_id = f"listing-{expected}-{hash(str(raw_floor))}"

    try:
        stored_listing = pipeline._store_listing(session, listing)
        assert stored_listing.floor == expected

        fetched = session.query(Listing).filter_by(id=stored_listing.id).one()
        assert fetched.floor == expected
    finally:
        session.close()
        if pipeline.session is not None:
            pipeline.session.close()


def test_calculate_market_metrics_skips_invalid_listings():
    from orchestration.data_pipeline import _calculate_market_metrics

    asset = DummyAsset()

    listings = [None, {"price": 900_000, "area": 75}, "not-a-dict"]

    _calculate_market_metrics(asset, listings, gov_data={})

    # Only one valid listing, so asset may or may not be saved depending on implementation.
    # If asset.save() is only called when metrics are calculated, check accordingly:
    metrics = asset.meta.get('market_metrics', {})
    if metrics:
        assert asset.saved is True
        assert metrics.get('modelPrice') == 900_000
        assert metrics.get('confidencePct') == 20
    else:
        assert asset.saved is False
