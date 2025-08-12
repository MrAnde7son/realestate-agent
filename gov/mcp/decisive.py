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
    # Simple and reliable field extraction
    # Look for the label followed by colon or dash
    if f"{label}:" in text:
        # Find the start of the value (after the colon)
        start = text.find(f"{label}:") + len(f"{label}:")
        value = text[start:].strip()
        
        # Find the end of the value by looking for the next field label
        # or common separators
        end_positions = []
        
        # Look for next field labels
        for next_label in ["שמאי:", "ועדה:"]:
            pos = value.find(next_label)
            if pos != -1:
                end_positions.append(pos)
        
        # Look for separators
        for sep in [" - ", " | ", ", "]:
            pos = value.find(sep)
            if pos != -1:
                end_positions.append(pos)
        
        # Use the earliest end position
        if end_positions:
            end_pos = min(end_positions)
            value = value[:end_pos].strip()
        
        return value
    
    elif f"{label}-" in text:
        # Handle dash separator
        start = text.find(f"{label}-") + len(f"{label}-")
        value = text[start:].strip()
        
        # Find the end of the value
        end_positions = []
        
        # Look for next field labels
        for next_label in ["שמאי:", "ועדה:"]:
            pos = value.find(next_label)
            if pos != -1:
                end_positions.append(pos)
        
        # Look for separators
        for sep in [" - ", " | ", ", "]:
            pos = value.find(sep)
            if pos != -1:
                end_positions.append(pos)
        
        # Use the earliest end position
        if end_positions:
            end_pos = min(end_positions)
            value = value[:end_pos].strip()
        
        return value
    
    return ""


def _parse_items(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    items = []
    for card in soup.select(".collector-result-item"):
        link_tag = card.find("a", href=True)
        
        # Extract title with proper separators
        if link_tag:
            title = link_tag.get_text(strip=True)
        else:
            # If no link, manually construct title with separators
            spans = card.find_all("span")
            title_parts = []
            for span in spans:
                title_parts.append(span.get_text(strip=True))
            title = " | ".join(title_parts)
        
        pdf_url = urljoin(BASE_URL, link_tag["href"]) if link_tag else ""
        
        # Extract text with proper separators
        if link_tag:
            # If there's a link, use the existing approach
            text = card.get_text(" | ", strip=True)
        else:
            # If no link, manually construct text with separators
            spans = card.find_all("span")
            text_parts = []
            for span in spans:
                text_parts.append(span.get_text(strip=True))
            text = " | ".join(text_parts)
        
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
