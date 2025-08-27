from __future__ import annotations

import pandas as pd

from db.database import SQLAlchemyDatabase
from db.models import Listing, SourceRecord, Transaction
from orchestration.data_pipeline import DataPipeline
from orchestration.collectors import (
    Yad2Collector,
    GISCollector,
    GovCollector,
    RamiCollector,
)
from yad2.core.models import RealEstateListing
from gov.nadlan.models import Deal


class FakeYad2Collector(Yad2Collector):
    def __init__(self):
        pass

    def fetch_listings(self, address, max_pages):
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

    def geocode(self, address, house_number):
        return 100.0, 200.0

    def collect(self, x, y):
        return {
            "blocks": [{"ms_gush": "1"}],
            "parcels": [{"ms_chelka": "2"}],
            "permits": [{"permit": "p"}],
            "rights": [{"land": "use"}],
            "shelters": [{"shelter": 1}],
            "green": [{"green": 1}],
            "noise": [{"noise": 1}],
        }


class FakeGovCollector(GovCollector):
    def __init__(self):
        pass

    def collect_decisive(self, block, parcel):
        return [{"title": "dec1"}]

    def collect_transactions(self, address):
        return [
            Deal(
                address="Fake st 1",
                deal_date="2024-01-01",
                deal_amount=100,
                rooms="3",
                floor="1",
                asset_type="apt",
                year_built="2000",
                area=80,
            )
        ]


class FakeRamiCollector(RamiCollector):
    def __init__(self):
        pass

    def collect(self, block, parcel):
        return [{"planNumber": "111", "planId": "222"}]


def test_data_pipeline_integration():
    db = SQLAlchemyDatabase("sqlite:///:memory:")
    pipeline = DataPipeline(
        db=db,
        yad2=FakeYad2Collector(),
        gis=FakeGISCollector(),
        gov=FakeGovCollector(),
        rami=FakeRamiCollector(),
    )

    ids = pipeline.run("Fake", 1)
    assert ids, "Pipeline did not return listing IDs"

    with db.get_session() as session:
        assert session.query(Listing).count() == 1
        assert session.query(Transaction).count() == 1
        srcs = session.query(SourceRecord).all()
        assert {s.source for s in srcs} == {"gis", "decisive", "rami"}
