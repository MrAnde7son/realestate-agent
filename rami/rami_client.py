"""Client for fetching planning (Taba) data from land.gov.il.

This class wraps the ``TabaSearch`` API endpoint and exposes a ``fetch_plans``
method that paginates through results and returns them as a
:class:`pandas.DataFrame`.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Iterable, Optional

import pandas as pd
import requests


class RamiClient:
    """Simple client for the RAMI TabaSearch API."""

    ENDPOINT = "https://apps.land.gov.il/TabaSearch/api/Plans/SearchPlans"

    DEFAULT_HEADERS: Dict[str, str] = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0",
    }

    def __init__(
        self,
        *,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        page_param: str = "page",
        size_param: str = "size",
        page_size: int = 100,
        max_pages: int = 200,
        delay: float = 0.2,
        session: Optional[requests.Session] = None,
        endpoint: Optional[str] = None,
    ) -> None:
        self.session = session or requests.Session()
        self.headers = dict(self.DEFAULT_HEADERS)
        if headers:
            self.headers.update(headers)
        self.cookies = cookies
        self.page_param = page_param
        self.size_param = size_param
        self.page_size = page_size
        self.max_pages = max_pages
        self.delay = delay
        self.endpoint = endpoint or self.ENDPOINT
        # Ensure a User-Agent header exists on the session for some picky APIs
        self.session.headers.update({"User-Agent": self.headers.get("User-Agent", "Mozilla/5.0")})

    def _one_page(self, base_payload: Dict[str, Any], page: int) -> Dict[str, Any]:
        """Fetch a single page of search results."""
        payload = dict(base_payload)
        if self.page_param:
            payload[self.page_param] = page
        if self.size_param:
            payload[self.size_param] = self.page_size
        response = self.session.post(
            self.endpoint,
            json=payload,
            headers=self.headers,
            cookies=self.cookies,
            timeout=60,
        )
        if response.status_code == 401:
            raise RuntimeError("401 Unauthorized – missing Cookie/Authorization headers?")
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _extract_results(data: Any) -> Iterable[Any]:
        """Return the list of items from a response payload."""
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        for key in ("data", "result", "results", "items"):
            node = data.get(key) if isinstance(data, dict) else None
            if isinstance(node, list):
                return node
            if isinstance(node, dict) and "items" in node:
                return node["items"]
        return []

    @staticmethod
    def _extract_total(data: Any) -> Optional[int]:
        """Attempt to extract total count of records from response payload."""
        if not isinstance(data, dict):
            return None
        for key in ("total", "count", "TotalCount"):
            value = data.get(key)
            if isinstance(value, int):
                return value
            if isinstance(value, dict) and isinstance(value.get("value"), int):
                return value["value"]
        return None

    def fetch_plans(self, base_payload: Dict[str, Any]) -> pd.DataFrame:
        """Fetch all plan results for a given search payload."""
        rows: list[Any] = []
        total: Optional[int] = None
        for p in range(self.max_pages):
            data = self._one_page(base_payload, p)
            page_rows = list(self._extract_results(data))
            if not page_rows:
                break
            rows.extend(page_rows)
            if total is None:
                total = self._extract_total(data)
            if total is not None and len(rows) >= total:
                break
            time.sleep(self.delay)
        return pd.DataFrame(rows)


__all__ = ["RamiClient"]
