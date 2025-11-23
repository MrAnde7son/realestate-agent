"""Lightweight client for RAMI/Amidar residential tenders (MichrazimSite)."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import requests

from utils.retry import request_with_retry


class MichrazimClient:
    """Client wrapper around https://apps.land.gov.il/MichrazimSite APIs."""

    BASE_URL = "https://apps.land.gov.il/MichrazimSite"
    SEARCH_ENDPOINT = f"{BASE_URL}/api/SearchApi/Search"
    DETAILS_ENDPOINT = f"{BASE_URL}/api/MichrazDetailsApi/Get"

    DEFAULT_HEADERS: Dict[str, str] = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "he,en;q=0.9",
    }

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 60.0,
    ) -> None:
        self.session = session or requests.Session()
        self.headers = dict(self.DEFAULT_HEADERS)
        if headers:
            self.headers.update(headers)
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def search(
        self, yeshuv_code: Optional[int] = None, extra_payload: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Return list of tenders from the Search endpoint.

        The endpoint responds even with an almost-empty payload; optionally filter
        server-side by settlement code when provided.
        """
        payload: Dict[str, Any] = {
            "ActiveQuickSearch": True,
            "ActiveMichraz": None,
        }
        if yeshuv_code:
            payload["KodYeshuv"] = yeshuv_code
        if extra_payload:
            payload.update(extra_payload)

        response = request_with_retry(
            self.session.post,
            self.SEARCH_ENDPOINT,
            json=payload,
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        self.logger.debug("Unexpected search response format: %s", type(data))
        return []

    def get_details(self, michraz_id: int) -> Dict[str, Any]:
        """Fetch detailed tender information by ID."""
        response = request_with_retry(
            self.session.get,
            self.DETAILS_ENDPOINT,
            params={"michrazID": michraz_id},
            headers=self.headers,
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data
        self.logger.debug("Unexpected details response format for %s: %s", michraz_id, type(data))
        return {}


__all__ = ["MichrazimClient"]
