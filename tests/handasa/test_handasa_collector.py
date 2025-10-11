"""Unit tests for the Handasa collector."""

from datetime import datetime

import pytest

from orchestration.collectors.handasa_collector import HandasaCollector


class DummyScraper:
    def __init__(self, documents):
        self._documents = documents
        self.calls = []

    def fetch_documents(self, block, parcel):
        self.calls.append((block, parcel))
        return list(self._documents)


def _ts(value: str) -> int:
    return int(datetime.strptime(value, "%Y-%m-%d").timestamp() * 1000)


def test_collect_normalizes_documents_and_deduplicates():
    documents = [
        {
            "Title": "היתר 12345",
            "DocumentDate": "2024-01-05",
            "DownloadURL": "https://example.com/12345.pdf",
            "DocumentDescription": "Permit description",
            "DocumentNumber": "12345",
        },
        {
            "Title": "היתר 12345",
            "DocumentDate": "2024-02-01",
            "DownloadURL": "https://example.com/duplicate.pdf",
            "DocumentDescription": "Duplicate",
            "DocumentNumber": "12345",
        },
        {
            "Title": "היתר 67890",
            "DocumentDate": "2024-03-10",
            "DownloadURL": "https://example.com/67890.pdf",
            "Status": "בתוקף",
            "DocumentGuid": "guid-67890",
        },
    ]
    scraper = DummyScraper(documents)
    collector = HandasaCollector(scraper=scraper)

    permits = collector.collect(block="6952", parcel="127")

    # Scraper is called with the provided block/parcel
    assert scraper.calls == [("6952", "127")]

    # Deduplication removes the duplicate document number
    assert len(permits) == 2

    first_permit = permits[0]
    assert first_permit["permission_num"] == "12345"
    assert first_permit["koteret"] == "היתר 12345"
    assert first_permit["sug_bakasha"] == "Permit description"
    assert first_permit["permission_date"] == _ts("2024-01-05")
    assert first_permit["url_hadmaya"] == "https://example.com/12345.pdf"
    assert first_permit["ms_gush"] == "6952"
    assert first_permit["ms_chelka"] == "127"
    assert first_permit["handasa_raw"]["DocumentDescription"] == "Permit description"

    second_permit = permits[1]
    assert second_permit["handasa_document_guid"] == "guid-67890"
    assert second_permit["building_stage"] == "בתוקף"


def test_collect_requires_block_and_parcel():
    collector = HandasaCollector(scraper=DummyScraper([]))
    with pytest.raises(ValueError):
        collector.collect(block="", parcel="127")
    with pytest.raises(ValueError):
        collector.collect(block="6952", parcel="")


def test_validate_parameters():
    collector = HandasaCollector(scraper=DummyScraper([]))
    assert collector.validate_parameters(block="1", parcel="2") is True
    assert collector.validate_parameters(block=None, parcel="2") is False
