# -*- coding: utf-8 -*-
"""
Parse Tel-Aviv "Zchuyot" (rights) PDF -> structured JSON for MCP server.

Extracts:
- header: issue_date, address, block/parcel, parcel area (if present)
- alerts (התראות)
- plans in force: local / citywide / national-regional (+ in planning if present)
- policy docs (מדיניות תכנונית)
- rights details (זכויות/קווי בניין/אחוזים) when recognizable
- all hyperlinks to plan docs and maps

Usage:
  python parse_zchuyot.py file.pdf --json out.json --plans-csv plans.csv
"""

import argparse
import csv
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pdfplumber
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

# Optional OCR
try:
    import pytesseract
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None
    Image = None

WS = re.compile(r"[ \t\u200e\u200f]+")
MULTI_NL = re.compile(r"\n{2,}")


def norm(s: str) -> str:
    s = (s or "").replace("\u200e", "").replace("\u200f", "")
    s = WS.sub(" ", s)
    return s.strip()


def try_date(s: str) -> Optional[str]:
    s = (s or "").strip().replace(".", "-").replace("/", "-")
    try:
        return dateparser.parse(s, dayfirst=True, fuzzy=True).strftime("%Y-%m-%d")
    except Exception:
        return None


def extract_text(pdf_path: str) -> str:
    txt_pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            t = p.extract_text() or ""
            txt_pages.append(t)
    text = MULTI_NL.sub("\n", "\n".join(txt_pages))
    if len(norm(text)) >= 80:
        return text

    # OCR fallback (images)
    if pytesseract and Image:  # pragma: no cover - requires optional deps
        ocr = []
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                im = p.to_image(resolution=300).original
                if not isinstance(im, Image.Image):
                    im = Image.fromarray(im)
                ocr.append(pytesseract.image_to_string(im, lang="heb+eng"))
        return "\n".join(ocr)
    return text


# ---------- header / basic ----------
def parse_header(text: str) -> Dict[str, Any]:
    out = {
        "issue_date": None,
        "address": None,
        "block": None,
        "parcel": None,
        "parcel_area_sqm": None,
    }
    # תאריך הפקה
    out["issue_date"] = find_first([
        r"(?:(?:תאריך|תאריך הפקה)\s*[:\-]?\s*)([0-9./ -]{6,})"
    ], text, date=True)

    # כתובת (משתנה בין פורמטים)
    out["address"] = find_first([
        r"(?:רחוב|כתובת)\s*[:\-]?\s*([^\n]+)"
    ], text)

    # גוש/חלקה
    g = find_first([r"גוש\s*[:\-]?\s*(\d{1,6})"], text)
    h = find_first([r"חלקה\s*[:\-]?\s*(\d{1,6})"], text)
    out["block"] = safe_int(g)
    out["parcel"] = safe_int(h)

    # שטח חלקה/מגרש (אם קיים)
    area = find_first([
        r"(?:שטח\s*(?:מגרש|חלקה|לחישוב|מר')\s*[:\- ]*)([\d,\.]+)"
    ], text)
    if area:
        try:
            out["parcel_area_sqm"] = float(area.replace(",", ""))
        except Exception:
            pass
    return out


# ---------- sections split ----------
def split_sections(text: str) -> Dict[str, str]:
    """
    Split by common section headers (robust to OCR noise).
    """
    markers = [
        ("alerts",       r"\nהתראות\b"),
        ("plans_local",  r"\nבתוקף\s+מקומיות\s+תכניות\b"),
        ("plans_city",   r"\nבתוקף\s+עירוניות\s+כלל\b"),
        ("plans_natreg", r"\nבתוקף\s+ומחוזיות\s+ארציות\s+מתאר\s+תכניות\b"),
        ("plans_arch",   r"\nארכיטקטוני\s+ועיצוב\s+בינוי\s+תוכניות\b"),
        ("in_planning_city", r"\nבתכנון\s+עירוניות\s+כלל\b"),
        ("in_planning_natreg", r"\nבתכנון\s+ומחוזיות\s+ארציות\s+מתאר\s+תכניות\b"),
        ("policy",       r"\nמדיניות\s+תכנונית\b"),
        ("land_use",     r"\nקרקע\s+יעוד\b"),
        ("rights",       r"\nזכויות\s+פירוט\b"),
        ("permit_terms", r"\nבניה\s+היתר\s+למתן\s+תנאי\b"),
        ("links",        r"\nhttps?://"),
    ]
    # Build a list of (name, start_idx)
    indices = []
    for name, pat in markers:
        m = re.search(pat, text, re.S)
        if m:
            indices.append((name, m.start()))
    # sort by position
    indices.sort(key=lambda x: x[1])

    sections = {}
    for i, (name, pos) in enumerate(indices):
        end = indices[i + 1][1] if i + 1 < len(indices) else len(text)
        sections[name] = text[pos:end]
    return sections


# ---------- helpers ----------
def safe_int(s: Optional[str]) -> Optional[int]:
    try:
        return int(s) if s and s.isdigit() else None
    except Exception:
        return None


def find_first(patterns: List[str], text: str, date=False) -> Optional[str]:
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            val = norm(m.group(1))
            if date:
                return try_date(val) or val
            return val
    return None


def find_all_urls(text: str) -> List[str]:
    urls = re.findall(r"https?://[^\s]+", text)
    # clean trailing punctuation
    clean = []
    for u in urls:
        u = u.rstrip(").,;]>\u200e\u200f")
        clean.append(u)
    # dedupe keep order
    seen = set()
    out = []
    for u in clean:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out


DATE_PAT = r"(?:[0-3]?\d/[01]?\d/\d{4})"


def parse_plans_block(block: str) -> List[Dict[str, Any]]:
    """
    Parse a table-like block of plans. Heuristics:
    - plan number: 3-6 digits (optionally with / parts e.g. 1/40/א/1/1)
    - name: text between number and dates
    - dates: deposit / effective (מתן תוקף) if present
    - attach nearby URLs when possible (handled outside as well)
    """
    lines = [norm(l) for l in block.splitlines() if norm(l)]
    out = []
    for i, L in enumerate(lines):
        # plan number (supports complex forms with Hebrew letters)
        mnum = re.search(r"((?:\d{3,6}(?:/\d+)*)(?:/[א-ת]\d*)?(?:/\d+)*)", L)
        if not mnum:
            continue
        plan_no = mnum.group(1)

        # extract possible dates
        dates = re.findall(DATE_PAT, L)
        deposit = valid_date(dates[0]) if dates else None
        effective = valid_date(dates[1]) if len(dates) > 1 else None

        # crude name: remove number and dates from line
        name = L
        name = name.replace(plan_no, "").strip()
        for d in dates:
            name = name.replace(d, "").strip()
        # common Hebrew labels to strip
        name = re.sub(r"(?:תוכנית|שם|הפקדה|מתן|תוקף|ילקוט`?מס|פרסומים|מס`?)", "", name).strip(" -:;,")

        if plan_no or name or deposit or effective:
            out.append({
                "plan_number": plan_no or None,
                "name": name or None,
                "deposit_date": deposit,
                "effective_date": effective,
            })
    return dedupe_plans(out)


def valid_date(s: Optional[str]) -> Optional[str]:
    return try_date(s) if s else None


def dedupe_plans(plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for p in plans:
        key = (p.get("plan_number"), p.get("deposit_date"), p.get("effective_date"), p.get("name"))
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def parse_alerts(block: str) -> List[str]:
    # split lines, keep meaningful alerts
    lines = [norm(l) for l in block.splitlines()]
    alerts = []
    for L in lines:
        if not L:
            continue
        # examples: "אתר עתיקות (רשות העתיקות)", "הגבלות גובה מחמירות", "התראה מעניקה"
        if any(tok in L for tok in ["התראה", "הגבלה", "עתיקות", "ארכיאולוג", "גובה", "מעניקה"]):
            alerts.append(L)
    # dedupe
    out = []
    seen = set()
    for a in alerts:
        if a not in seen:
            seen.add(a)
            out.append(a)
    return out


def parse_rights(block: str) -> Dict[str, Any]:
    """
    Enhanced version that can extract comprehensive building rights data:
    - building lines (קו בניין צדדי/אחורי/חזית)
    - number of floors (מספר קומות)
    - percent (%/אחוז בנייה)
    - area measurements in square meters
    - building rights measurements
    - floor area percentages (25%, 75%)
    - basement area (מרתף)
    - service areas (שטחי שירות)
    - auxiliary buildings (מבני עזר)
    - references to a plan number in text
    """
    rights = {"notes": []}
    lines = [norm(l) for l in block.splitlines() if norm(l)]
    
    for L in lines:
        # Look for building lines (קו בניין) - more flexible patterns
        if any(word in L for word in ["קו", "בניין", "קו בניין"]):
            rights.setdefault("building_lines", []).append(L)
        
        # Look for building lines with backticks (from the PDF)
        if "`מ" in L and "ןיינבוק" in L:
            rights.setdefault("building_lines", []).append(L)
        
        # Look for floor information
        if re.search(r"(?:מספר\s+קומות|קומות\s*מספר)", L):
            rights["floors_note"] = L
        
        # Look for building percentage
        percent_match = re.search(r"(\d{2,3})\s*%(?:\s*בנ(?:י|י)ה)?", L)
        if percent_match:
            rights["percent_building"] = int(percent_match.group(1))
        
        # Look for floor area percentages and types dynamically
        # Pattern: "שטח קומה טיפוסית 25%" or "שטח קומה שנייה 75%"
        floor_patterns = [
            r"שטח\s+קומה\s+(טיפוסית|ראשונה|שנייה|שלישית|רביעית|חמישית|עליונה|תחתונה)\s*(\d+)\s*%",
            r"(\d+)\s*%\s*שטח\s+קומה\s+(טיפוסית|ראשונה|שנייה|שלישית|רביעית|חמישית|עליונה|תחתונה)",
            r"קומה\s+(טיפוסית|ראשונה|שנייה|שלישית|רביעית|חמישית|עליונה|תחתונה)\s*(\d+)\s*%",
            r"(\d+)\s*%\s*קומה\s+(טיפוסית|ראשונה|שנייה|שלישית|רביעית|חמישית|עליונה|תחתונה)",
            # More flexible patterns for PDF text
            r"(\d+)\s*%\s*(טיפוסית|ראשונה|שנייה|שלישית|רביעית|חמישית|עליונה|תחתונה)",
            r"(טיפוסית|ראשונה|שנייה|שלישית|רביעית|חמישית|עליונה|תחתונה)\s*(\d+)\s*%",
            # Pattern for "25%אוהש" and "75%לשרועשבתיקלח"
            r"(\d+)\s*%\s*אוהש",
            r"(\d+)\s*%\s*לשרועשבתיקלח"
        ]
        
        for pattern in floor_patterns:
            matches = re.findall(pattern, L)
            for match in matches:
                if len(match) == 2:
                    if match[0].isdigit():
                        percent = int(match[0])
                        floor_type = match[1]
                    else:
                        percent = int(match[1])
                        floor_type = match[0]
                    
                    # Map special patterns to floor types
                    if floor_type == "אוהש":
                        floor_type = "טיפוסית"
                    elif floor_type == "לשרועשבתיקלח":
                        floor_type = "שנייה"
                    
                    rights.setdefault("floor_details", []).append({
                        "type": floor_type,
                        "percentage": percent
                    })
                    rights.setdefault("floor_percentages", []).append(percent)
                elif len(match) == 1 and match[0].isdigit():
                    # Handle single percentage patterns
                    percent = int(match[0])
                    rights.setdefault("general_percentages", []).append(percent)
        
        # Look for relative floor percentages (e.g., "75% מקומה טיפוסית")
        relative_patterns = [
            r"(\d+)\s*%\s*מקומה\s+(טיפוסית|ראשונה|שנייה|שלישית|רביעית|חמישית|עליונה|תחתונה)",
            r"(\d+)\s*%\s*מהקומה\s+(טיפוסית|ראשונה|שנייה|שלישית|רביעית|חמישית|עליונה|תחתונה)"
        ]
        
        for pattern in relative_patterns:
            matches = re.findall(pattern, L)
            for match in matches:
                percent = int(match[0])
                base_floor = match[1]
                rights.setdefault("relative_floor_percentages", []).append({
                    "percentage": percent,
                    "base_floor": base_floor
                })
        
        # Look for general percentage patterns (fallback)
        general_percent_match = re.search(r"(\d+)\s*%", L)
        if general_percent_match:
            percent = int(general_percent_match.group(1))
            if 5 <= percent <= 100:  # Reasonable range for building percentages
                rights.setdefault("general_percentages", []).append(percent)
        
        # Look for basement area (מרתף)
        if "מרתף" in L:
            basement_match = re.search(r"(\d+)\s*מ[״\"]ר", L)
            if basement_match:
                rights["basement_area"] = int(basement_match.group(1))
        
        # Look for service areas (שטחי שירות)
        if "שטחי שירות" in L or "שירות" in L:
            service_match = re.search(r"(\d+)\s*%", L)
            if service_match:
                rights["service_percentage"] = int(service_match.group(1))
        
        # Look for auxiliary buildings (מבני עזר)
        if "מבני עזר" in L or "עזר" in L:
            aux_match = re.search(r"(\d+)\s*מ[״\"]ר", L)
            if aux_match:
                rights["auxiliary_buildings"] = int(aux_match.group(1))
        
        # Look for number of floors
        floors_match = re.search(r"(\d+)\s*קומות", L)
        if floors_match:
            rights["number_of_floors"] = int(floors_match.group(1))
        
        # Look for building coverage percentages (אחוז בנייה)
        if "אחוז בנייה" in L or "בנייה" in L or "בחור" in L:
            coverage_match = re.search(r"(\d+)\s*%", L)
            if coverage_match:
                percent = int(coverage_match.group(1))
                if 10 <= percent <= 100:  # Reasonable range for building coverage
                    rights.setdefault("building_coverage_percentages", []).append(percent)
        
        # Look for parking percentages (אחוז חניה)
        if "חניה" in L or "חנייה" in L:
            parking_match = re.search(r"(\d+)\s*%", L)
            if parking_match:
                percent = int(parking_match.group(1))
                if 5 <= percent <= 50:  # Reasonable range for parking
                    rights.setdefault("parking_percentages", []).append(percent)
        
        # Look for roof percentages (אחוז גג)
        if "גג" in L:
            roof_match = re.search(r"(\d+)\s*%", L)
            if roof_match:
                percent = int(roof_match.group(1))
                if 10 <= percent <= 100:  # Reasonable range for roof
                    rights.setdefault("roof_percentages", []).append(percent)
        
        # Look for floor area percentages (אחוז קומה)
        if "קומה" in L and "%" in L:
            floor_match = re.search(r"(\d+)\s*%", L)
            if floor_match:
                percent = int(floor_match.group(1))
                if 5 <= percent <= 100:  # Reasonable range for floor
                    rights.setdefault("floor_percentages", []).append(percent)
        
        # Look for area measurements in square meters - more flexible patterns
        area_matches = re.findall(r"(\d+)\s*מ[״\"]ר", L)
        if area_matches:
            rights.setdefault("areas", []).extend([int(m) for m in area_matches])
        
        # Look for area measurements with backticks (from the PDF)
        area_matches_backticks = re.findall(r"`מ(\d+)", L)
        if area_matches_backticks:
            rights.setdefault("areas", []).extend([int(m) for m in area_matches_backticks])
        
        # Look for building rights measurements with backticks
        if "`מ" in L and "ןיינבוק" in L:
            rights.setdefault("building_rights_areas", []).append(L)
        
        # Look for specific building rights patterns with backticks
        if re.search(r"`מ(\d+).*ןיינבוק", L):
            rights.setdefault("specific_building_rights", []).append(L)
        
        # Look for building rights patterns with backticks - more flexible
        if "`מ" in L and "ןיינבוק" in L:
            rights.setdefault("specific_building_rights", []).append(L)
        
        # Look for building rights patterns with backticks - even more flexible
        if "`מ" in L:
            rights.setdefault("building_rights_areas", []).append(L)
        
        # Look for building rights patterns with spaces and backticks
        if "`מ " in L and "ןיינבוק" in L:
            rights.setdefault("building_rights_areas", []).append(L)
        
        # Look for specific building rights patterns from the PDF
        # Pattern: `מ 7ןיינבוק `מ 18ךרדבחור 19 (905)דודסוכרמבוחר
        if "`מ" in L and "ןיינבוק" in L and "ךרדבחור" in L:
            rights.setdefault("specific_building_rights", []).append(L)
        
        # Look for building rights with specific numbers
        # Pattern: `מ 6ןיינבוק `מ 10ךרדבחור 78 (903)ם"קבוחר
        if "`מ" in L and "ןיינבוק" in L and "ם" in L:
            rights.setdefault("specific_building_rights", []).append(L)
        
        # Look for building rights measurements - more flexible
        if "מ״ר" in L:
            rights.setdefault("building_rights_areas", []).append(L)
        
        # Look for specific building rights patterns
        if re.search(r"(\d+)\s*מ[״\"]ר.*(?:קו|בניין|זכות|בנייה)", L):
            rights.setdefault("specific_building_rights", []).append(L)
        
        # Look for plan references
        plan_refs = re.findall(r"\b(\d{3,6})\b", L)
        if plan_refs:
            rights.setdefault("referred_plans", set()).update(plan_refs)
        
        # Look for block and parcel info
        if "גוש" in L or "חלקה" in L:
            rights.setdefault("parcel_info", []).append(L)
        
        # Add note as a dictionary with the text content
        rights["notes"].append({"text": L, "type": "general"})
    
    # Convert sets to lists for JSON serialization
    if "referred_plans" in rights:
        rights["referred_plans"] = sorted(list(rights["referred_plans"]))
    
    return rights


def parse_policy(block: str) -> List[Dict[str, Any]]:
    out = []
    lines = [norm(l) for l in block.splitlines() if norm(l)]
    for L in lines:
        mnum = re.search(r"\b(9\d{3}|8\d{3})\b", L)  # many policy ids 9000+
        dates = re.findall(DATE_PAT, L)
        name = L
        if mnum:
            name = name.replace(mnum.group(0), "").strip()
        for d in dates:
            name = name.replace(d, "").strip()
        if mnum or dates or name:
            out.append({
                "policy_number": mnum.group(0) if mnum else None,
                "name": name or None,
                "date": valid_date(dates[0]) if dates else None,
            })
    return out


def parse_html_privilege_page(html_content: str) -> List[Dict[str, Any]]:
    """
    Parse HTML privilege page and extract all parcels from the dropdown menu.
    
    Args:
        html_content: HTML content of the privilege page
        
    Returns:
        List of dictionaries containing parcel information
    """
    parcels = []

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        opts_pattern = r"is_opts\s*=\s*'([^']+)'"
        opts_match = re.search(opts_pattern, html_content)

        if opts_match:
            opts_html = opts_match.group(1).replace('`', '"')
            opts_soup = BeautifulSoup(opts_html, 'html.parser')
            
            for option in opts_soup.find_all('option'):
                value = option.get('value', '')
                text = option.get_text(strip=True)
                
                if value and text:
                    # Parse the value string to extract parameters
                    # Format: block=6632&parcel=3200&status=0&street=4844&house=0&chasum=0&
                    params = {}
                    for param in value.split('&'):
                        if '=' in param:
                            key, val = param.split('=', 1)
                            params[key] = val
                    
                    # Extract parcel details from text
                    # Format: מגרש: 3200 מוסדר  -  רחוב קדושי השואה  (יעוד קרקע: אזור תעסוקה שטח: 12826.81 מ``ר)
                    parcel_info = {
                        'block': params.get('block'),
                        'parcel': params.get('parcel'),
                        'status': params.get('status'),
                        'street': params.get('street'),
                        'house': params.get('house'),
                        'chasum': params.get('chasum'),
                        'raw_text': text,
                        'parcel_number': None,
                        'parcel_status': None,
                        'street_name': None,
                        'house_number': None,
                        'land_use': None,
                        'area': None
                    }
                    
                    # Parse the Hebrew text to extract structured information
                    # Extract parcel number (e.g., "3200")
                    parcel_num_match = re.search(r'מגרש:\s*(\d+)', text)
                    if parcel_num_match:
                        parcel_info['parcel_number'] = parcel_num_match.group(1)
                    
                    # Extract status (e.g., "מוסדר")
                    status_match = re.search(r'(\w+)\s*-\s*', text)
                    if status_match:
                        parcel_info['parcel_status'] = status_match.group(1)
                    
                    # Extract street name (after the dash)
                    street_match = re.search(r'-\s*([^(]+?)\s*\(', text)
                    if street_match:
                        parcel_info['street_name'] = street_match.group(1).strip()
                    
                    # Extract house number if present
                    house_match = re.search(r'מס.?\s*(\d+)', text)
                    if house_match:
                        parcel_info['house_number'] = house_match.group(1)
                    
                    # Extract land use and area from parentheses
                    details_match = re.search(r'\(([^)]+)\)', text)
                    if details_match:
                        details = details_match.group(1)
                        
                        # Extract land use
                        land_use_match = re.search(r'יעוד קרקע:\s*([^\n]+)', details)
                        if land_use_match:
                            land_use = land_use_match.group(1).split('שטח')[0].strip()
                            parcel_info['land_use'] = land_use

                        # Extract area
                        area_match = re.search(r'שטח:\s*([\d,\.]+)', details)
                        if area_match:
                            parcel_info['area'] = area_match.group(1).strip()
                    
                    parcels.append(parcel_info)
        
        # If no JavaScript parsing worked, try to find options directly in HTML
        if not parcels:
            options = soup.find_all('option')
            for option in options:
                value = option.get('value', '')
                text = option.get_text(strip=True)
                
                if value and text and 'block=' in value:
                    # Parse the value string
                    params = {}
                    for param in value.split('&'):
                        if '=' in param:
                            key, val = param.split('=', 1)
                            params[key] = val
                    
                    parcel_info = {
                        'block': params.get('block'),
                        'parcel': params.get('parcel'),
                        'status': params.get('status'),
                        'street': params.get('street'),
                        'house': params.get('house'),
                        'chasum': params.get('chasum'),
                        'raw_text': text,
                        'parcel_number': None,
                        'parcel_status': None,
                        'street_name': None,
                        'house_number': None,
                        'land_use': None,
                        'area': None
                    }
                    
                    # Try to parse the text content
                    # Extract parcel number
                    parcel_num_match = re.search(r'מגרש:\s*(\d+)', text)
                    if parcel_num_match:
                        parcel_info['parcel_number'] = parcel_num_match.group(1)
                    
                    # Extract other details similar to above
                    status_match = re.search(r'(\w+)\s*-\s*', text)
                    if status_match:
                        parcel_info['parcel_status'] = status_match.group(1)
                    
                    street_match = re.search(r'-\s*([^(]+?)\s*\(', text)
                    if street_match:
                        parcel_info['street_name'] = street_match.group(1).strip()
                    
                    house_match = re.search(r'מס`\s*(\d+)', text)
                    if house_match:
                        parcel_info['house_number'] = house_match.group(1)
                    
                    details_match = re.search(r'\(([^)]+)\)', text)
                    if details_match:
                        details = details_match.group(1)
                        
                        land_use_match = re.search(r'יעוד קרקע:\s*([^\n]+)', details)
                        if land_use_match:
                            land_use = land_use_match.group(1).split('שטח')[0].strip()
                            parcel_info['land_use'] = land_use

                        area_match = re.search(r'שטח:\s*([\d,\.]+)', details)
                        if area_match:
                            parcel_info['area'] = area_match.group(1).strip()
                    
                    parcels.append(parcel_info)
        
        return parcels
        
    except Exception as e:
        # Log error and return empty list
        print(f"Error parsing HTML privilege page: {e}")
        return []


# ---------- main parse ----------
def parse_zchuyot(pdf_path: str) -> Dict[str, Any]:
    text = extract_text(pdf_path)
    text = norm(text)

    basic = parse_header(text)
    sections = split_sections(text)

    urls_all = find_all_urls(text)

    plans_local = parse_plans_block(sections.get("plans_local", ""))
    plans_city = parse_plans_block(sections.get("plans_city", ""))
    plans_natreg = parse_plans_block(sections.get("plans_natreg", ""))
    plans_arch = parse_plans_block(sections.get("plans_arch", ""))
    inplan_city = parse_plans_block(sections.get("in_planning_city", ""))
    inplan_natreg = parse_plans_block(sections.get("in_planning_natreg", ""))

    alerts = parse_alerts(sections.get("alerts", ""))
    policy = parse_policy(sections.get("policy", ""))
    rights = parse_rights(sections.get("rights", "") + "\n" + sections.get("permit_terms", ""))
    
    
    # Also try to parse from the raw_preview if it contains Hebrew text
    if text and not rights.get('notes'):
        # Split raw_preview into lines and process each line
        lines = text.split('\n')
        for line in lines:
            if line.strip():
                # Try to parse each line as a rights note
                line_rights = parse_rights(line)
                if line_rights.get('notes'):
                    rights.setdefault('notes', []).extend(line_rights['notes'])
                if line_rights.get('building_lines'):
                    rights.setdefault('building_lines', []).extend(line_rights['building_lines'])
                if line_rights.get('areas'):
                    rights.setdefault('areas', []).extend(line_rights['areas'])
                if line_rights.get('building_rights_areas'):
                    rights.setdefault('building_rights_areas', []).extend(line_rights['building_rights_areas'])
                if line_rights.get('specific_building_rights'):
                    rights.setdefault('specific_building_rights', []).extend(line_rights['specific_building_rights'])
                if line_rights.get('referred_plans'):
                    rights.setdefault('referred_plans', set()).update(line_rights['referred_plans'])
                if line_rights.get('floor_percentages'):
                    rights.setdefault('floor_percentages', []).extend(line_rights['floor_percentages'])
                if line_rights.get('basement_area'):
                    rights['basement_area'] = line_rights['basement_area']
                if line_rights.get('service_percentage'):
                    rights['service_percentage'] = line_rights['service_percentage']
                if line_rights.get('auxiliary_buildings'):
                    rights['auxiliary_buildings'] = line_rights['auxiliary_buildings']
                if line_rights.get('number_of_floors'):
                    rights['number_of_floors'] = line_rights['number_of_floors']

    # Process all existing notes through parse_rights to extract additional data
    if rights.get('notes'):
        for note in rights['notes']:
            # Handle both string and dictionary note formats
            if isinstance(note, dict):
                note_text = note.get('text', '')
            else:
                note_text = str(note) if note else ''
            
            if note_text and note_text.strip():
                # Try to parse each note for additional rights data
                note_rights = parse_rights(note_text)
                
                # Merge the additional data found in the note
                if note_rights.get('building_coverage_percentages'):
                    rights.setdefault('building_coverage_percentages', []).extend(note_rights['building_coverage_percentages'])
                if note_rights.get('parking_percentages'):
                    rights.setdefault('parking_percentages', []).extend(note_rights['parking_percentages'])
                if note_rights.get('roof_percentages'):
                    rights.setdefault('roof_percentages', []).extend(note_rights['roof_percentages'])
                if note_rights.get('floor_percentages'):
                    rights.setdefault('floor_percentages', []).extend(note_rights['floor_percentages'])
                if note_rights.get('general_percentages'):
                    rights.setdefault('general_percentages', []).extend(note_rights['general_percentages'])
                if note_rights.get('floor_details'):
                    rights.setdefault('floor_details', []).extend(note_rights['floor_details'])
                if note_rights.get('relative_floor_percentages'):
                    rights.setdefault('relative_floor_percentages', []).extend(note_rights['relative_floor_percentages'])
                if note_rights.get('building_lines'):
                    rights.setdefault('building_lines', []).extend(note_rights['building_lines'])
                if note_rights.get('areas'):
                    rights.setdefault('areas', []).extend(note_rights['areas'])
                if note_rights.get('building_rights_areas'):
                    rights.setdefault('building_rights_areas', []).extend(note_rights['building_rights_areas'])
                if note_rights.get('specific_building_rights'):
                    rights.setdefault('specific_building_rights', []).extend(note_rights['specific_building_rights'])
                if note_rights.get('referred_plans'):
                    rights.setdefault('referred_plans', set()).update(note_rights['referred_plans'])
                if note_rights.get('basement_area'):
                    rights['basement_area'] = note_rights['basement_area']
                if note_rights.get('service_percentage'):
                    rights['service_percentage'] = note_rights['service_percentage']
                if note_rights.get('auxiliary_buildings'):
                    rights['auxiliary_buildings'] = note_rights['auxiliary_buildings']
                if note_rights.get('number_of_floors'):
                    rights['number_of_floors'] = note_rights['number_of_floors']

    # attach urls to nearest plan by proximity of number in url (if contains plan id)
    def attach_urls(plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        for p in plans:
            p_urls = []
            pn = p.get("plan_number") or ""
            # loose attach: any url that contains that number somewhere
            for u in urls_all:
                if pn and pn in u:
                    p_urls.append(u)
            if p_urls:
                # dedupe
                pu = []
                seen = set()
                for u in p_urls:
                    if u not in seen:
                        seen.add(u)
                        pu.append(u)
                p["urls"] = pu
        return plans

    plans_local = attach_urls(plans_local)
    plans_city = attach_urls(plans_city)
    plans_natreg = attach_urls(plans_natreg)
    plans_arch = attach_urls(plans_arch)
    inplan_city = attach_urls(inplan_city)
    inplan_natreg = attach_urls(inplan_natreg)

    result = {
        "source_file": os.path.abspath(pdf_path),
        "extracted_at": datetime.utcnow().isoformat() + "Z",
        "basic": basic,
        "alerts": alerts,
        "plans": {
            "in_force": {
                "local": plans_local,
                "citywide": plans_city,
                "national_regional": plans_natreg,
                "architectural": plans_arch,
            },
            "in_planning": {
                "citywide": inplan_city,
                "national_regional": inplan_natreg,
            },
        },
        "policy": policy,
        "rights": rights,
        "all_links": urls_all,  # raw list of every URL found
        "raw_preview": text[:2000],
    }
    return result


# ---------- CLI ----------
def dump_csv(path: str, rows: List[Dict[str, Any]], fields: List[str]):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in fields})


def main():  # pragma: no cover - CLI utility
    ap = argparse.ArgumentParser(description="Parse Tel-Aviv Zchuyot PDF → JSON")
    ap.add_argument("pdf", help="path to PDF")
    ap.add_argument("--json", help="output JSON file")
    ap.add_argument("--plans-csv", help="CSV of in-force plans (all types merged)")
    args = ap.parse_args()

    data = parse_zchuyot(args.pdf)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"JSON saved to {args.json}")
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))

    if args.plans_csv:
        all_plans = (
            data["plans"]["in_force"]["local"]
            + data["plans"]["in_force"]["citywide"]
            + data["plans"]["in_force"]["national_regional"]
            + data["plans"]["in_force"]["architectural"]
        )
        fields = ["plan_number", "name", "deposit_date", "effective_date", "urls"]
        # stringify urls
        for p in all_plans:
            if "urls" in p and isinstance(p["urls"], list):
                p["urls"] = " | ".join(p["urls"])
        dump_csv(args.plans_csv, all_plans, fields)
        print(f"Plans CSV saved to {args.plans_csv}")


if __name__ == "__main__":  # pragma: no cover - script entry
    main()