from __future__ import annotations

import re
from typing import List, Dict
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .constants import USER_AGENT, DEFAULT_TIMEOUT

BASE_URL = "https://www.gov.il"
DECISIVE_ENDPOINT = (
    f"{BASE_URL}/he/departments/dynamiccollectors/decisive_appraisal_decisions"
)
HEADERS = {"User-Agent": USER_AGENT}


def _extract_field(text: str, label: str) -> str:
    pattern = rf"{label}\s*[:\-]\s*([^|]+?)\s*(?=$|\|)"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return ""


def _parse_items(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    items = []
    for card in soup.select(".collector-result-item"):
        link_tag = card.find("a", href=True)
        title = link_tag.get_text(strip=True) if link_tag else card.get_text(strip=True)
        pdf_url = urljoin(BASE_URL, link_tag["href"]) if link_tag else ""
        text = card.get_text(" | ", strip=True)
        date = _extract_field(text, "תאריך")
        appraiser = _extract_field(text, "שמאי")
        committee = _extract_field(text, "ועדה")
        items.append(
            {
                "title": title,
                "date": date,
                "appraiser": appraiser,
                "committee": committee,
                "pdf_url": pdf_url,
            }
        )
    return items


def fetch_decisive_appraisals(block: str = "", plot: str = "", max_pages: int = 1) -> List[Dict]:
    """Fetch decisive appraisal decisions from gov.il dynamic collector."""
    params = {"Block": block, "Plot": plot, "skip": 0}
    all_items: List[Dict] = []
    for page in range(max_pages):
        resp = requests.get(
            DECISIVE_ENDPOINT, params=params, headers=HEADERS, timeout=DEFAULT_TIMEOUT
        )
        resp.raise_for_status()
        items = _parse_items(resp.text)
        if not items:
            break
        all_items.extend(items)
        params["skip"] += 10
    return all_items
