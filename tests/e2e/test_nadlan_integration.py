"""Deterministic integration checks for GovCollector.

The original version of this module drove Selenium and remote APIs, making CI
runs extremely slow and flaky.  These tests exercise the same integration
points but with predictable in-memory doubles so we can still assert on the
shape of the collected data.
"""

from __future__ import annotations

from typing import Dict

import pytest

from gov.decisive import DecisiveAppraisal
from gov.nadlan.models import Deal
from orchestration.collectors.gov_collector import GovCollector
from orchestration.location import LocationQuery

from .fakes import FakeDecisiveClient, FakeNadlanScraper


def _deal(**overrides: object) -> Deal:
    payload: Dict[str, object] = {
        "address": "רוזוב 14, תל אביב-יפו",
        "deal_amount": 2_500_000,
        "deal_date": "2023-01-15",
        "rooms": "3",
        "floor": "2",
        "asset_type": "דירה",
        "year_built": "2010",
        "area": 85.5,
        "parcelNum": "6638-68-5",
    }
    payload.update(overrides)
    return Deal.from_item(payload)


def _appraisal(**overrides: object) -> DecisiveAppraisal:
    base = {
        "title": "Appraisal",
        "date": "15.01.2023",
        "appraiser": "צוות",
        "committee": "ועדה",
        "pdf_url": "https://example.invalid/appraisal.pdf",
        "appraisal_type": "full",
        "appraisal_version": "1",
        "appraiser_type": "city",
        "block": "6336",
        "plot": "7",
        "publicity_date": "16.01.2023",
    }
    base.update(overrides)
    return DecisiveAppraisal(**base)


def test_gov_collector_combines_transactions_and_decisive_data():
    deals = [_deal(deal_amount=2_800_000), _deal(deal_amount=3_100_000)]
    scraper = FakeNadlanScraper(deals)
    appraisals = [_appraisal(title="תכנית א"), _appraisal(title="תכנית ב", plot="8")]
    decisive_client = FakeDecisiveClient(appraisals)
    collector = GovCollector(deals_client=scraper, decisive_client=decisive_client)

    location = LocationQuery(city="תל אביב", street="רוזוב", house_number=14, block="6336", parcel="7")
    result = collector.collect(location=location)

    assert [entry["deal_amount"] for entry in result["transactions"]] == [2_800_000, 3_100_000]
    assert [entry["title"] for entry in result["decisive"]] == ["תכנית א", "תכנית ב"]
    assert scraper.calls == ["רוזוב 14 תל אביב"]
    assert decisive_client.calls == [("6336", "", 1)]


def test_gov_collector_handles_external_failures_gracefully():
    scraper = FakeNadlanScraper([], fail=True)
    decisive_client = FakeDecisiveClient([], fail=True)
    collector = GovCollector(deals_client=scraper, decisive_client=decisive_client)

    location = LocationQuery(city="תל אביב", street="רוזוב", house_number=14, block="6336", parcel="7")
    result = collector.collect(location=location)

    assert result == {"decisive": [], "transactions": []}


def test_validate_parameters_requires_location():
    collector = GovCollector(
        deals_client=FakeNadlanScraper(), decisive_client=FakeDecisiveClient()
    )
    good_location = LocationQuery(city="תל אביב", street="רוזוב", house_number=14, block="6336", parcel="7")

    assert collector.validate_parameters(location=good_location) is True
    assert collector.validate_parameters(location=None) is False


@pytest.mark.parametrize(
    "location,expected",
    [
        (LocationQuery(city="תל אביב", street="רוזוב", block="6336", parcel="7"), "רוזוב תל אביב"),
        (LocationQuery(city="תל אביב", block="6336", parcel="7"), "תל אביב"),
        (LocationQuery(street="רוזוב", house_number=10, block="6336", parcel="7"), "רוזוב 10"),
    ],
)
def test_scraper_receives_human_readable_address(location: LocationQuery, expected: str):
    scraper = FakeNadlanScraper([_deal()])
    collector = GovCollector(deals_client=scraper, decisive_client=FakeDecisiveClient())

    collector.collect(location=location)

    assert scraper.calls == [expected]
