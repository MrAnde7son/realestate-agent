# -*- coding: utf-8 -*-
"""
Parse Tel-Aviv "Zchuyot" (rights) PDF -> structured JSON for MCP server.

Extracts:
- header: issue_date, address, gush/helka, parcel area (if present)
- alerts (התראות)
- plans in force: local / citywide / national-regional (+ in planning if present)
- policy docs (מדיניות תכנונית)
- rights details (זכויות/קווי בניין/אחוזים) when recognizable
- all hyperlinks to plan docs and maps

Usage:
  python parse_zchuyot.py file.pdf --json out.json --plans-csv plans.csv
"""

import os
import re
import json
import argparse
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dateutil import parser as dateparser
import pdfplumber
from bs4 import BeautifulSoup
import csv

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
        "gush": None,
        "helka": None,
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
    out["gush"] = safe_int(g)
    out["helka"] = safe_int(h)

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
    Try to capture common rights snippets:
    - building lines (קו בניין צדדי/אחורי/חזית)
    - number of floors (מספר קומות)
    - percent (%/אחוז בנייה)
    - references to a plan number in text
    """
    rights = {"notes": []}
    lines = [norm(l) for l in block.splitlines() if norm(l)]
    for L in lines:
        if "קו" in L and "בניין" in L:
            rights.setdefault("building_lines", []).append(L)
        if re.search(r"(?:מספר\s+קומות|קומות\s*מספר)", L):
            rights["floors_note"] = L
        m = re.search(r"(\d{2,3})\s*%(?:\s*בנ(?:י|י)ה)?", L)
        if m:
            rights["percent_building"] = int(m.group(1))
        # plan refs inline (e.g., "ראה 738")
        pref = re.findall(r"\b(\d{3,6})\b", L)
        if pref:
            rights.setdefault("referred_plans", set()).update(pref)
        rights["notes"].append(L)
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
                    # Format: gush=6632&helka=3200&status=0&street=4844&house=0&chasum=0&
                    params = {}
                    for param in value.split('&'):
                        if '=' in param:
                            key, val = param.split('=', 1)
                            params[key] = val
                    
                    # Extract parcel details from text
                    # Format: מגרש: 3200 מוסדר  -  רחוב קדושי השואה  (יעוד קרקע: אזור תעסוקה שטח: 12826.81 מ``ר)
                    parcel_info = {
                        'gush': params.get('gush'),
                        'helka': params.get('helka'),
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
                
                if value and text and 'gush=' in value:
                    # Parse the value string
                    params = {}
                    for param in value.split('&'):
                        if '=' in param:
                            key, val = param.split('=', 1)
                            params[key] = val
                    
                    parcel_info = {
                        'gush': params.get('gush'),
                        'helka': params.get('helka'),
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