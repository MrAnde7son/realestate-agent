"""Collector that enriches GIS permits with data from the Handasa portal."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from handasa.scraper import HandasaScraper, HandasaScraperError

from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class HandasaCollector(BaseCollector):
    """Collect building permits directly from the Handasa website."""

    def __init__(self, scraper: Optional[HandasaScraper] = None) -> None:
        self._scraper: Optional[HandasaScraper] = scraper

    def collect(self, *, block: str, parcel: str) -> List[Dict[str, Any]]:
        """Return permits for the supplied block/parcel."""

        if not block or not parcel:
            raise ValueError("HandasaCollector requires block and parcel numbers")

        logger.info("Fetching Handasa permits", extra={"block": block, "parcel": parcel})
        try:
            documents = self._get_scraper().fetch_documents(block, parcel)
        except HandasaScraperError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise HandasaScraperError(str(exc)) from exc

        permits: List[Dict[str, Any]] = []
        seen: Set[str] = set()
        for document in documents:
            permit = self._document_to_permit(document, block, parcel)
            identifier_raw = (
                permit.get("permission_num")
                or permit.get("request_num")
                or permit.get("handasa_document_guid")
            )
            identifier = str(identifier_raw).strip() if identifier_raw not in (None, "") else None
            if identifier and identifier in seen:
                continue
            if identifier:
                seen.add(identifier)
            permits.append(permit)

        logger.info(
            "Collected Handasa permits", extra={"block": block, "parcel": parcel, "count": len(permits)}
        )
        return permits

    # ------------------------------------------------------------------
    @staticmethod
    def _document_to_permit(document: Dict[str, Any], block: str, parcel: str) -> Dict[str, Any]:
        """Translate a Handasa document payload into the GIS permit schema."""

        def _first(*keys: str) -> Optional[Any]:
            for key in keys:
                if key in document and document[key] not in (None, ""):
                    return document[key]
            return None

        def _normalize_id(value: Any) -> Optional[str]:
            if value is None:
                return None
            text = str(value).strip()
            return text or None

        def _parse_timestamp(value: Any) -> Optional[int]:
            if value in (None, ""):
                return None
            if isinstance(value, (int, float)):
                # Assume already unix timestamp (seconds or milliseconds)
                if value > 10 ** 12:  # milliseconds
                    return int(value)
                return int(value * 1000)
            if isinstance(value, str):
                text = value.strip()
                if not text:
                    return None
                for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%d/%m/%Y"):
                    try:
                        dt = datetime.strptime(text.replace("Z", ""), fmt)
                        return int(dt.timestamp() * 1000)
                    except ValueError:
                        continue
            return None

        title = _first("Title", "DocumentTitle", "DocumentName", "Subject")
        description = _first("DocumentDescription", "Description", "DocumentType")
        permission_num = _normalize_id(
            _first(
                "PermissionNumber",
                "PermitNumber",
                "PermitNum",
                "DocumentNumber",
                "DocumentId",
                "DocumentID",
                "Title",
            )
        )
        if permission_num is None and title:
            # Extract digits from the title as a fallback identifier
            digits = "".join(ch for ch in str(title) if ch.isdigit())
            permission_num = digits or None

        request_num = _normalize_id(_first("RequestNumber", "RequestNum"))
        stage = _first("Status", "Stage", "DocumentStatus")
        permission_date = _parse_timestamp(_first("DocumentDate", "PermissionDate", "CreatedOn"))
        url = _first("DownloadURL", "DownloadUrl", "Url", "URL")

        permit: Dict[str, Any] = {
            "permission_num": permission_num,
            "request_num": request_num,
            "koteret": title,
            "sug_bakasha": description,
            "building_stage": stage,
            "permission_date": permission_date,
            "url_hadmaya": url,
            "ms_gush": str(block) if block is not None else None,
            "ms_chelka": str(parcel) if parcel is not None else None,
            "source": "handasa",
        }

        handasa_guid = _normalize_id(_first("DocumentGuid", "DocumentGUID", "DocumentUniqueId"))
        if handasa_guid:
            permit["handasa_document_guid"] = handasa_guid

        # Preserve original payload for debugging
        permit["handasa_raw"] = document
        return permit

    # ------------------------------------------------------------------
    def validate_parameters(self, **kwargs) -> bool:
        block = kwargs.get("block")
        parcel = kwargs.get("parcel")
        return bool(block and parcel)

    def _get_scraper(self) -> HandasaScraper:
        if self._scraper is None:
            self._scraper = HandasaScraper()
        return self._scraper

