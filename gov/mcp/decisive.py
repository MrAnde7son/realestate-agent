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
    """Extract a field value following a label in a block of text."""
    # Match patterns like "label: value" or "label - value" with optional spaces.
    # Accept both the regular hyphen and the en dash (–) to support variations
    # that appear in different data sources.
    # Also support "מיום" pattern which is followed by just a space
    if label == "מיום":
        # Special pattern for "מיום" - can be followed by space only  
        pattern = rf"{re.escape(label)}\s+(\d{{2}}\.\d{{2}}\.\d{{2,4}}|\d{{2}}/\d{{2}}/\d{{2,4}})"
    else:
        pattern = rf"{re.escape(label)}\s*[:\-–]\s*([^|,]*)"
    
    match = re.search(pattern, text)
    if not match:
        return ""

    value = match.group(1).strip()

    # Trim at common separators if they appear inside the value
    for sep in [" - ", " | ", ", ", " – "]:
        if sep in value:
            value = value.split(sep)[0].strip()
    return value


def _parse_items(html: str) -> List[Dict]:
    """Parse decisive appraisal items from HTML, supporting both old and new website structures."""
    soup = BeautifulSoup(html, "lxml")
    items = []
    
    # Try the old structure first (.collector-result-item)
    old_cards = soup.select(".collector-result-item")
    if old_cards:
        for card in old_cards:
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
    
    # If no results with old structure, try the new structure (ol.search_results li)
    if not items:
        new_cards = soup.select("ol.search_results li")
        for li in new_cards:
            # Extract title from h5 > a
            h5 = li.find("h5")
            if not h5:
                continue
                
            link_tag = h5.find("a", href=True)
            if not link_tag:
                continue
                
            title = link_tag.get_text(strip=True)
            relative_href = link_tag.get("href", "")
            
            # Build full URL
            pdf_url = urljoin(BASE_URL, relative_href) if relative_href else ""
            
            # Extract details from p.body
            body_p = li.find("p", class_="body")
            details_text = body_p.get_text(" | ", strip=True) if body_p else ""
            
            # Extract specific fields using the existing _extract_field function
            # Extract date from title - look for "מיום" pattern
            date = _extract_field(title, "מיום")  # "from date" - extract from title
            if not date:
                # Fallback: try to extract date pattern directly from title
                import re
                date_match = re.search(r"\d{2}\.\d{2}\.\d{2,4}", title)
                if date_match:
                    date = date_match.group(0)
            appraiser = _extract_field(details_text, "שמאי")
            committee = _extract_field(details_text, "ועדה")
            
            items.append({
                "title": title,
                "date": date,
                "appraiser": appraiser,
                "committee": committee,
                "pdf_url": pdf_url,
            })
    
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
