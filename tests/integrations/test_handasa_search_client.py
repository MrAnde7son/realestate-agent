from __future__ import annotations

from typing import Any, Dict

from handasa.client import (
    BASE_SELECT_PROPERTIES,
    CSOM_ALL_PROPERTIES_ALLOWLIST,
    HandasaClient,
    HandasaSearchClient,
    HandasaSearchConfig,
    HandasaSearchFilters,
)


def test_kql_builder_with_multiple_filters():
    cfg = HandasaSearchConfig(base_url="https://example.com")
    client = HandasaSearchClient(cfg)
    filters = HandasaSearchFilters(
        folder_id="12345",
        blocks_parcels="678",
        doc_date_from="2024-01-01",
        doc_date_to="2024-03-31",
        document_type_in=["type-a", "type-b"],
        file_extension_in=["pdf", "dwg"],
        publishable=True,
    )

    kql = client._build_kql(filters)

    assert 'TlvMPEngFolderId:"12345"' in kql
    assert 'TlvMPEngFolderBlocksParcels:"678"' in kql
    assert 'TlvMPEngDocumentType:"type-a"' in kql
    assert 'TlvMPEngDocumentType:"type-b"' in kql
    assert "TlvMPEngDocDate>=2024-01-01T00:00:00Z" in kql
    assert "TlvMPEngDocDate<=2024-03-31T23:59:59Z" in kql
    assert "FileExtension:\"pdf\"" in kql
    assert "FileExtension:\"dwg\"" in kql
    # Default exclusions and booleans should still be present
    assert "-TlvMPEngDocumentType:" in kql
    assert "TlvMPEngIsConnectedDoc:false" in kql
    assert "TlvMPEngSensitiveByFolderId:false" in kql
    assert "TlvMPEngPublishable:true" in kql


def test_pagination_collects_all_pages(monkeypatch):
    cfg = HandasaSearchConfig(base_url="https://example.com", use_rest=True)
    client = HandasaSearchClient(cfg)
    filters = HandasaSearchFilters()

    pages = [
        {"items": [{"Title": "doc1"}], "total_rows": 3},
        {"items": [{"Title": "doc2"}], "total_rows": 3},
        {"items": [{"Title": "doc3"}], "total_rows": 3},
    ]
    calls = {"count": 0}

    def fake_execute_rest_request(**kwargs):
        index = calls["count"]
        calls["count"] += 1
        return pages[index]

    monkeypatch.setattr(client, "_execute_rest_request", fake_execute_rest_request)
    monkeypatch.setattr(client, "_sleep", lambda duration=None: None)

    result = client.search(filters, row_limit=1, all_pages=True)

    assert calls["count"] == 3
    assert result["total_rows"] == 3
    assert [item["Title"] for item in result["items"]] == ["doc1", "doc2", "doc3"]


def test_select_properties_all_modes():
    cfg_rest = HandasaSearchConfig(base_url="https://example.com", use_rest=True)
    rest_client = HandasaSearchClient(cfg_rest)
    rest_props = rest_client._merge_select_properties(["CustomField"], True, backend="rest")
    assert rest_props[0] == "*"
    assert "CustomField" in rest_props
    for base_prop in BASE_SELECT_PROPERTIES:
        assert base_prop in rest_props

    rest_payload = rest_client._build_rest_payload(
        querytext="*",
        row_limit=50,
        start_row=0,
        select_properties=rest_props,
        refinement_filters=[],
        refiners=None,
        sort=None,
        list_id=None,
        list_item_id=None,
    )
    assert rest_payload["request"]["SelectProperties"]["results"][0] == "*"

    cfg_csom = HandasaSearchConfig(base_url="https://example.com", use_rest=False)
    csom_client = HandasaSearchClient(cfg_csom)
    csom_props = csom_client._merge_select_properties(["AnotherField"], True, backend="csom")
    for base_prop in BASE_SELECT_PROPERTIES:
        assert base_prop in csom_props
    for allowed in CSOM_ALL_PROPERTIES_ALLOWLIST:
        assert allowed in csom_props
    assert "AnotherField" in csom_props
    assert "*" not in csom_props

    csom_payload = csom_client._build_csom_payload(
        querytext="*",
        row_limit=50,
        start_row=0,
        select_properties=csom_props,
        refinement_filters=[],
        refiners=None,
        sort=None,
        list_id=None,
        list_item_id=None,
    )
    assert "AnotherField" in csom_payload
    assert "TlvMPEngPermitNum" in csom_payload
    assert "<Object Type=\"String\">*</Object>" not in csom_payload


def test_get_archive_uses_dynamic_search(monkeypatch):
    client = HandasaClient()
    calls: Dict[str, Any] = {}

    class StubSearch:
        def build_archive_kql(self, block_param: str) -> str:
            calls["block_param"] = block_param
            return f"KQL({block_param})"

        def search(self, filters: HandasaSearchFilters, **kwargs: Any) -> Dict[str, Any]:
            calls["filters"] = filters
            calls["search_kwargs"] = kwargs
            return {
                "items": [
                    {
                        "UniqueID": "{abc}",
                        "Path": "https://example.com/doc.pdf",
                        "TlvMPEngDocumentType": "היתר",
                        "TlvMPEngDocDate": "2024-01-01T00:00:00Z",
                    }
                ]
            }

    client.search_client = StubSearch()
    monkeypatch.setattr(client, "_get_request_digest", lambda block: "digest-token")

    results = client.get_archive("1234")

    assert calls["block_param"] == "1234"
    assert calls["search_kwargs"]["request_digest"] == "digest-token"
    assert calls["search_kwargs"]["querytext_override"] == "KQL(1234)"
    assert results[0]["source"] == "Handasa"
