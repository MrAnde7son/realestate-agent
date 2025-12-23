"""Lightweight client for RAMI/Amidar residential tenders (MichrazimSite)."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional

import requests

from utils.retry import request_with_retry


class MichrazimClient:
    """Client wrapper around https://apps.land.gov.il/MichrazimSite APIs."""

    BASE_URL = "https://apps.land.gov.il/MichrazimSite"
    SEARCH_ENDPOINT = f"{BASE_URL}/api/SearchApi/Search"
    DETAILS_ENDPOINT = f"{BASE_URL}/api/MichrazDetailsApi/Get"
    YESHUVIM_ENDPOINT = f"{BASE_URL}/api/YeshuvimApi/Get"

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
        self,
        yeshuv_code: Optional[int] = None,
        extra_payload: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Return list of tenders from the Search endpoint.

        The endpoint responds even with an almost-empty payload; optionally filter
        server-side by settlement code when provided.
        """
        payload: Dict[str, Any] = {
            "ActiveQuickSearch": False,
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
            timeout=timeout or self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        self.logger.debug("Unexpected search response format: %s", type(data))
        return []

    def get_details(self, michraz_id: int, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Fetch detailed tender information by ID."""
        response = request_with_retry(
            self.session.get,
            self.DETAILS_ENDPOINT,
            params={"michrazID": michraz_id},
            headers=self.headers,
            timeout=timeout or self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            return data
        self.logger.debug("Unexpected details response format for %s: %s", michraz_id, type(data))
        return {}

    def get_yishuvim(self, timeout: Optional[float] = None) -> List[Dict[str, Any]]:
        """Fetch list of all settlements (yishuvim) with their codes and names.
        
        Returns a list of settlement objects, each containing fields like:
        - mtysvSemelYishuv: settlement code (int) - used for filtering searches
        - mtysvShemYishuv: settlement name (str)
        - Other settlement metadata fields
        """
        response = request_with_retry(
            self.session.get,
            self.YESHUVIM_ENDPOINT,
            headers=self.headers,
            timeout=timeout or self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, list):
            return data
        self.logger.debug("Unexpected yishuvim response format: %s", type(data))
        return []

    @staticmethod
    def _normalize_duplicate_letters(text: str) -> str:
        """Normalize Hebrew text by removing consecutive duplicate letters.
        
        This handles spelling variations like הרצלייה vs הרצליה (double yod),
        and other cases where duplicate letters may appear.
        
        Args:
            text: Hebrew text to normalize
            
        Returns:
            Normalized text with consecutive duplicate letters removed
        """
        if not text:
            return text
        # Remove consecutive duplicate characters using regex
        # This matches any character followed by one or more of the same character
        return re.sub(r'(.)\1+', r'\1', text)
    
    def find_yishuv_code(self, yishuv_name: str, timeout: Optional[float] = None) -> Optional[int]:
        """Find settlement code (mtysvSemelYishuv) by settlement name.
        
        Args:
            yishuv_name: Settlement name to search for (e.g., "תל אביב יפו")
            timeout: Optional request timeout
            
        Returns:
            Settlement code (mtysvSemelYishuv) if found, None otherwise
        """
        yishuvim = self.get_yishuvim(timeout=timeout)
        yishuv_name_normalized = yishuv_name.strip()
        yishuv_name_normalized_no_dups = self._normalize_duplicate_letters(yishuv_name_normalized)
        
        for yishuv in yishuvim:
            name = yishuv.get("mtysvShemYishuv", "").strip()
            # Try exact match first
            if name == yishuv_name_normalized:
                code = yishuv.get("mtysvSemelYishuv")
                if code:
                    try:
                        return int(code)
                    except (ValueError, TypeError):
                        self.logger.debug("Invalid mtysvSemelYishuv value: %s", code)
            # Try normalized match (handles duplicate letters like double yod)
            name_normalized = self._normalize_duplicate_letters(name)
            if name_normalized == yishuv_name_normalized_no_dups:
                code = yishuv.get("mtysvSemelYishuv")
                if code:
                    try:
                        return int(code)
                    except (ValueError, TypeError):
                        self.logger.debug("Invalid mtysvSemelYishuv value: %s", code)
        return None


__all__ = ["MichrazimClient"]

if __name__ == "__main__":
    client = MichrazimClient()
    print(client.search(extra_payload={'mtysvShemYishuv': 'פתח תקווה'}))
