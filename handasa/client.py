from __future__ import annotations

import base64
import json
import logging
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from json import loads
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import requests

logger = logging.getLogger(__name__)

SEARCH_RESULTS_URL = "https://handasa.tel-aviv.gov.il/Pages/SearchResultsAnonPageNew.aspx"
PROCESS_QUERY_URL = "https://handasa.tel-aviv.gov.il/_vti_bin/client.svc/ProcessQuery"
FILES_API_URL = "https://handasa.tel-aviv.gov.il/api/files"
CONTEXT_INFO_URL = "https://handasa.tel-aviv.gov.il/_api/contextinfo"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
_DIGEST_PATTERN = re.compile(r'"formDigestValue"\s*:\s*"([^"]+)"')



DEFAULT_DOCUMENT_TYPE_EXCLUSIONS = [
    "תיק פקוח",
    "פיקוח-אחר",
    "מכתבים/תכתובות-שימור",
    "תביעות,צווים מינהליים",
    "דואר נכנס ויוצא פיקוח על הבניה",
]

BASE_SELECT_PROPERTIES = [
    "Title",
    "Path",
    "SPWebUrl",
    "UniqueID",
    "FileExtension",
    "ListItemID",
    "ListID",
    "ContentTypeId",
    "TlvMPEngDocumentType",
    "TlvMPEngDocDate",
]

COMMON_PROPS = [
    "Title",
    "Path",
    "Author",
    "Size",
    "Write",
    "HitHighlightedSummary",
    "SPWebUrl",
    "UniqueID",
    "FileExtension",
    "ListItemID",
    "ListID",
    "ContentTypeId",
    "TlvMPEngWebsioPreview",
    "TlvMPEngFolderId",
    "TlvMPEngFolderStreetCodes",
    "TlvMPEngFolderStreetCodeHouseNum",
    "TlvMPEngFolderStreetCodeHouseNumEntrance",
    "TlvMPEngFolderBlocks",
    "TlvMPEngFolderBlocksParcels",
    "DocumentLink",
    "TlvMPEngDocumentType",
    "TlvMPEngDocDate",
    "TlvMPEngRequestNum",
    "TlvMPEngOnlineReqNum",
    "TlvMPEngPermitNum",
]

CSOM_ALL_PROPERTIES_ALLOWLIST = list(dict.fromkeys(BASE_SELECT_PROPERTIES + COMMON_PROPS))


@dataclass
class HandasaSearchConfig:
    base_url: str
    culture_lcid: int = 1037
    timezone_id: int = 27
    list_id: Optional[str] = None
    list_item_id: Optional[int] = None
    client_type: str = ""
    results_url_template: str = (
        "https://handasa.tel-aviv.gov.il/Pages/SearchResultsAnonPageNew.aspx?block=__BLOCK_PARAM__"
    )
    use_rest: bool = True
    timeout_sec: float = 30
    retries: int = 3
    retry_backoff_sec: float = 0.5


@dataclass
class HandasaSearchFilters:
    folder_id: Optional[str] = None
    request_num: Optional[str] = None
    address: Optional[str] = None
    partial_address: Optional[str] = None
    blocks_parcels: Optional[str] = None
    permit_num: Optional[str] = None
    online_req_num: Optional[str] = None
    building_id: Optional[str] = None
    document_type_in: Optional[List[str]] = None
    document_type_not_in: Optional[List[str]] = None
    doc_date_from: Optional[str] = None
    doc_date_to: Optional[str] = None
    file_extension_in: Optional[List[str]] = None
    publishable: Optional[bool] = None
    is_connected_doc: Optional[bool] = None
    sensitive_by_folder: Optional[bool] = None
    refinement_filters: Optional[List[str]] = None
    sort: Optional[List[Tuple[str, str]]] = None
    list_id: Optional[str] = None
    list_item_id: Optional[int] = None


class HandasaSearchClient:
    """Search client for the Handasa SharePoint search endpoint.

    The client can speak both the REST ``/_api/search/postquery`` interface and the
    CSOM ``ProcessQuery`` interface used by the public website.  The logic is
    intentionally contained in small helpers that can easily be unit tested and
    mocked.  ``search`` is the public entry point.
    """

    REST_ENDPOINT = "/_api/search/postquery"
    CSOM_ENDPOINT = "/_vti_bin/client.svc/ProcessQuery"

    def __init__(self, cfg: HandasaSearchConfig, session: Optional[requests.Session] = None):
        self.cfg = cfg
        self.session = session or requests.Session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def search(
        self,
        filters: HandasaSearchFilters,
        row_limit: int = 100,
        start_row: int = 0,
        all_pages: bool = True,
        select_properties: Optional[List[str]] = None,
        select_all_properties: bool = False,
        refiners: Optional[List[str]] = None,
        request_digest: Optional[str] = None,
        querytext_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        row_limit = max(1, min(row_limit, 500))
        querytext = querytext_override or self._build_kql(filters)
        refinement_filters = filters.refinement_filters or []
        select_props_rest = self._merge_select_properties(select_properties, select_all_properties, backend="rest")
        select_props_csom = self._merge_select_properties(select_properties, select_all_properties, backend="csom")
        effective_list_id = filters.list_id if filters.list_id is not None else self.cfg.list_id
        effective_list_item_id = (
            filters.list_item_id if filters.list_item_id is not None else self.cfg.list_item_id
        )

        total_rows: Optional[int] = None
        collected_items: List[Dict[str, Any]] = []
        refiners_payload: Optional[Any] = None

        current_start = max(0, start_row)
        while True:
            if self.cfg.use_rest:
                page = self._execute_rest_request(
                    querytext=querytext,
                    row_limit=row_limit,
                    start_row=current_start,
                    select_properties=select_props_rest,
                    refinement_filters=refinement_filters,
                    refiners=refiners,
                    sort=filters.sort,
                    list_id=effective_list_id,
                    list_item_id=effective_list_item_id,
                )
            else:
                page = self._execute_csom_request(
                    querytext=querytext,
                    row_limit=row_limit,
                    start_row=current_start,
                    select_properties=select_props_csom,
                    refinement_filters=refinement_filters,
                    refiners=refiners,
                    sort=filters.sort,
                    list_id=effective_list_id,
                    list_item_id=effective_list_item_id,
                    request_digest=request_digest,
                )

            total_rows = page.get("total_rows", total_rows)
            refiners_payload = page.get("refiners") or refiners_payload
            items = page.get("items", [])
            collected_items.extend(items)

            if not all_pages:
                break
            if len(items) < row_limit:
                break
            if total_rows is not None and current_start + row_limit >= total_rows:
                break

            current_start += row_limit
            self._sleep()

        result: Dict[str, Any] = {"total_rows": total_rows or len(collected_items), "items": collected_items}
        if refiners_payload is not None:
            result["refiners"] = refiners_payload
        return result

    # ------------------------------------------------------------------
    # Helpers: query construction
    # ------------------------------------------------------------------
    def _build_kql(self, filters: HandasaSearchFilters) -> str:
        clauses: List[str] = []

        def add_clause(expression: str) -> None:
            if expression:
                clauses.append(expression)

        if filters.folder_id:
            add_clause(self._kql_equals("TlvMPEngFolderId", filters.folder_id))
        if filters.request_num:
            add_clause(self._kql_equals("TlvMPEngRequestNum", filters.request_num))
        if filters.address:
            add_clause(self._kql_equals("TlvMPEngFolderStreetCodeHouseNumEntrance", filters.address))
        if filters.partial_address:
            add_clause(self._kql_equals("TlvMPEngFolderStreetCodeHouseNum", filters.partial_address))
        if filters.blocks_parcels:
            add_clause(self._kql_equals("TlvMPEngFolderBlocksParcels", filters.blocks_parcels))
        if filters.permit_num:
            add_clause(self._kql_equals("TlvMPEngPermitNum", filters.permit_num))
        if filters.online_req_num:
            add_clause(self._kql_equals("TlvMPEngOnlineReqNum", filters.online_req_num))
        if filters.building_id:
            add_clause(self._kql_equals("TlvMPEngBuildingID", filters.building_id))

        if filters.document_type_in:
            add_clause(self._kql_in("TlvMPEngDocumentType", filters.document_type_in))

        exclusions = filters.document_type_not_in
        if exclusions is None:
            exclusions = DEFAULT_DOCUMENT_TYPE_EXCLUSIONS
        if exclusions:
            add_clause(self._kql_not_in("TlvMPEngDocumentType", exclusions))

        if filters.doc_date_from or filters.doc_date_to:
            add_clause(self._kql_date_range("TlvMPEngDocDate", filters.doc_date_from, filters.doc_date_to))

        if filters.file_extension_in:
            add_clause(self._kql_in("FileExtension", filters.file_extension_in))

        publishable = filters.publishable
        if publishable is not None:
            add_clause(self._kql_bool("TlvMPEngPublishable", publishable))

        connected = filters.is_connected_doc
        if connected is None:
            connected = False
        add_clause(self._kql_bool("TlvMPEngIsConnectedDoc", connected))

        sensitive = filters.sensitive_by_folder
        if sensitive is None:
            sensitive = False
        add_clause(self._kql_bool("TlvMPEngSensitiveByFolderId", sensitive))

        return " ".join(filter(None, clauses)) or "*"

    @staticmethod
    def _kql_escape(value: str) -> str:
        return value.replace("\"", "\\\"")

    def _kql_equals(self, field: str, value: str) -> str:
        return f'{field}:"{self._kql_escape(value)}"'

    def _kql_bool(self, field: str, value: bool) -> str:
        return f"{field}:{str(value).lower()}"

    def _kql_in(self, field: str, values: Iterable[str]) -> str:
        sanitized = [self._kql_equals(field, str(v)) for v in values if v]
        if not sanitized:
            return ""
        if len(sanitized) == 1:
            return sanitized[0]
        return "(" + " OR ".join(sanitized) + ")"

    def _kql_not_in(self, field: str, values: Iterable[str]) -> str:
        sanitized = [f'-{field}:"{self._kql_escape(str(v))}"' for v in values if v]
        if not sanitized:
            return ""
        if len(sanitized) == 1:
            return sanitized[0]
        return "(" + " ".join(sanitized) + ")"

    def _kql_date_range(self, field: str, start: Optional[str], end: Optional[str]) -> str:
        clauses: List[str] = []
        if start:
            clauses.append(f"{field}>={start}T00:00:00Z")
        if end:
            clauses.append(f"{field}<={end}T23:59:59Z")
        return " ".join(clauses)

    # ------------------------------------------------------------------
    # Helpers: select properties
    # ------------------------------------------------------------------
    def _merge_select_properties(
        self,
        select_properties: Optional[List[str]],
        select_all: bool,
        *,
        backend: str,
    ) -> List[str]:
        ordered: List[str] = []

        def extend(values: Iterable[str]) -> None:
            for value in values:
                if value and value not in ordered:
                    ordered.append(value)

        if backend == "rest" and select_all:
            extend(["*"])

        extend(BASE_SELECT_PROPERTIES)

        if select_all:
            if backend == "csom":
                extend(CSOM_ALL_PROPERTIES_ALLOWLIST)

        if select_properties:
            extend(select_properties)

        return ordered

    # ------------------------------------------------------------------
    # Helpers: REST backend
    # ------------------------------------------------------------------
    def _execute_rest_request(
        self,
        *,
        querytext: str,
        row_limit: int,
        start_row: int,
        select_properties: List[str],
        refinement_filters: List[str],
        refiners: Optional[List[str]],
        sort: Optional[List[Tuple[str, str]]],
        list_id: Optional[str],
        list_item_id: Optional[int],
    ) -> Dict[str, Any]:
        payload = self._build_rest_payload(
            querytext=querytext,
            row_limit=row_limit,
            start_row=start_row,
            select_properties=select_properties,
            refinement_filters=refinement_filters,
            refiners=refiners,
            sort=sort,
            list_id=list_id,
            list_item_id=list_item_id,
        )
        url = self._build_url(self.REST_ENDPOINT)
        response = self._request_with_retries("post", url, json=payload, headers={"Accept": "application/json;odata=verbose"})
        data = response.json()
        return self._parse_rest_response(data)

    def _build_rest_payload(
        self,
        *,
        querytext: str,
        row_limit: int,
        start_row: int,
        select_properties: List[str],
        refinement_filters: List[str],
        refiners: Optional[List[str]],
        sort: Optional[List[Tuple[str, str]]],
        list_id: Optional[str],
        list_item_id: Optional[int],
    ) -> Dict[str, Any]:
        properties: List[Dict[str, Any]] = []
        if list_id:
            properties.append(
                {
                    "Key": "ListId",
                    "Value": {"StrVal": list_id, "Type": "String"},
                }
            )
        if list_item_id is not None:
            properties.append(
                {
                    "Key": "ListItemId",
                    "Value": {"IntVal": list_item_id, "Type": "Int32"},
                }
            )
        if self.cfg.client_type:
            properties.append(
                {
                    "Key": "ClientType",
                    "Value": {"StrVal": self.cfg.client_type, "Type": "String"},
                }
            )

        body: Dict[str, Any] = {
            "request": {
                "__metadata": {"type": "Microsoft.Office.Server.Search.REST.SearchRequest"},
                "Querytext": querytext,
                "RowLimit": row_limit,
                "StartRow": start_row,
                "SelectProperties": {"results": select_properties},
                "TrimDuplicates": False,
                "QueryTemplatePropertiesData": {
                    "QueryTemplatePropertiesResults": {
                        "results": [
                            {"Key": "Culture", "Value": {"IntVal": self.cfg.culture_lcid, "Type": "Int32"}},
                            {"Key": "TimeZoneId", "Value": {"IntVal": self.cfg.timezone_id, "Type": "Int32"}},
                        ]
                    }
                },
            }
        }

        if properties:
            body["request"]["Properties"] = {"results": properties}

        if refinement_filters:
            body["request"]["RefinementFilters"] = {"results": list(refinement_filters)}
        if refiners:
            body["request"]["Refiners"] = ",".join(refiners)
        if sort:
            body["request"]["SortList"] = {
                "results": [
                    {
                        "Property": field,
                        "Direction": 1 if direction.lower() == "desc" else 0,
                    }
                    for field, direction in sort
                ]
            }

        return body

    def _parse_rest_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        primary = payload.get("PrimaryQueryResult", {})
        relevant = primary.get("RelevantResults", {})
        table = relevant.get("Table", {})
        rows = table.get("Rows", [])

        items: List[Dict[str, Any]] = []
        for row in rows:
            cells = row.get("Cells", [])
            mapped = {cell.get("Key"): cell.get("Value") for cell in cells if cell.get("Key")}
            if mapped:
                items.append(mapped)

        refiners = None
        refinement_results = primary.get("RefinementResults")
        if isinstance(refinement_results, dict):
            refiners = refinement_results.get("Refiners")

        total_rows = relevant.get("TotalRows")
        return {"items": items, "total_rows": total_rows, "refiners": refiners}

    # ------------------------------------------------------------------
    # Helpers: CSOM backend
    # ------------------------------------------------------------------
    def _execute_csom_request(
        self,
        *,
        querytext: str,
        row_limit: int,
        start_row: int,
        select_properties: List[str],
        refinement_filters: List[str],
        refiners: Optional[List[str]],
        sort: Optional[List[Tuple[str, str]]],
        list_id: Optional[str],
        list_item_id: Optional[int],
        request_digest: Optional[str],
    ) -> Dict[str, Any]:
        payload = self._build_csom_payload(
            querytext=querytext,
            row_limit=row_limit,
            start_row=start_row,
            select_properties=select_properties,
            refinement_filters=refinement_filters,
            refiners=refiners,
            sort=sort,
            list_id=list_id,
            list_item_id=list_item_id,
        )
        url = self._build_url(self.CSOM_ENDPOINT)
        headers = {
            "Content-Type": "text/xml",
            "Accept": "application/json;odata=verbose",
            "X-Requested-With": "XMLHttpRequest",
        }
        if request_digest:
            headers["X-RequestDigest"] = request_digest
        response = self._request_with_retries("post", url, data=payload.encode("utf-8"), headers=headers)
        text = response.text
        return self._parse_csom_response(text)

    def _build_csom_payload(
        self,
        *,
        querytext: str,
        row_limit: int,
        start_row: int,
        select_properties: List[str],
        refinement_filters: List[str],
        refiners: Optional[List[str]],
        sort: Optional[List[Tuple[str, str]]],
        list_id: Optional[str],
        list_item_id: Optional[int],
    ) -> str:
        select_xml = "".join(
            f"<Object Type=\"String\">{self._kql_escape(prop)}</Object>" for prop in select_properties
        )
        refinement_filters_xml = "".join(
            f"<Object Type=\"String\">{self._kql_escape(ref)}</Object>" for ref in refinement_filters
        )
        refiners_xml = "".join(f"<Object Type=\"String\">{self._kql_escape(r)}</Object>" for r in refiners or [])

        sort_xml = "".join(
            """
            <Object Type="Microsoft.Office.Server.Search.REST.Sort" Id="{idx}">
                <Property Name="Direction" Type="Int32">{direction}</Property>
                <Property Name="Property" Type="String">{field}</Property>
            </Object>
            """.format(
                idx=idx,
                direction=1 if direction.lower() == "desc" else 0,
                field=self._kql_escape(field),
            )
            for idx, (field, direction) in enumerate(sort or [])
        )

        properties_xml_parts: List[str] = []
        if list_id:
            properties_xml_parts.append(
                """
                <Object Type="KeyValue">
                    <Property Name="Key" Type="String">ListId</Property>
                    <Property Name="Value" Type="String">{list_id}</Property>
                    <Property Name="ValueType" Type="String">Edm.String</Property>
                </Object>
                """.format(list_id=self._kql_escape(list_id))
            )
        if list_item_id is not None:
            properties_xml_parts.append(
                """
                <Object Type="KeyValue">
                    <Property Name="Key" Type="String">ListItemId</Property>
                    <Property Name="Value" Type="Int32">{list_item_id}</Property>
                    <Property Name="ValueType" Type="String">Edm.Int32</Property>
                </Object>
                """.format(list_item_id=list_item_id)
            )
        properties_xml = "".join(properties_xml_parts)

        payload = (
            f"<Request xmlns=\"http://schemas.microsoft.com/sharepoint/clientquery/2009\" "
            f"SchemaVersion=\"15.0.0.0\" LibraryVersion=\"16.0.0.0\" ApplicationName=\"HandasaSearchClient\">\n"
            f"  <Actions>\n"
            f"    <ObjectPath Id=\"1\" ObjectPathId=\"0\" />\n"
            f"    <SetProperty Id=\"2\" ObjectPathId=\"0\" Name=\"TimeZoneId\">"
            f"<Parameter Type=\"Number\">{self.cfg.timezone_id}</Parameter></SetProperty>\n"
            f"    <SetProperty Id=\"3\" ObjectPathId=\"0\" Name=\"QueryText\">"
            f"<Parameter Type=\"String\">{self._kql_escape(querytext)}</Parameter></SetProperty>\n"
            f"    <SetProperty Id=\"4\" ObjectPathId=\"0\" Name=\"RowLimit\">"
            f"<Parameter Type=\"Number\">{row_limit}</Parameter></SetProperty>\n"
            f"    <SetProperty Id=\"5\" ObjectPathId=\"0\" Name=\"StartRow\">"
            f"<Parameter Type=\"Number\">{start_row}</Parameter></SetProperty>\n"
            f"    <SetProperty Id=\"6\" ObjectPathId=\"0\" Name=\"Culture\">"
            f"<Parameter Type=\"Number\">{self.cfg.culture_lcid}</Parameter></SetProperty>\n"
            f"    <SetProperty Id=\"7\" ObjectPathId=\"0\" Name=\"SelectProperties\">\n"
            f"      <Parameter Type=\"Array\">{select_xml}</Parameter>\n"
            f"    </SetProperty>\n"
            f"    <SetProperty Id=\"8\" ObjectPathId=\"0\" Name=\"RefinementFilters\">\n"
            f"      <Parameter Type=\"Array\">{refinement_filters_xml}</Parameter>\n"
            f"    </SetProperty>\n"
            f"    <SetProperty Id=\"9\" ObjectPathId=\"0\" Name=\"Refiners\">\n"
            f"      <Parameter Type=\"Array\">{refiners_xml}</Parameter>\n"
            f"    </SetProperty>\n"
            f"    <SetProperty Id=\"10\" ObjectPathId=\"0\" Name=\"SortList\">\n"
            f"      <Parameter Type=\"Array\">{sort_xml}</Parameter>\n"
            f"    </SetProperty>\n"
            f"    <SetProperty Id=\"11\" ObjectPathId=\"0\" Name=\"Properties\">\n"
            f"      <Parameter Type=\"Array\">{properties_xml}</Parameter>\n"
            f"    </SetProperty>\n"
            f"  </Actions>\n"
            f"  <ObjectPaths>\n"
            f"    <Constructor Id=\"0\" TypeId=\"{{d36b0f7b-8df2-47eb-a4fb-4ef2c5c2fefe}}\" />\n"
            f"  </ObjectPaths>\n"
            f"</Request>"
        )
        return payload

    def _parse_csom_response(self, payload: str) -> Dict[str, Any]:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return {"items": [], "total_rows": 0, "refiners": None}

        primary: Optional[Dict[str, Any]] = None
        for entry in data:
            if isinstance(entry, dict) and "PrimaryQueryResult" in entry:
                primary = entry.get("PrimaryQueryResult")
                break

        if not primary:
            return {"items": [], "total_rows": 0, "refiners": None}

        relevant = primary.get("RelevantResults", {})
        table = relevant.get("Table", {})
        rows = table.get("Rows", [])

        items: List[Dict[str, Any]] = []
        for row in rows:
            cells = row.get("Cells", [])
            mapped = {cell.get("Key"): cell.get("Value") for cell in cells if cell.get("Key")}
            if mapped:
                items.append(mapped)

        refiners = None
        refinement_results = primary.get("RefinementResults")
        if isinstance(refinement_results, dict):
            refiners = refinement_results.get("Refiners")

        total_rows = relevant.get("TotalRows")
        return {"items": items, "total_rows": total_rows, "refiners": refiners}

    # ------------------------------------------------------------------
    # Helpers: stock KQL snippets
    # ------------------------------------------------------------------
    def build_archive_kql(self, block_param: str) -> str:
        block_clause = self._kql_equals("TlvMPEngFolderBlocksParcels", block_param)
        defaults = [
            block_clause,
            self._kql_bool("TlvMPEngIsConnectedDoc", False),
            self._kql_bool("TlvMPEngSensitiveByFolderId", False),
            self._kql_not_in("TlvMPEngDocumentType", DEFAULT_DOCUMENT_TYPE_EXCLUSIONS),
        ]
        publishable = [
            block_clause,
            self._kql_bool("TlvMPEngIsConnectedDoc", False),
            self._kql_bool("TlvMPEngPublishable", True),
        ]
        defaults_clause = " ".join(filter(None, defaults))
        publishable_clause = " ".join(filter(None, publishable))
        return f"({defaults_clause}) OR ({publishable_clause})"

    # ------------------------------------------------------------------
    # Helpers: transport
    # ------------------------------------------------------------------
    def _request_with_retries(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        attempts = self.cfg.retries + 1
        delay = self.cfg.retry_backoff_sec
        last_exc: Optional[Exception] = None
        for attempt in range(1, attempts + 1):
            try:
                response = self.session.request(method, url, timeout=self.cfg.timeout_sec, **kwargs)
                response.raise_for_status()
                return response
            except requests.RequestException as exc:  # pragma: no cover - network failures are hard to simulate deterministically
                last_exc = exc
                if attempt >= attempts:
                    raise
                sleep_for = delay * (2 ** (attempt - 1))
                jitter = random.uniform(0, delay)
                self._sleep(sleep_for + jitter)
        if last_exc:
            raise last_exc
        raise RuntimeError("Unexpected retry handling state")

    def _build_url(self, path: str) -> str:
        base = self.cfg.base_url.rstrip("/")
        return f"{base}{path}"

    def _sleep(self, duration: Optional[float] = None) -> None:
        if duration is None:
            duration = random.uniform(0.2, 0.4)
        time.sleep(duration)


def _normalize_label(value: Optional[str]) -> str:
    if not value:
        return ""
    text = str(value).replace("\xa0", " ").replace("\u200f", "").strip()
    text = re.sub(r"[()\[\],/]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


_HANDASA_EXACT_TYPE_MAP = {
    _normalize_label("היתר מילולי חתום"): "permit",
    _normalize_label("היתר-תכנית חתומה"): "permit",
    _normalize_label("היתר תכנית חתומה"): "permit",
    _normalize_label("היתר מילולי"): "permit",
    _normalize_label("תשריט בית משותף"): "condo_plan",
    _normalize_label("מפת מדידה להיתר"): "technical_drawing",
    _normalize_label("תשריט בית משותף (עדכני)"): "condo_plan",
}

_HANDASA_KEYWORD_RULES: List[Tuple[Tuple[str, ...], str]] = [
    (("היתר", "חת"), "permit"),
    (("היתר", "מילול"), "permit"),
    (("תשריט",), "condo_plan"),
    (("מפת", "מדידה"), "technical_drawing"),
    (("תכנית", "אדריכ"), "architectural_drawing"),
    (("תכנית", "סניטרית"), "technical_drawing"),
    (("תכנית", "חשמל"), "technical_drawing"),
    (("תכנית", "חניה"), "architectural_drawing"),
]

_PERMIT_DOCUMENT_TYPES = {"permit", "permit_construction", "permit_renovation"}


def _classify_handasa_document(row: Dict[str, Any]) -> Tuple[str, str]:
    descriptor_candidates = [
        row.get("TlvMPEngDocumentType"),
        row.get("TlvMPEngDocumentName"),
        row.get("ContentType"),
        row.get("Title"),
    ]
    descriptor = next(
        (value for value in descriptor_candidates if isinstance(value, str) and value.strip()),
        "",
    )
    normalized = _normalize_label(descriptor)
    if normalized in _HANDASA_EXACT_TYPE_MAP:
        doc_type = _HANDASA_EXACT_TYPE_MAP[normalized]
    else:
        doc_type = "other"
        for keywords, candidate_type in _HANDASA_KEYWORD_RULES:
            if all(keyword in normalized for keyword in keywords):
                doc_type = candidate_type
                break

    category = "permit" if doc_type in _PERMIT_DOCUMENT_TYPES else "document"
    if doc_type == "plan":
        category = "plan"
    elif doc_type in {"condo_plan", "architectural_drawing", "technical_drawing", "blueprint"}:
        category = "drawing"

    return doc_type, category


def _normalize_unique_id(unique_id: Optional[str]) -> Optional[str]:
    if not unique_id:
        return None
    unique_id = unique_id.strip()
    if unique_id.startswith("{") and unique_id.endswith("}"):
        return unique_id[1:-1]
    return unique_id


def _parse_sharepoint_date(value: Any) -> Optional[str]:
    """Convert SharePoint style date values to ISO formatted strings."""

    if not value:
        return None

    # /Date(1698451200000)/ format (milliseconds from epoch)
    if isinstance(value, str) and value.startswith("/Date(") and value.endswith(")/"):
        try:
            timestamp_ms = int(value[6:-2])
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc)
            return dt.date().isoformat()
        except ValueError:
            return None

    # ISO formatted string
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return dt.date().isoformat()
        except ValueError:
            return None

    # Raw unix timestamp (seconds or milliseconds)
    if isinstance(value, (int, float)):
        timestamp = value / 1000 if value > 1e12 else value
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.date().isoformat()

    return None


class HandasaClient:
    """Client for the Tel-Aviv Handasa (engineering) portal."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        *,
        timeout: float = 60.0,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        self.session = session or requests.Session()
        self.timeout = timeout
        # Ensure we have a reasonable default user-agent to avoid being blocked
        self.session.headers.setdefault("User-Agent", user_agent)
        base_url = SEARCH_RESULTS_URL.split("/Pages", 1)[0]
        cfg = HandasaSearchConfig(
            base_url=base_url,
            use_rest=False,
            timeout_sec=timeout,
            retries=3,
            retry_backoff_sec=0.5,
        )
        self.search_client = HandasaSearchClient(cfg, session=self.session)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_archive(self, block: str, parcel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all building archive for a given block/parcel combination."""

        block_param = self._format_block_parcel(block, parcel)
        digest = self._get_request_digest(block_param)
        querytext = self.search_client.build_archive_kql(block_param)
        search_result = self.search_client.search(
            HandasaSearchFilters(),
            row_limit=50,
            all_pages=True,
            request_digest=digest,
            querytext_override=querytext,
        )
        items = search_result.get("items", [])
        return [self._normalize_row(row) for row in items if row]

    def search_documents(
        self,
        filters: HandasaSearchFilters,
        *,
        row_limit: int = 100,
        start_row: int = 0,
        all_pages: bool = True,
        select_properties: Optional[List[str]] = None,
        select_all_properties: bool = False,
        refiners: Optional[List[str]] = None,
        request_digest: Optional[str] = None,
        querytext_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute a Handasa SharePoint search with the dynamic payload builder."""

        digest = request_digest or self._get_context_request_digest()
        if not digest:
            raise RuntimeError("Failed to obtain request digest for Handasa search")

        return self.search_client.search(
            filters,
            row_limit=row_limit,
            start_row=start_row,
            all_pages=all_pages,
            select_properties=select_properties,
            select_all_properties=select_all_properties,
            refiners=refiners,
            request_digest=digest,
            querytext_override=querytext_override,
        )

    def download_document(
        self,
        unique_id: str,
        save_to: Optional[Union[str, Path]] = None,
        overwrite: bool = False,
    ) -> Dict[str, Any]:
        """Download a permit document by its unique SharePoint ID.

        Args:
            unique_id: SharePoint unique identifier (GUID with or without braces).
            save_to: Optional destination path or directory for the decoded file.
            overwrite: When saving, control whether to overwrite an existing file.
        """

        unique_id = _normalize_unique_id(unique_id) or ""
        response = self.session.get(
            FILES_API_URL,
            params={"id": unique_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, str):  # Some endpoints double-encode JSON
            payload = loads(payload)

        buffer = payload.get("buffer", "")
        try:
            content = base64.b64decode(buffer) if buffer else b""
        except Exception:  # pragma: no cover - invalid base64 shouldn't fail client
            logger.warning("Failed to decode permit %s buffer", unique_id)
            content = b""

        result = {
            "file_name": payload.get("fileName"),
            "content_type": payload.get("contentType", "application/octet-stream"),
            "content": content,
            "size": len(content),
            "raw": payload,
        }

        if save_to and content:
            target_path = Path(save_to)
            save_to_str = str(save_to)
            if target_path.exists() and target_path.is_dir():
                is_directory = True
            else:
                is_directory = save_to_str.endswith(("/", "\\")) or target_path.suffix == ""

            if is_directory:
                file_name = result["file_name"] or f"{unique_id or 'document'}.bin"
                target_path = target_path / file_name

            if target_path.exists() and not overwrite:
                raise FileExistsError(f"File already exists: {target_path}")

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with target_path.open("wb") as handle:
                handle.write(content)
            result["file_path"] = target_path

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _format_block_parcel(self, block: str, parcel: Optional[str]) -> str:
        block_str = str(block or "").strip()
        parcel_str = str(parcel or "").strip()
        if not block_str:
            raise ValueError("HandasaClient requires a block number")
        if parcel_str:
            return f"{block_str}_{parcel_str}"
        return block_str

    def _get_request_digest(self, block_param: str) -> str:
        digest = self._get_context_request_digest()
        if not digest:
            try:
                digest = self._fetch_request_digest_from_page(block_param)
            except requests.RequestException as exc:
                logger.warning("Handasa digest fetch via search page failed: %s", exc)

        if not digest:
            raise RuntimeError("Failed to obtain request digest from Handasa portal")

        return digest

    def _get_context_request_digest(self) -> Optional[str]:
        try:
            response = self.session.post(
                CONTEXT_INFO_URL,
                headers={"Accept": "application/json;odata=verbose"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            if isinstance(data, str):
                data = loads(data)
            digest = (
                data.get("d", {})
                .get("GetContextWebInformation", {})
                .get("FormDigestValue")
            )
            if isinstance(digest, str) and digest.strip():
                return digest
        except requests.RequestException as exc:
            logger.debug("Handasa contextinfo digest fetch failed: %s", exc)
        except ValueError:
            logger.debug("Handasa contextinfo digest JSON parse failed")
        return None

    def _fetch_request_digest_from_page(self, block_param: str) -> Optional[str]:
        response = self.session.get(
            SEARCH_RESULTS_URL,
            params={"block": block_param},
            headers={
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,image/apng,*/*;q=0.8"
                ),
                "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        match = _DIGEST_PATTERN.search(response.text)
        if match:
            return match.group(1)
        logger.debug("Handasa digest not found in search page response")
        return None

    def _normalize_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        unique_id = _normalize_unique_id(row.get("UniqueID"))
        permission_num = row.get("TlvMPEngPermitNum") or row.get("PermitNumber")
        request_num = row.get("TlvMPEngOnlineReqNum") or row.get("TlvMPEngRequestNum")
        document_date = (
            _parse_sharepoint_date(row.get("TlvMPEngIssueDate"))
            or _parse_sharepoint_date(row.get("IssueDate"))
            or _parse_sharepoint_date(row.get("Write"))
            or _parse_sharepoint_date(row.get("TlvMPEngDocDate"))
        )
        status = row.get("TlvMPEngProcessStage") or row.get("TlvMPEngDocumentStatus") or ""
        external_id = unique_id or permission_num or request_num or row.get("Path")
        external_url = row.get('DocumentLink') or self._build_external_url(unique_id, row)
        preview_url = "https://handasa.tel-aviv.gov.il" + row.get("TlvMPEngWebsioPreview") if row.get("TlvMPEngWebsioPreview") else None

        normalized = {
            "title": row.get('TlvMPEngDocumentType'),
            "status": status,
            "permission_num": permission_num,
            "request_num": request_num,
            "external_id": external_id,
            "external_url": external_url,
            "document_date": document_date,
            "preview_url": preview_url,
            "source": "Handasa",
            "meta": row,
        }

        # Carry additional numeric metrics if provided by the API
        for key in (
            "TlvMPEngHousingUnits",
            "TlvMPEngCommercialArea",
            "TlvMPEngResidentialArea",
            "TlvMPEngResidentialUnits",
        ):
            if key in row:
                normalized[key] = row.get(key)

        document_type, document_category = _classify_handasa_document(row)
        normalized["document_type"] = document_type
        normalized["document_category"] = document_category

        return normalized

    def _build_external_url(self, unique_id: Optional[str], row: Dict[str, Any]) -> str:
        if unique_id:
            return f"{FILES_API_URL}?id={unique_id}"
        return row.get("Path", "")


__all__ = [
    "HandasaClient",
    "HandasaSearchClient",
    "HandasaSearchConfig",
    "HandasaSearchFilters",
    "BASE_SELECT_PROPERTIES",
    "CSOM_ALL_PROPERTIES_ALLOWLIST",
]

if __name__ == "__main__":
    client = HandasaClient()
    archive = client.get_archive("6952", "127")
    print(archive)
