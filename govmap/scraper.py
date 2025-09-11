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
    def __init__(self, base_url: str = "https://es.govmap.gov.il/TldSearch/api/AutoComplete", timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.sess = requests.Session()
        self.sess.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
        })

    def search(self, query: str, ids: str = "276267023", gid: str = "govmap") -> Dict[str, Any]:
        r = self.sess.get(self.base_url, params={"query": query, "ids": ids, "gid": gid}, timeout=self.timeout, verify=False)
        r.raise_for_status()
        return r.json()

    def top_neighborhood_id(self, query: str) -> str | None:
        data = self.search(query)
        res = data.get("res", {})
        for bucket in ("NEIGHBORHOOD", "POI_MID_POINT", "STREET", "SETTLEMENT", "BUILDING"):
            for item in res.get(bucket, [])[:5]:
                key = item.get("Key", "")
                if key and "id=" in key:
                    # heuristic: parse id param if present in key/url-like string
                    try:
                        import urllib.parse as up
                        q = up.urlparse(key)
                        qs = up.parse_qs(q.query)
                        nid = qs.get("id", [None])[0]
                        if nid:
                            return str(nid)
                    except Exception:
                        pass
        return None
