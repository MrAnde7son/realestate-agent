# -*- coding: utf-8 -*-
"""
A super-light "scraper" for the public GovMap autocomplete endpoint.
Use this when you want address/POI/neighborhood suggestions without the JS SDK.

You already call this pattern in gov/nadlan/scraper.py; this class wraps it in a
reusable component so other modules can depend on it directly.
"""
from typing import Any, Dict, List
import requests

class GovMapAutocomplete:
    def __init__(self, base_url: str = "https://www.govmap.gov.il/api/search-service/autocomplete", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.sess = requests.Session()
        self.sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })

    def search(self, query: str, language: str = "he", max_results: int = 10) -> Dict[str, Any]:
        # Update headers for the new API
        self.sess.headers.update({
            "Accept": "application/json",
            "Accept-Language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
            "Content-Type": "application/json",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        })
        
        # Prepare JSON body for the new API
        payload = {
            "searchText": query,
            "language": language,
            "isAccurate": False,
            "maxResults": max_results
        }
        
        r = self.sess.post(self.base_url, json=payload, timeout=self.timeout, verify=False)
        r.raise_for_status()
        return r.json()

    def top_neighborhood_id(self, query: str) -> str | None:
        data = self.search(query)
        results = data.get("results", [])
        for result in results[:5]:
            # Check if this is a neighborhood or POI result
            data_type = result.get("data", {}).get("type", "")
            if data_type in ("NEIGHBORHOOD", "POI_MID_POINT", "STREET", "SETTLEMENT", "BUILDING"):
                return result.get("id")
        return None
