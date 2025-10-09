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
  python parse_zchuyot_oop.py file.pdf --json out.json --plans-csv plans.csv
"""

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
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


# ---------- utilities ----------
class TextNormalizer:
    """Utility class for text normalization operations."""
    WS = re.compile(r"[ \t\u200e\u200f]+")
    MULTI_NL = re.compile(r"\n{2,}")

    @classmethod
    def normalize(cls, text: str) -> str:
        """Normalize text by removing special characters and whitespace."""
        if not text:
            return ""
        text = text.replace("\u200e", "").replace("\u200f", "")
        text = cls.WS.sub(" ", text)
        return text.strip()

    @classmethod
    def normalize_multiline(cls, text: str) -> str:
        """Normalize multiline text by reducing multiple newlines."""
        return cls.MULTI_NL.sub("\n", text)


class DateParser:
    """Utility class for date parsing operations."""
    @staticmethod
    def try_parse_date(date_str: str) -> Optional[str]:
        """Try to parse a date string into ISO format."""
        if not date_str:
            return None
        s = date_str.strip().replace(".", "-").replace("/", "-")
        try:
            return dateparser.parse(s, dayfirst=True, fuzzy=True).strftime("%Y-%m-%d")
        except Exception:
            return None


class PatternMatcher:
    """Utility class for pattern matching operations."""
    @staticmethod
    def find_first(patterns: List[str], text: str, date: bool = False) -> Optional[str]:
        """Find first match from a list of patterns."""
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = TextNormalizer.normalize(match.group(1))
                if date:
                    return DateParser.try_parse_date(value) or value
                return value
        return None

    @staticmethod
    def safe_int(value: Optional[str]) -> Optional[int]:
        """Safely convert string to integer."""
        try:
            return int(value) if value and value.isdigit() else None
        except Exception:
            return None

    @staticmethod
    def find_all_urls(text: str) -> List[str]:
        """Find all URLs in text."""
        urls = re.findall(r"https?://[^\s]+", text)
        clean_urls = []
        seen = set()
        for url in urls:
            url = url.rstrip(").,;]>\u200e\u200f")
            if url not in seen:
                seen.add(url)
                clean_urls.append(url)
        return clean_urls


# ---------- extraction / splitting ----------
class TextExtractor:
    """Handles PDF text extraction with OCR fallback."""
    def __init__(self, ocr_available: bool = False):
        self.ocr_available = ocr_available and pytesseract is not None and Image is not None

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF with OCR fallback if needed."""
        text = self._extract_text_from_pdf(pdf_path)
        if len(TextNormalizer.normalize(text)) >= 80:
            return text
        if self.ocr_available:
            return self._extract_text_with_ocr(pdf_path)
        return text

    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        txt_pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text() or ""
                txt_pages.append(t)
        return TextNormalizer.normalize_multiline("\n".join(txt_pages))

    def _extract_text_with_ocr(self, pdf_path: str) -> str:
        ocr_results = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                image = page.to_image(resolution=300).original
                if not isinstance(image, Image.Image):
                    image = Image.fromarray(image)
                ocr_text = pytesseract.image_to_string(image, lang="heb+eng")
                ocr_results.append(ocr_text)
        return "\n".join(ocr_results)


class SectionSplitter:
    """Handles splitting of document into sections."""
    SECTION_MARKERS = [
        ("alerts",       r"\nהתראות\b"),
        ("plans_local",  r"\nבתוקף\s+מקומיות\s+תכניות\b"),
        ("plans_city",   r"\nבתוקף\s+עירוניות\s+כלל\b"),
        ("plans_natreg", r"\nבתוקף\s+ומחוזיות\s+ארציות\s+מתאר\s+תכניות\b"),
        ("plans_arch",   r"\nארכיטקטוני\s+ועיצוב\s+בינוי\s+תוכניות\b"),
        ("in_planning_city", r"\nבתכנון\s+עירוניות\s+כלל\b"),
        ("in_planning_natreg", r"\nבתכנון\s+ומחוזיות\s+ארציות\s+מתאר\s+תכניות\b"),
        ("policy",       r"\nמדיניות\s+תכנונית\b"),
        ("land_use",     r"\nקרקע\s+יעוד\b"),
        ("rights",       r"\nפירוט\s+זכויות\b"),
        ("permit_terms", r"\nבניה\s+היתר\s+למתן\s+תנאי\b"),
        ("links",        r"\nhttps?://"),
    ]

    def split_sections(self, text: str) -> Dict[str, str]:
        indices = []
        for name, pattern in self.SECTION_MARKERS:
            match = re.search(pattern, text, re.S)
            if match:
                indices.append((name, match.start()))
        indices.sort(key=lambda x: x[1])

        sections = {}
        for i, (name, pos) in enumerate(indices):
            end = indices[i + 1][1] if i + 1 < len(indices) else len(text)
            sections[name] = text[pos:end]
        return sections


# ---------- header, alerts, plans, policy ----------
class HeaderParser:
    """Parses document header information."""
    def parse(self, text: str) -> Dict[str, Any]:
        header = {
            "issue_date": None,
            "address": None,
            "block": None,
            "parcel": None,
            "parcel_area_sqm": None,
        }

        # תאריך הפקה
        header["issue_date"] = PatternMatcher.find_first(
            [r"(?:(?:תאריך|תאריך הפקה)\s*[:\-]?\s*)([0-9./ -]{6,})"],
            text,
            date=True,
        )

        # כתובת (strip common OCR junk/backticks/parentheticals)
        addr = PatternMatcher.find_first(
            [r"(?:רחוב|כתובת)\s*[:\-]?\s*([^\n]+)"], text
        )
        if addr:
            addr = re.sub(r"[`'\"“”]", "", addr)
            addr = re.sub(r"\(.*?\)$", "", addr).strip(" -:,")
        header["address"] = addr or None

        # גוש/חלקה
        block = PatternMatcher.find_first([r"גוש\s*[:\-]?\s*(\d{1,6})"], text)
        parcel = PatternMatcher.find_first([r"חלקה\s*[:\-]?\s*(\d{1,6})"], text)
        header["block"] = PatternMatcher.safe_int(block)
        header["parcel"] = PatternMatcher.safe_int(parcel)

        # שטח חלקה/מגרש (try a couple of variants)
        area = PatternMatcher.find_first(
            [
                r"(?:שטח\s*(?:מגרש|חלקה|לחישוב|מר')\s*[:\- ]*)([\d,\.]+)",
                r"שטח\s*(?:מגרש|חלקה)\s*[:\- ]*([\d,\.]+)\s*(?:מ[\"״']?ר)?",
            ],
            text,
        )
        if area:
            try:
                header["parcel_area_sqm"] = float(area.replace(",", ""))
            except Exception:
                pass

        return header


class AlertsParser:
    """Parses alerts section."""
    def parse(self, text: str) -> List[str]:
        lines = [TextNormalizer.normalize(line) for line in text.splitlines()]
        alerts = []
        for line in lines:
            if not line:
                continue
            if any(t in line for t in ["התראה", "הגבלה", "עתיקות", "ארכיאולוג", "גובה", "מעניקה"]):
                alerts.append(line)
        # dedupe
        seen, out = set(), []
        for a in alerts:
            if a not in seen:
                seen.add(a)
                out.append(a)
        return out


class PlansParser:
    """Parses plans sections."""
    DATE_PATTERN = r"(?:[0-3]?\d/[01]?\d/\d{4})"

    def parse_plans_block(self, text: str) -> List[Dict[str, Any]]:
        lines = [TextNormalizer.normalize(line) for line in text.splitlines() if TextNormalizer.normalize(line)]
        plans = []
        for line in lines:
            p = self._parse_plan_line(line)
            if p:
                plans.append(p)
        return self._dedupe_plans(plans)

    def _parse_plan_line(self, line: str) -> Optional[Dict[str, Any]]:
        mnum = re.search(r"((?:\d{3,6}(?:/\d+)*)(?:/[א-ת]\d*)?(?:/\d+)*)", line)
        if not mnum:
            return None
        plan_number = mnum.group(1)

        dates = re.findall(self.DATE_PATTERN, line)
        deposit = DateParser.try_parse_date(dates[0]) if dates else None
        effective = DateParser.try_parse_date(dates[1]) if len(dates) > 1 else None

        name = line.replace(plan_number, "").strip()
        for d in dates:
            name = name.replace(d, "").strip()
        name = re.sub(r"(?:תוכנית|שם|הפקדה|מתן|תוקף|ילקוט`?מס|פרסומים|מס`?)", "", name).strip(" -:;,")

        return {
            "plan_number": plan_number or None,
            "name": name or None,
            "deposit_date": deposit,
            "effective_date": effective,
        }

    def _dedupe_plans(self, plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        out = []
        for p in plans:
            key = (p.get("plan_number"), p.get("deposit_date"), p.get("effective_date"), p.get("name"))
            if key not in seen:
                seen.add(key)
                out.append(p)
        return out


class PolicyParser:
    """Parses policy documents section."""
    DATE_PATTERN = r"(?:[0-3]?\d/[01]?\d/\d{4})"

    def parse(self, text: str) -> List[Dict[str, Any]]:
        out = []
        lines = [TextNormalizer.normalize(line) for line in text.splitlines() if TextNormalizer.normalize(line)]
        for L in lines:
            pol = self._parse_policy_line(L)
            if pol:
                out.append(pol)
        return out

    def _parse_policy_line(self, line: str) -> Optional[Dict[str, Any]]:
        mnum = re.search(r"\b(9\d{3}|8\d{3})\b", line)  # many policy ids 8000-9000+
        dates = re.findall(self.DATE_PATTERN, line)
        name = line
        if mnum:
            name = name.replace(mnum.group(0), "").strip()
        for d in dates:
            name = name.replace(d, "").strip()
        if mnum or dates or name:
            return {
                "policy_number": mnum.group(0) if mnum else None,
                "name": name or None,
                "date": DateParser.try_parse_date(dates[0]) if dates else None,
            }
        return None


# ---------- rights ----------
class RightsParser:
    """Parses building rights and privileges."""
    def parse_rights(self, text: str) -> Dict[str, Any]:
        rights = {"notes": []}
        lines = [TextNormalizer.normalize(line) for line in text.splitlines() if TextNormalizer.normalize(line)]

        for line in lines:
            # original quick capture (kept)
            self._parse_line_for_rights(line, rights)
            # detailed capture inside the section (added for parity/robustness)
            self._parse_building_lines(line, rights)
            self._parse_floor_percentages(line, rights)
            self._parse_minmax_values(line, rights)
            self._parse_dwelling_units(line, rights)
            self._parse_floors(line, rights)
            self._parse_coverage(line, rights)
            self._parse_parking(line, rights)
            self._parse_auxiliary_building(line, rights)

        # de-dupe referred plans
        if "referred_plans" in rights:
            rights["referred_plans"] = sorted(list(set(rights["referred_plans"])))
        return rights

    def parse_privilege_table_directly(self, text: str) -> Dict[str, Any]:
        """Parse privilege table structure directly from raw text."""
        rights: Dict[str, Any] = {}
        for raw in text.split("\n"):
            line = TextNormalizer.normalize(raw)
            if not line:
                continue
            self._parse_building_lines(line, rights)
            self._parse_floor_percentages(line, rights)
            self._parse_minmax_values(line, rights)
            self._parse_dwelling_units(line, rights)
            self._parse_floors(line, rights)
            self._parse_coverage(line, rights)
            self._parse_parking(line, rights)
            self._parse_auxiliary_building(line, rights)
        return rights

    # ---- helpers for rights ----
    def _parse_line_for_rights(self, line: str, rights: Dict[str, Any]) -> None:
        if any(w in line for w in ["קו", "בניין", "קו בניין"]):
            rights.setdefault("building_lines", []).append(line)
        if "`מ" in line and "ןיינבוק" in line:
            rights.setdefault("building_lines", []).append(line)

        if re.search(r"(?:מספר\s+קומות|קומות\s*מספר)", line):
            m = re.search(r"(\d+)\s*קומות", line)
            if m:
                rights["number_of_floors"] = int(m.group(1))
            rights["floors_note"] = line

        # coverage (specific)
        for pat in [
            r"אחוז\s+משטח\s+מגרש\s*(\d+)\s*%",
            r"(\d+)\s*%\s*אחוז\s+משטח\s+מגרש",
            r"אחוז\s+בנייה\s*(\d+)\s*%",
            r"(\d+)\s*%\s*אחוז\s+בנייה",
        ]:
            m = re.search(pat, line)
            if m:
                rights["building_coverage_percentage"] = int(m.group(1))
                break

        # plan refs
        plan_refs = re.findall(r"\b(\d{3,6})\b", line)
        if plan_refs:
            rights.setdefault("referred_plans", []).extend(plan_refs)

        rights.setdefault("notes", []).append({"text": line, "type": "general"})

    def _parse_building_lines(self, line: str, rights: Dict[str, Any]) -> None:
        pats = [
            r"(\d+)\s*מטרים?\s*קו\s+בניין\s+(צדדי|אחורי|חזית)",
            r"(\d+)\s*(\d+)\s*ידדצןיינבוק",  # OCR: side building line
            r"(\d+)\s*ירוחא\s*ןיינב\s*וק",   # OCR: rear building line
        ]
        for pat in pats:
            m = re.search(pat, line)
            if m and len(m.groups()) == 2:
                distance = int(m.group(1))
                line_type = m.group(2)
                if line_type in ["צדדי", "1", "2"]:
                    line_type = "צדדי"
                elif line_type in ["אחורי", "ירוחא"]:
                    line_type = "אחורי"
                elif line_type in ["חזית"]:
                    line_type = "חזית"
                rights.setdefault("building_lines_detailed", []).append(
                    {"type": line_type, "distance_meters": distance, "raw_text": line}
                )
                break

    def _parse_floor_percentages(self, line: str, rights: Dict[str, Any]) -> None:
        # Adds variants without the % sign but with “אחוז/אחוזים”
        pats = [
            r"(\d+)\s*%\s*(טיפוסית|שנייה|ראשונה|שלישית)",
            r"(\d+)\s*תיסופיט",
            r"(\d+)\s*הינש",
            r"(\d+)\s*(?:אחוז(?:ים)?)\s*(טיפוסית|שנייה|ראשונה|שלישית)",     # NEW
            r"קומה\s+(טיפוסית|שנייה|ראשונה|שלישית)\s+(\d+)\s*(?:אחוז(?:ים)?)",  # NEW
        ]
        for pat in pats:
            m = re.search(pat, line)
            if m:
                percent = int(m.group(1))
                if "תיסופיט" in line:
                    floor_type = "טיפוסית"
                elif "הינש" in line:
                    floor_type = "שנייה"
                elif len(m.groups()) > 1 and not m.group(2).isdigit():
                    floor_type = m.group(2)
                else:
                    # groups order differs across patterns; try best-effort
                    floor_type = m.group(2) if len(m.groups()) > 1 and not m.group(2).isdigit() else "טיפוסית"
                rights.setdefault("floor_percentages_detailed", []).append(
                    {"type": floor_type, "percentage": percent, "raw_text": line}
                )
                break

    def _parse_minmax_values(self, line: str, rights: Dict[str, Any]) -> None:
        pats = [
            r"(\d+)\s*(מינימום|מקסימום)",
            r"(\d+)\s*(םומינימ|םומיסקמ)",
            r"(\d+)\s*(םינימום|םקסימום)",
        ]
        for pat in pats:
            m = re.search(pat, line)
            if m:
                value = int(m.group(1))
                kind = m.group(2)
                if kind in ["מינימום", "םומינימ", "םינימום"]:
                    rights.setdefault("minimum_values", []).append({"value": value, "raw_text": line})
                elif kind in ["מקסימום", "םומיסקמ", "םקסימום"]:
                    rights.setdefault("maximum_values", []).append({"value": value, "raw_text": line})
                break

    def _parse_dwelling_units(self, line: str, rights: Dict[str, Any]) -> None:
        pats = [
            r"(\d+)\s*יחידות?\s+דיור",
            r"יחידות?\s+דיור\s*(\d+)",
            r"מספר\s+יחידות\s+דיור\s*(\d+)",
            r"(\d+)\s*מספר\s+יחידות\s+דיור",
        ]
        for pat in pats:
            m = re.search(pat, line)
            if m:
                units = int(m.group(1) or (m.group(2) if len(m.groups()) > 1 else 0))
                rights["dwelling_units"] = units
                break

    def _parse_floors(self, line: str, rights: Dict[str, Any]) -> None:
        pats = [
            r"(\d+)\s*קומות",
            r"קומות\s*(\d+)",
            r"מספר\s+קומות\s*(\d+)",
            r"(\d+)\s*מספר\s+קומות",
        ]
        for pat in pats:
            m = re.search(pat, line)
            if m:
                floors = int(m.group(1) or (m.group(2) if len(m.groups()) > 1 else 0))
                rights["number_of_floors"] = floors
                break

    def _parse_coverage(self, line: str, rights: Dict[str, Any]) -> None:
        pats = [
            r"(\d+)\s*%\s*אחוז\s+משטח\s+מגרש",
            r"(\d+)\s*%\s*אחוז\s+בנייה",
        ]
        for pat in pats:
            m = re.search(pat, line)
            if m:
                rights["building_coverage_percentage"] = int(m.group(1))
                break

    def _parse_parking(self, line: str, rights: Dict[str, Any]) -> None:
        pats = [
            r"(\d+)\s*מותר\s+חניה",
            r"(\d+)\s*רתומ\s+הינח",
        ]
        for pat in pats:
            m = re.search(pat, line)
            if m:
                rights.setdefault("parking_requirements", []).append(
                    {"value": int(m.group(1)), "raw_text": line}
                )
                break

    def _parse_auxiliary_building(self, line: str, rights: Dict[str, Any]) -> None:
        m = re.search(r"(\d+)\s*רזעהנבמ", line)
        if m:
            rights["auxiliary_building_area"] = int(m.group(1))


# ---------- HTML dropdown parser ----------
class HTMLPrivilegePageParser:
    """Parses HTML privilege pages."""
    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        parcels: List[Dict[str, Any]] = []
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            opts_match = re.search(r"is_opts\s*=\s*'([^']+)'", html_content)
            if opts_match:
                opts_html = opts_match.group(1).replace("`", '"')
                opts_soup = BeautifulSoup(opts_html, "html.parser")
                for option in opts_soup.find_all("option"):
                    p = self._parse_option(option)
                    if p:
                        parcels.append(p)

            if not parcels:
                for option in soup.find_all("option"):
                    p = self._parse_option(option)
                    if p:
                        parcels.append(p)
        except Exception as e:
            print(f"Error parsing HTML privilege page: {e}")
        return parcels

    def _parse_option(self, option) -> Optional[Dict[str, Any]]:
        value = option.get("value", "")
        text = option.get_text(strip=True)
        if not value or not text or "block=" not in value:
            return None

        params: Dict[str, str] = {}
        for param in value.split("&"):
            if "=" in param:
                k, v = param.split("=", 1)
                params[k] = v

        parcel_info: Dict[str, Any] = {
            "block": params.get("block"),
            "parcel": params.get("parcel"),
            "status": params.get("status"),
            "street": params.get("street"),
            "house": params.get("house"),
            "chasum": params.get("chasum"),
            "raw_text": text,
            "parcel_number": None,
            "parcel_status": None,
            "street_name": None,
            "house_number": None,
            "land_use": None,
            "area": None,
        }
        self._extract_parcel_details(text, parcel_info)
        return parcel_info

    def _extract_parcel_details(self, text: str, parcel_info: Dict[str, Any]) -> None:
        m = re.search(r"מגרש:\s*(\d+)", text)
        if m:
            parcel_info["parcel_number"] = m.group(1)
        m = re.search(r"(\w+)\s*-\s*", text)
        if m:
            parcel_info["parcel_status"] = m.group(1)
        m = re.search(r"-\s*([^(]+?)\s*\(", text)
        if m:
            parcel_info["street_name"] = m.group(1).strip()
        m = re.search(r"מס.?\s*(\d+)", text)
        if m:
            parcel_info["house_number"] = m.group(1)
        det = re.search(r"\(([^)]+)\)", text)
        if det:
            details = det.group(1)
            m = re.search(r"יעוד קרקע:\s*([^\n]+)", details)
            if m:
                parcel_info["land_use"] = m.group(1).split("שטח")[0].strip()
            m = re.search(r"שטח:\s*([\d,\.]+)", details)
            if m:
                parcel_info["area"] = m.group(1).strip()


# ---------- main orchestrator ----------
class ZchuyotParser:
    """Main parser class that orchestrates the parsing process."""
    def __init__(self, ocr_available: bool = False):
        self.text_extractor = TextExtractor(ocr_available)
        self.section_splitter = SectionSplitter()
        self.header_parser = HeaderParser()
        self.alerts_parser = AlertsParser()
        self.plans_parser = PlansParser()
        self.rights_parser = RightsParser()
        self.policy_parser = PolicyParser()
        self.html_parser = HTMLPrivilegePageParser()

    def parse(self, pdf_path: str) -> Dict[str, Any]:
        text = self.text_extractor.extract_text(pdf_path)
        text = TextNormalizer.normalize(text)

        # basic header
        basic_info = self.header_parser.parse(text)

        # sections
        sections = self.section_splitter.split_sections(text)

        # urls
        all_urls = PatternMatcher.find_all_urls(text)

        # plans
        plans_data = self._parse_plans(sections)

        # alerts
        alerts = self.alerts_parser.parse(sections.get("alerts", ""))

        # policy
        policy = self.policy_parser.parse(sections.get("policy", ""))

        # rights (section + doc-wide)
        rights = self.rights_parser.parse_rights(
            sections.get("rights", "") + "\n" + sections.get("permit_terms", "")
        )
        direct_rights = self.rights_parser.parse_privilege_table_directly(text)
        rights = self._merge_rights_data(rights, direct_rights)

        # attach urls to plans
        plans_data = self._attach_urls_to_plans(plans_data, all_urls)

        result = {
            "source_file": os.path.abspath(pdf_path),
            "extracted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "basic": basic_info,
            "alerts": alerts,
            "plans": plans_data,
            "policy": policy,
            "rights": rights,
            "all_links": all_urls,
            "raw_preview": text[:2000],
        }
        return result

    def _parse_plans(self, sections: Dict[str, str]) -> Dict[str, Any]:
        return {
            "in_force": {
                "local": self.plans_parser.parse_plans_block(sections.get("plans_local", "")),
                "citywide": self.plans_parser.parse_plans_block(sections.get("plans_city", "")),
                "national_regional": self.plans_parser.parse_plans_block(sections.get("plans_natreg", "")),
                "architectural": self.plans_parser.parse_plans_block(sections.get("plans_arch", "")),
            },
            "in_planning": {
                "citywide": self.plans_parser.parse_plans_block(sections.get("in_planning_city", "")),
                "national_regional": self.plans_parser.parse_plans_block(sections.get("in_planning_natreg", "")),
            },
        }

    def _merge_rights_data(self, rights: Dict[str, Any], direct_rights: Dict[str, Any]) -> Dict[str, Any]:
        for key, value in direct_rights.items():
            if key in rights:
                if isinstance(value, list) and isinstance(rights[key], list):
                    rights[key].extend(value)
                elif isinstance(value, dict) and isinstance(rights[key], dict):
                    rights[key].update(value)
                else:
                    rights[key] = value
            else:
                rights[key] = value
        return rights

    def _attach_urls_to_plans(self, plans_data: Dict[str, Any], all_urls: List[str]) -> Dict[str, Any]:
        for category in plans_data.values():
            if isinstance(category, dict):
                for plan_list in category.values():
                    if not isinstance(plan_list, list):
                        continue
                    for plan in plan_list:
                        pn = plan.get("plan_number", "") or ""
                        p_urls = [u for u in all_urls if pn and pn in u]
                        if p_urls:
                            # de-dupe
                            seen, uu = set(), []
                            for u in p_urls:
                                if u not in seen:
                                    seen.add(u)
                                    uu.append(u)
                            plan["urls"] = uu
        return plans_data


# ---------- export ----------
class CSVExporter:
    """Handles CSV export functionality (without mutating parsed data)."""
    @staticmethod
    def export_plans_csv(plans_data: Dict[str, Any], output_path: str) -> None:
        all_plans = (
            plans_data["in_force"]["local"]
            + plans_data["in_force"]["citywide"]
            + plans_data["in_force"]["national_regional"]
            + plans_data["in_force"]["architectural"]
        )
        fields = ["plan_number", "name", "deposit_date", "effective_date", "urls"]

        # create rows without mutating input
        rows: List[Dict[str, Any]] = []
        for p in all_plans:
            row = {k: p.get(k) for k in fields}
            if isinstance(row.get("urls"), list):
                row["urls"] = " | ".join(row["urls"])
            rows.append(row)

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows)


# ---------- compatibility functions ----------
def parse_zchuyot(pdf_path: str) -> Dict[str, Any]:
    """Parse a Zchuyot PDF file - compatibility wrapper for the new OOP parser."""
    parser = ZchuyotParser(ocr_available=True)
    return parser.parse(pdf_path)


def parse_html_privilege_page(html_content: str) -> List[Dict[str, Any]]:
    """Parse HTML privilege page - compatibility wrapper for the new OOP parser."""
    parser = HTMLPrivilegePageParser()
    return parser.parse(html_content)


# ---------- CLI ----------
def main():
    parser = argparse.ArgumentParser(description="Parse Tel-Aviv Zchuyot PDF → JSON")
    parser.add_argument("pdf", help="path to PDF")
    parser.add_argument("--json", help="output JSON file")
    parser.add_argument("--plans-csv", help="CSV of in-force plans (all types merged)")
    args = parser.parse_args()

    try:
        zchuyot_parser = ZchuyotParser(ocr_available=True)
        data = zchuyot_parser.parse(args.pdf)

        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"JSON saved to {args.json}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))

        if args.plans_csv:
            CSVExporter.export_plans_csv(data["plans"], args.plans_csv)
            print(f"Plans CSV saved to {args.plans_csv}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
