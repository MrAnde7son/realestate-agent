from __future__ import annotations

import base64
import logging
import re
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

# Large CSOM payload used by the public Handasa search form.  Keeping it in a
# separate template file keeps this module readable.
PROCESS_QUERY_TEMPLATE = Path(__file__).with_name("payload_template.xml").read_text(encoding="utf-8")

_DIGEST_PATTERN = re.compile(r'"formDigestValue"\s*:\s*"([^"]+)"')
_BLOCK_PLACEHOLDER = "__BLOCK_PARAM__"
_START_ROW_PLACEHOLDER = "__START_ROW__"


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
            page_size: int = 50,
    ) -> List[Dict[str, Any]]:
        block_param = self._format_block_parcel(block, parcel)
        digest = self._get_request_digest(block_param)

        start_row = 0
        all_rows: List[Dict[str, Any]] = []
        seen_ids: set[str] = set()

        while True:
            payload = self._build_payload(block_param, start_row=start_row)
            resp = self.session.post(
                PROCESS_QUERY_URL,
                data=payload.encode("utf-8"),
                headers={
                    "Content-Type": "text/xml",
                    "X-Requested-With": "XMLHttpRequest",
                    "X-RequestDigest": digest,
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = loads(resp.content.decode("utf-8"))

            # Extract rows + page meta
            batch_rows, total_rows = self._extract_rows_and_total(data)

            # Normalize + de-dupe
            normalized_batch: List[Dict[str, Any]] = []
            for r in batch_rows:
                n = self._normalize_row(r)
                ext_id = n.get("external_id") or n.get("preview_url") or n.get("external_url")
                if ext_id and ext_id in seen_ids:
                    continue
                if ext_id:
                    seen_ids.add(ext_id)
                normalized_batch.append(n)

            all_rows.extend(normalized_batch)

            # Stop when we’ve reached or exceeded total, or when the batch is short/empty
            if not batch_rows:
                break
            start_row += page_size
            if total_rows is not None and start_row >= total_rows:
                break

        return all_rows

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
    @staticmethod
    def _format_block_parcel(block: str, parcel: Optional[str]) -> str:
        block_str = str(block or "").strip()
        parcel_str = str(parcel or "").strip()
        if not block_str:
            raise ValueError("HandasaClient requires a block number")
        if parcel_str:
            return f"{block_str}_{parcel_str}"
        return block_str

    def _get_request_digest(self, block_param: str) -> str:
        digest = None
        for i in range(3):
            try:
                digest = self._fetch_request_digest_from_page(block_param)
            except requests.RequestException as exc:
                logger.warning("Handasa digest fetch via search page failed: %s", exc)
            if digest:
                break
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
        logger.debug("Handasa digest not found in search page response")
        return None

    @staticmethod
    def _build_payload(block_param: str, start_row: int = 0) -> str:
        tmpl = PROCESS_QUERY_TEMPLATE
        if _BLOCK_PLACEHOLDER not in tmpl:
            logger.debug("Handasa payload template missing block placeholder")
        if _START_ROW_PLACEHOLDER not in tmpl:
            logger.debug("Handasa payload template missing start-row placeholder")
        return (
            tmpl
            .replace(_BLOCK_PLACEHOLDER, block_param)
            .replace(_START_ROW_PLACEHOLDER, str(start_row))
        )

    @staticmethod
    def _extract_rows_and_total(payload: Iterable[Any]) -> tuple[List[Dict[str, Any]], Optional[int]]:
        rows: List[Dict[str, Any]] = []
        total: Optional[int] = None
        for entry in payload:
            if isinstance(entry, dict):
                for value in entry.values():
                    if isinstance(value, dict) and value.get("ResultTables"):
                        for table in value.get("ResultTables", []):
                            if table.get("TableType") == "RelevantResults":
                                if isinstance(table.get("ResultRows"), list):
                                    rows.extend(table["ResultRows"])
                                # SharePoint Search returns TotalRows (and TotalRowsIncludingDuplicates)
                                if "TotalRows" in table and isinstance(table["TotalRows"], int):
                                    total = table["TotalRows"]
        return rows, total


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

    @staticmethod
    def _build_external_url(unique_id: Optional[str], row: Dict[str, Any]) -> str:
        if unique_id:
            return f"{FILES_API_URL}?id={unique_id}"
        return row.get("Path", "")


__all__ = ["HandasaClient"]

if __name__ == "__main__":
    client = HandasaClient()
    archive = client.get_archive("6952", "127")
    print(archive)
