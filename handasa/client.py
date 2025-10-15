from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timezone
from json import loads
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

import xml.etree.ElementTree as ET

import requests

logger = logging.getLogger(__name__)

SEARCH_RESULTS_URL = "https://handasa.tel-aviv.gov.il/Pages/SearchResultsAnonPageNew.aspx"
PROCESS_QUERY_URL = "https://handasa.tel-aviv.gov.il/_vti_bin/client.svc/ProcessQuery"
FILES_API_URL = "https://handasa.tel-aviv.gov.il/api/files"
CONTEXT_INFO_URL = "https://handasa.tel-aviv.gov.il/_api/contextinfo"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

# Large CSOM payload used by the public Handasa search form.  Keeping it in a
# separate template file keeps this module readable.
PROCESS_QUERY_TEMPLATE = Path(__file__).with_name("payload_template.xml").read_text(encoding="utf-8")

_SP_NAMESPACE = "http://schemas.microsoft.com/sharepoint/clientquery/2009"
_SP = f"{{{_SP_NAMESPACE}}}"
ET.register_namespace("", _SP_NAMESPACE)

_DIGEST_PATTERN = re.compile(r'"formDigestValue"\s*:\s*"([^"]+)"')
_INPUT_DIGEST_PATTERN = re.compile(r'id="__REQUESTDIGEST"[^>]*value="([^"]+)"')
_BLOCK_PLACEHOLDER = "__BLOCK_PARAM__"


def _extract_default_select_properties() -> Tuple[str, ...]:
    template = PROCESS_QUERY_TEMPLATE.replace(_BLOCK_PLACEHOLDER, "0")
    root = ET.fromstring(template)
    ns = {"sp": _SP_NAMESPACE}
    values: List[str] = []
    for method in root.findall("sp:Actions/sp:Method[@ObjectPathId='17']", ns):
        for param in method.findall("sp:Parameters/sp:Parameter", ns):
            if param.text:
                values.append(param.text.strip())
    return tuple(values)


_DEFAULT_SELECT_PROPERTIES = _extract_default_select_properties()
_QUERY_TEMPLATE_MARKER = "TlvMPEngPublishable:true"


def _next_action_id(actions: ET.Element) -> int:
    max_id = 0
    for element in actions:
        identifier = element.attrib.get("Id")
        if identifier and identifier.isdigit():
            max_id = max(max_id, int(identifier))
    return max_id + 1


def _set_number_property(root: ET.Element, name: str, value: int) -> None:
    ns = {"sp": _SP_NAMESPACE}
    parameter = root.find(f"sp:Actions/sp:SetProperty[@Name='{name}']/sp:Parameter", ns)
    if parameter is not None:
        parameter.text = str(int(value))


def _create_query_property_method(actions: ET.Element, name: str) -> ET.Element:
    method = ET.SubElement(
        actions,
        f"{_SP}Method",
        {"Name": "SetQueryPropertyValue", "Id": str(_next_action_id(actions)), "ObjectPathId": "12"},
    )
    params = ET.SubElement(method, f"{_SP}Parameters")
    param_name = ET.SubElement(params, f"{_SP}Parameter", {"Type": "String"})
    param_name.text = name
    value_param = ET.SubElement(
        params,
        f"{_SP}Parameter",
        {"TypeId": "{b25ba502-71d7-4ae4-a701-4ca2fb1223be}"},
    )

    defaults = (
        ("BoolVal", "Boolean", "false"),
        ("IntVal", "Number", "0"),
        ("QueryPropertyValueTypeIndex", "Number", "1"),
        ("StrArray", "Null", None),
        ("StrVal", "Null", None),
    )
    for prop_name, prop_type, text in defaults:
        prop = ET.SubElement(value_param, f"{_SP}Property", {"Name": prop_name, "Type": prop_type})
        if text is not None:
            prop.text = text

    return method


def _set_query_property_value(
    root: ET.Element,
    name: str,
    *,
    int_value: Optional[int] = None,
    str_value: Optional[str] = None,
) -> None:
    actions = root.find(f"{_SP}Actions")
    if actions is None:
        return

    ns = {"sp": _SP_NAMESPACE}
    target: Optional[ET.Element] = None
    for method in actions.findall("sp:Method", ns):
        if method.attrib.get("Name") != "SetQueryPropertyValue":
            continue
        params = method.findall("sp:Parameters/sp:Parameter", ns)
        if params and params[0].text == name:
            target = method
            break

    if target is None:
        target = _create_query_property_method(actions, name)

    params = target.findall(f"{_SP}Parameters/{_SP}Parameter")
    if len(params) < 2:
        return

    value_param = params[1]
    properties = {prop.attrib.get("Name"): prop for prop in value_param.findall(f"{_SP}Property")}

    bool_prop = properties.get("BoolVal")
    if bool_prop is not None:
        bool_prop.text = "false"

    str_array_prop = properties.get("StrArray")
    if str_array_prop is not None:
        str_array_prop.attrib["Type"] = "Null"
        str_array_prop.text = None

    if int_value is not None:
        int_prop = properties.get("IntVal")
        if int_prop is not None:
            int_prop.attrib["Type"] = "Number"
            int_prop.text = str(int(int_value))
        qpvt = properties.get("QueryPropertyValueTypeIndex")
        if qpvt is not None:
            qpvt.text = "2"
        str_prop = properties.get("StrVal")
        if str_prop is not None:
            str_prop.attrib["Type"] = "Null"
            str_prop.text = None

    if str_value is not None:
        str_prop = properties.get("StrVal")
        if str_prop is not None:
            str_prop.attrib["Type"] = "String"
            str_prop.text = str(str_value)
        qpvt = properties.get("QueryPropertyValueTypeIndex")
        if qpvt is not None:
            qpvt.text = "1"
        int_prop = properties.get("IntVal")
        if int_prop is not None:
            int_prop.attrib["Type"] = "Number"
            int_prop.text = "0"


def _set_select_properties(root: ET.Element, properties: Iterable[str]) -> None:
    actions = root.find(f"{_SP}Actions")
    if actions is None:
        return

    ns = {"sp": _SP_NAMESPACE}
    for method in list(actions.findall("sp:Method[@ObjectPathId='17']", ns)):
        actions.remove(method)

    next_id = _next_action_id(actions)
    for value in properties:
        value_str = str(value).strip()
        if not value_str:
            continue
        method = ET.SubElement(
            actions,
            f"{_SP}Method",
            {"Name": "Add", "Id": str(next_id), "ObjectPathId": "17"},
        )
        next_id += 1
        params = ET.SubElement(method, f"{_SP}Parameters")
        param = ET.SubElement(params, f"{_SP}Parameter", {"Type": "String"})
        param.text = value_str


def _apply_document_type_filters(root: ET.Element, document_types: Optional[Iterable[str]]) -> None:
    if not document_types:
        return

    types: List[str] = []
    for doc in document_types:
        if doc is None:
            continue
        doc_str = str(doc).strip()
        if doc_str:
            types.append(doc_str)
    if not types:
        return

    ns = {"sp": _SP_NAMESPACE}
    parameter = root.find("sp:Actions/sp:SetProperty[@Name='QueryTemplate']/sp:Parameter", ns)
    if parameter is None or parameter.text is None:
        return

    clause = " AND (" + " OR ".join(f'TlvMPEngDocumentType:"{doc}"' for doc in types) + ")"
    text = parameter.text
    if _QUERY_TEMPLATE_MARKER in text:
        text = text.replace(_QUERY_TEMPLATE_MARKER, _QUERY_TEMPLATE_MARKER + clause, 1)
    else:
        text = f"{text}{clause}"
    parameter.text = text


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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_archive(
        self,
        block: str,
        parcel: Optional[str] = None,
        *,
        select_properties: Optional[Iterable[str]] = None,
        document_types: Optional[Iterable[str]] = None,
        page_size: int = 50,
        start_row: int = 0,
        max_pages: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch building archive results for a given block/parcel combination.

        Args:
            block: Block ("gush") identifier.
            parcel: Optional parcel ("helka") identifier.
            select_properties: Optional iterable of SharePoint managed property
                names to include in the search response.
            document_types: Optional iterable of document type names to filter.
            page_size: Number of results to request per page.
            start_row: Initial search result offset.
            max_pages: Optional cap on the number of result pages to fetch.
        """

        if page_size <= 0:
            raise ValueError("HandasaClient page_size must be a positive integer")
        if start_row < 0:
            raise ValueError("HandasaClient start_row must not be negative")

        block_param = self._format_block_parcel(block, parcel)
        digest = self._get_request_digest(block_param)

        rows: List[Dict[str, Any]] = []
        current_start = start_row
        pages_fetched = 0

        while True:
            payload = self._build_payload(
                block_param,
                select_properties=select_properties,
                document_types=document_types,
                row_limit=page_size,
                start_row=current_start,
            )
            response = self.session.post(
                PROCESS_QUERY_URL,
                data=payload.encode("utf-8"),
                headers={
                    "Content-Type": "text/xml",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-RequestDigest": digest,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = loads(response.content.decode("utf-8"))
            page_rows = self._extract_rows(data)
            if not page_rows:
                break

            rows.extend(page_rows)
            pages_fetched += 1

            if len(page_rows) < page_size:
                break

            current_start += len(page_rows)

            if max_pages is not None and pages_fetched >= max_pages:
                break

        return [self._normalize_row(row) for row in rows if row]

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
        digest = None
        try:
            digest = self._fetch_request_digest_from_page(block_param)
        except requests.RequestException as exc:
            logger.warning("Handasa digest fetch via search page failed: %s", exc)

        if not digest:
            raise RuntimeError("Failed to obtain request digest from Handasa portal")

        return digest

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

        match = _INPUT_DIGEST_PATTERN.search(response.text)
        if match:
            return match.group(1)

        logger.debug("Handasa digest not found in search page response")
        return None

    def _build_payload(
        self,
        block_param: str,
        *,
        select_properties: Optional[Iterable[str]] = None,
        document_types: Optional[Iterable[str]] = None,
        start_row: int = 0,
        row_limit: int = 50,
    ) -> str:
        if _BLOCK_PLACEHOLDER not in PROCESS_QUERY_TEMPLATE:
            logger.debug("Handasa payload template missing placeholder; refreshing cache")

        template = PROCESS_QUERY_TEMPLATE.replace(_BLOCK_PLACEHOLDER, block_param)
        root = ET.fromstring(template)

        _set_number_property(root, "RowsPerPage", row_limit)
        _set_number_property(root, "RowLimit", row_limit)
        _set_query_property_value(root, "StartRow", int_value=start_row)

        properties = tuple(prop for prop in (select_properties or _DEFAULT_SELECT_PROPERTIES) if prop)
        if not properties:
            properties = _DEFAULT_SELECT_PROPERTIES
        _set_select_properties(root, properties)

        _apply_document_type_filters(root, document_types)

        return ET.tostring(root, encoding="utf-8").decode("utf-8")

    def _extract_rows(self, payload: Iterable[Any]) -> List[Dict[str, Any]]:
        rows = []
        for entry in payload:
            if isinstance(entry, dict):
                for value in entry.values():
                    if isinstance(value, dict) and value.get("ResultTables"):
                        tables = value.get("ResultTables", [])
                        for table in tables:
                            result_rows = table.get("ResultRows")
                            if isinstance(result_rows, list) and table.get("TableType") == 'RelevantResults':
                                rows.extend(result_rows)
        return rows

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


__all__ = ["HandasaClient"]

if __name__ == "__main__":
    client = HandasaClient()
    archive = client.get_archive("6952", "127")
    print(archive)
