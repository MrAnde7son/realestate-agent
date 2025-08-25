from __future__ import annotations

import pandas as pd

from db.database import SQLAlchemyDatabase
from db.models import Listing, SourceRecord, Transaction
from orchestration.data_pipeline import DataPipeline
from yad2.core.models import RealEstateListing
from gov.nadlan.models import Deal


class FakeYad2Scraper:
    def fetch_location_data(self, search_text):
        return {"cities": [{"id": 1}], "streets": [{"id": 2}]}

    def set_search_parameters(self, **kwargs):
        self.params = kwargs

    def scrape_all_pages(self, max_pages=1, delay=0):
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


class FakeGIS:
    def get_address_coordinates(self, street, house_number, like=True):
        return 100.0, 200.0

    def get_blocks(self, x, y):
        return [{"ms_gush": "1"}]

    def get_parcels(self, x, y):
        return [{"ms_chelka": "2"}]

    def get_building_permits(self, x, y, radius=30):
        return [{"permit": "p"}]

    def get_land_use_main(self, x, y):
        return [{"land": "use"}]

    def get_shelters(self, x, y, radius=200):
        return [{"shelter": 1}]

    def get_green_areas(self, x, y, radius=150):
        return [{"green": 1}]

    def get_noise_levels(self, x, y):
        return [{"noise": 1}]


def fake_fetch_decisive_appraisals(block: str, plot: str, max_pages: int = 1):
    return [{"title": "dec1"}]


class FakeDeals:
    def get_deals_by_address(self, address):
        return [Deal(address="Fake st 1", deal_date="2024-01-01", deal_amount=100, rooms="3", floor="1", asset_type="apt", year_built="2000", area=80)]


class FakeRami:
    def fetch_plans(self, params):
        return pd.DataFrame([{"planNumber": "111", "planId": "222"}])


def test_data_pipeline_integration():
    db = SQLAlchemyDatabase("sqlite:///:memory:")
    pipeline = DataPipeline(
        db=db,
        yad2_client=FakeYad2Scraper(),
        gis_client=FakeGIS(),
        deals_client=FakeDeals(),
        decisive_func=fake_fetch_decisive_appraisals,
        rami_client=FakeRami(),
    )

    ids = pipeline.run("Fake", 1)
    assert ids, "Pipeline did not return listing IDs"

    with db.get_session() as session:
        assert session.query(Listing).count() == 1
        assert session.query(Transaction).count() == 1
        srcs = session.query(SourceRecord).all()
        assert {s.source for s in srcs} == {"gis", "decisive", "rami"}
