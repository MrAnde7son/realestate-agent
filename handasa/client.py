from __future__ import annotations

import base64
import logging
import re
from datetime import datetime, timezone
from json import loads
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

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
    def get_archive(self, block: str, parcel: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all building archive for a given block/parcel combination."""

        block_param = self._format_block_parcel(block, parcel)
        digest = self._get_request_digest(block_param)
        payload = self._build_payload(block_param)
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
        rows = self._extract_rows(data)
        return [self._normalize_row(row) for row in rows if row]

    def download_document(
        self,
        unique_id: str,
        save_to: Optional[Union[str, Path]] = "permits",
        overwrite: bool = True,
    ) -> Dict[str, Any]:
        """Download a permit document by its unique SharePoint ID.

        Args:
            unique_id: SharePoint unique identifier (GUID with or without braces).
            save_to: Optional destination directory for the decoded file.
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

            file_name = result["file_name"] or f"{unique_id}.pdf"
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
        logger.debug("Handasa digest not found in search page response")
        return None

    def _build_payload(self, block_param: str) -> str:
        if _BLOCK_PLACEHOLDER not in PROCESS_QUERY_TEMPLATE:
            logger.debug("Handasa payload template missing placeholder; refreshing cache")
        return PROCESS_QUERY_TEMPLATE.replace(_BLOCK_PLACEHOLDER, block_param)

    def _extract_rows(self, payload: Iterable[Any]) -> List[Dict[str, Any]]:
        rows = []
        for entry in payload:
            if isinstance(entry, dict):
                for value in entry.values():
                    if isinstance(value, dict) and value.get("ResultTables"):
                        tables = value.get("ResultTables", [])
                        for table in tables:
                            result_rows = table.get("ResultRows")
                            if isinstance(result_rows, list):
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

        return normalized

    def _build_external_url(self, unique_id: Optional[str], row: Dict[str, Any]) -> str:
        if unique_id:
            return f"{FILES_API_URL}?id={unique_id}"
        return row.get("Path", "")


__all__ = ["HandasaClient"]

if __name__ == "__main__":
    client = HandasaClient()
    archive = client.get_archive("6952", "127")
    for doc in archive:
        if doc['external_url'].endswith('pdf'):
            print(doc)
