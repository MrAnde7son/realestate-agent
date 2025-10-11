"""Tests for Handasa permit merging helpers."""

from orchestration.data_pipeline import _merge_permits


def test_merge_permits_deduplicates_by_permission_number():
    primary = [
        {"permission_num": "123", "koteret": "GIS Permit"},
        {"permission_num": "456", "koteret": "Another"},
    ]
    fallback = [
        {"permission_num": "456", "koteret": "Duplicate from Handasa"},
        {"permission_num": "789", "koteret": "Handasa Only"},
    ]

    merged = _merge_permits(primary, fallback)

    ids = [permit["permission_num"] for permit in merged]
    assert ids == ["123", "456", "789"]


def test_merge_permits_uses_request_number_when_missing_permission():
    primary = []
    fallback = [
        {"request_num": "REQ-1", "koteret": "Missing permission"},
        {"handasa_document_guid": "guid", "koteret": "Guid only"},
    ]

    merged = _merge_permits(primary, fallback)

    assert len(merged) == 2
    assert merged[0]["request_num"] == "REQ-1"
    assert merged[1]["handasa_document_guid"] == "guid"
