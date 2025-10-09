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
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

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
        
        date_str = date_str.strip().replace(".", "-").replace("/", "-")
        try:
            return dateparser.parse(date_str, dayfirst=True, fuzzy=True).strftime("%Y-%m-%d")
        except Exception:
            return None


class TextExtractor:
    """Handles PDF text extraction with OCR fallback."""
    
    def __init__(self, ocr_available: bool = False):
        self.ocr_available = ocr_available and pytesseract is not None and Image is not None
    
    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF with OCR fallback if needed."""
        try:
            text = self._extract_text_from_pdf(pdf_path)
            if len(TextNormalizer.normalize(text)) >= 80:
                return text
            
            if self.ocr_available:
                return self._extract_text_with_ocr(pdf_path)
            
            return text
        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}")
    
    def _extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text directly from PDF."""
        txt_pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                txt_pages.append(text)
        
        return TextNormalizer.normalize_multiline("\n".join(txt_pages))
    
    def _extract_text_with_ocr(self, pdf_path: str) -> str:
        """Extract text using OCR for image-based PDFs."""
        ocr_results = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                image = page.to_image(resolution=300).original
                if not isinstance(image, Image.Image):
                    image = Image.fromarray(image)
                ocr_text = pytesseract.image_to_string(image, lang="heb+eng")
                ocr_results.append(ocr_text)
        
        return "\n".join(ocr_results)


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
        """Split text into sections based on markers."""
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


class HeaderParser:
    """Parses document header information."""
    
    def parse(self, text: str) -> Dict[str, Any]:
        """Parse header information from text."""
        header = {
            "issue_date": None,
            "address": None,
            "block": None,
            "parcel": None,
            "parcel_area_sqm": None,
        }
        
        # תאריך הפקה
        header["issue_date"] = PatternMatcher.find_first([
            r"(?:(?:תאריך|תאריך הפקה)\s*[:\-]?\s*)([0-9./ -]{6,})"
        ], text, date=True)
        
        # כתובת (משתנה בין פורמטים)
        header["address"] = PatternMatcher.find_first([
            r"(?:רחוב|כתובת)\s*[:\-]?\s*([^\n]+)"
        ], text)
        
        # גוש/חלקה
        block = PatternMatcher.find_first([r"גוש\s*[:\-]?\s*(\d{1,6})"], text)
        parcel = PatternMatcher.find_first([r"חלקה\s*[:\-]?\s*(\d{1,6})"], text)
        header["block"] = PatternMatcher.safe_int(block)
        header["parcel"] = PatternMatcher.safe_int(parcel)
        
        # שטח חלקה/מגרש (אם קיים)
        area = PatternMatcher.find_first([
            r"(?:שטח\s*(?:מגרש|חלקה|לחישוב|מר')\s*[:\- ]*)([\d,\.]+)"
        ], text)
        
        if area:
            try:
                header["parcel_area_sqm"] = float(area.replace(",", ""))
            except Exception:
                pass
        
        return header


class AlertsParser:
    """Parses alerts section."""
    
    def parse(self, text: str) -> List[str]:
        """Parse alerts from text."""
        lines = [TextNormalizer.normalize(line) for line in text.splitlines()]
        alerts = []
        
        for line in lines:
            if not line:
                continue
            
            if any(token in line for token in ["התראה", "הגבלה", "עתיקות", "ארכיאולוג", "גובה", "מעניקה"]):
                alerts.append(line)
        
        # Deduplicate
        seen = set()
        unique_alerts = []
        for alert in alerts:
            if alert not in seen:
                seen.add(alert)
                unique_alerts.append(alert)
        
        return unique_alerts


class PlansParser:
    """Parses plans sections."""
    
    DATE_PATTERN = r"(?:[0-3]?\d/[01]?\d/\d{4})"
    
    def parse_plans_block(self, text: str) -> List[Dict[str, Any]]:
        """Parse a block of plans."""
        lines = [TextNormalizer.normalize(line) for line in text.splitlines() if TextNormalizer.normalize(line)]
        plans = []
        
        for line in lines:
            plan = self._parse_plan_line(line)
            if plan:
                plans.append(plan)
        
        return self._dedupe_plans(plans)
    
    def _parse_plan_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single plan line."""
        # Plan number (supports complex forms with Hebrew letters)
        plan_match = re.search(r"((?:\d{3,6}(?:/\d+)*)(?:/[א-ת]\d*)?(?:/\d+)*)", line)
        if not plan_match:
            return None
        
        plan_number = plan_match.group(1)
        
        # Extract dates
        dates = re.findall(self.DATE_PATTERN, line)
        deposit_date = DateParser.try_parse_date(dates[0]) if dates else None
        effective_date = DateParser.try_parse_date(dates[1]) if len(dates) > 1 else None
        
        # Extract name
        name = line
        name = name.replace(plan_number, "").strip()
        for date in dates:
            name = name.replace(date, "").strip()
        
        name = re.sub(r"(?:תוכנית|שם|הפקדה|מתן|תוקף|ילקוט`?מס|פרסומים|מס`?)", "", name).strip(" -:;,")
        
        return {
            "plan_number": plan_number or None,
            "name": name or None,
            "deposit_date": deposit_date,
            "effective_date": effective_date,
        }
    
    def _dedupe_plans(self, plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate plans."""
        seen = set()
        unique_plans = []
        
        for plan in plans:
            key = (
                plan.get("plan_number"),
                plan.get("deposit_date"),
                plan.get("effective_date"),
                plan.get("name")
            )
            if key not in seen:
                seen.add(key)
                unique_plans.append(plan)
        
        return unique_plans


class RightsParser:
    """Parses building rights and privileges."""
    
    def __init__(self):
        self.pattern_matcher = PatternMatcher()
    
    def parse_rights(self, text: str) -> Dict[str, Any]:
        """Parse building rights from text."""
        rights = {"notes": []}
        lines = [TextNormalizer.normalize(line) for line in text.splitlines() if TextNormalizer.normalize(line)]
        
        for line in lines:
            self._parse_line_for_rights(line, rights)
        
        # Dedupe referred_plans
        if "referred_plans" in rights:
            rights["referred_plans"] = sorted(list(set(rights["referred_plans"])))
        
        return rights
    
    def parse_privilege_table_directly(self, text: str) -> Dict[str, Any]:
        """Parse privilege table structure directly from raw text."""
        rights = {}
        lines = text.split('\n')
        
        for line in lines:
            line = TextNormalizer.normalize(line)
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
    
    def _parse_line_for_rights(self, line: str, rights: Dict[str, Any]) -> None:
        """Parse a single line for various rights patterns."""
        # Building lines
        if any(word in line for word in ["קו", "בניין", "קו בניין"]):
            rights.setdefault("building_lines", []).append(line)
        
        if "`מ" in line and "ןיינבוק" in line:
            rights.setdefault("building_lines", []).append(line)
        
        # Floor information
        if re.search(r"(?:מספר\s+קומות|קומות\s*מספר)", line):
            floors_match = re.search(r"(\d+)\s*קומות", line)
            if floors_match:
                rights["number_of_floors"] = int(floors_match.group(1))
            rights["floors_note"] = line
        
        # Building coverage percentage
        coverage_patterns = [
            r"אחוז\s+משטח\s+מגרש\s*(\d+)\s*%",
            r"(\d+)\s*%\s*אחוז\s+משטח\s+מגרש",
            r"אחוז\s+בנייה\s*(\d+)\s*%",
            r"(\d+)\s*%\s*אחוז\s+בנייה"
        ]
        
        for pattern in coverage_patterns:
            match = re.search(pattern, line)
            if match:
                rights["building_coverage_percentage"] = int(match.group(1))
                break
        
        # Floor area percentages
        self._parse_floor_percentages(line, rights)
        
        # Plan references
        plan_refs = re.findall(r"\b(\d{3,6})\b", line)
        if plan_refs:
            rights.setdefault("referred_plans", []).extend(plan_refs)
        
        # Add note
        rights["notes"].append({"text": line, "type": "general"})
    
    def _parse_building_lines(self, line: str, rights: Dict[str, Any]) -> None:
        """Parse building lines from line."""
        building_line_patterns = [
            r"(\d+)\s*מטרים?\s*קו\s+בניין\s+(צדדי|אחורי|חזית)",
            r"(\d+)\s*(\d+)\s*ידדצןיינבוק",  # OCR: side building line
            r"(\d+)\s*ירוחא\s*ןיינב\s*וק"     # OCR: rear building line
        ]
        
        for pattern in building_line_patterns:
            match = re.search(pattern, line)
            if match and len(match.groups()) == 2:
                distance = int(match.group(1))
                line_type = match.group(2)
                
                if line_type in ["צדדי", "1", "2"]:
                    line_type = "צדדי"
                elif line_type in ["אחורי", "ירוחא"]:
                    line_type = "אחורי"
                elif line_type in ["חזית"]:
                    line_type = "חזית"
                
                rights.setdefault("building_lines_detailed", []).append({
                    "type": line_type,
                    "distance_meters": distance,
                    "raw_text": line
                })
                break
    
    def _parse_floor_percentages(self, line: str, rights: Dict[str, Any]) -> None:
        """Parse floor percentages from line."""
        floor_percent_patterns = [
            r"(\d+)\s*%\s*(טיפוסית|שנייה|ראשונה|שלישית)",
            r"(\d+)\s*תיסופיט",  # OCR: typical floor
            r"(\d+)\s*הינש"      # OCR: second floor
        ]
        
        for pattern in floor_percent_patterns:
            match = re.search(pattern, line)
            if match:
                percent = int(match.group(1))
                
                if "תיסופיט" in line:
                    floor_type = "טיפוסית"
                elif "הינש" in line:
                    floor_type = "שנייה"
                elif "ראשונה" in line:
                    floor_type = "ראשונה"
                elif "שלישית" in line:
                    floor_type = "שלישית"
                else:
                    floor_type = match.group(2) if len(match.groups()) > 1 else "טיפוסית"
                
                rights.setdefault("floor_percentages_detailed", []).append({
                    "type": floor_type,
                    "percentage": percent,
                    "raw_text": line
                })
                break
    
    def _parse_minmax_values(self, line: str, rights: Dict[str, Any]) -> None:
        """Parse minimum/maximum values from line."""
        minmax_patterns = [
            r"(\d+)\s*(מינימום|מקסימום)",
            r"(\d+)\s*(םומינימ|םומיסקמ)",  # OCR version
            r"(\d+)\s*(םינימום|םקסימום)"   # Alternative OCR version
        ]
        
        for pattern in minmax_patterns:
            match = re.search(pattern, line)
            if match:
                value = int(match.group(1))
                minmax_type = match.group(2)
                
                if minmax_type in ["מינימום", "םומינימ", "םינימום"]:
                    rights.setdefault("minimum_values", []).append({
                        "value": value,
                        "raw_text": line
                    })
                elif minmax_type in ["מקסימום", "םומיסקמ", "םקסימום"]:
                    rights.setdefault("maximum_values", []).append({
                        "value": value,
                        "raw_text": line
                    })
                break
    
    def _parse_dwelling_units(self, line: str, rights: Dict[str, Any]) -> None:
        """Parse dwelling units from line."""
        dwelling_patterns = [
            r"(\d+)\s*יחידות?\s+דיור",
            r"יחידות?\s+דיור\s*(\d+)",
            r"מספר\s+יחידות\s+דיור\s*(\d+)",
            r"(\d+)\s*מספר\s+יחידות\s+דיור"
        ]
        
        for pattern in dwelling_patterns:
            match = re.search(pattern, line)
            if match:
                units = int(match.group(1) or match.group(2))
                rights["dwelling_units"] = units
                break
    
    def _parse_floors(self, line: str, rights: Dict[str, Any]) -> None:
        """Parse number of floors from line."""
        floors_patterns = [
            r"(\d+)\s*קומות",
            r"קומות\s*(\d+)",
            r"מספר\s+קומות\s*(\d+)",
            r"(\d+)\s*מספר\s+קומות"
        ]
        
        for pattern in floors_patterns:
            match = re.search(pattern, line)
            if match:
                floors = int(match.group(1) or match.group(2))
                rights["number_of_floors"] = floors
                break
    
    def _parse_coverage(self, line: str, rights: Dict[str, Any]) -> None:
        """Parse building coverage percentage from line."""
        coverage_patterns = [
            r"(\d+)\s*%\s*אחוז\s+משטח\s+מגרש",
            r"(\d+)\s*%\s*אחוז\s+בנייה"
        ]
        
        for pattern in coverage_patterns:
            match = re.search(pattern, line)
            if match:
                rights["building_coverage_percentage"] = int(match.group(1))
                break
    
    def _parse_parking(self, line: str, rights: Dict[str, Any]) -> None:
        """Parse parking requirements from line."""
        parking_patterns = [
            r"(\d+)\s*מותר\s+חניה",
            r"(\d+)\s*רתומ\s+הינח"  # OCR version
        ]
        
        for pattern in parking_patterns:
            match = re.search(pattern, line)
            if match:
                parking_value = int(match.group(1))
                rights.setdefault("parking_requirements", []).append({
                    "value": parking_value,
                    "raw_text": line
                })
                break
    
    def _parse_auxiliary_building(self, line: str, rights: Dict[str, Any]) -> None:
        """Parse auxiliary building area from line."""
        aux_building_match = re.search(r"(\d+)\s*רזעהנבמ", line)
        if aux_building_match:
            area = int(aux_building_match.group(1))
            rights["auxiliary_building_area"] = area


class PolicyParser:
    """Parses policy documents section."""
    
    DATE_PATTERN = r"(?:[0-3]?\d/[01]?\d/\d{4})"
    
    def parse(self, text: str) -> List[Dict[str, Any]]:
        """Parse policy documents from text."""
        policies = []
        lines = [TextNormalizer.normalize(line) for line in text.splitlines() if TextNormalizer.normalize(line)]
        
        for line in lines:
            policy = self._parse_policy_line(line)
            if policy:
                policies.append(policy)
        
        return policies
    
    def _parse_policy_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single policy line."""
        policy_match = re.search(r"\b(9\d{3}|8\d{3})\b", line)
        dates = re.findall(self.DATE_PATTERN, line)
        
        name = line
        if policy_match:
            name = name.replace(policy_match.group(0), "").strip()
        
        for date in dates:
            name = name.replace(date, "").strip()
        
        if policy_match or dates or name:
            return {
                "policy_number": policy_match.group(0) if policy_match else None,
                "name": name or None,
                "date": DateParser.try_parse_date(dates[0]) if dates else None,
            }
        
        return None


class HTMLPrivilegePageParser:
    """Parses HTML privilege pages."""
    
    def parse(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse HTML privilege page and extract parcels."""
        parcels = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            opts_pattern = r"is_opts\s*=\s*'([^']+)'"
            opts_match = re.search(opts_pattern, html_content)
            
            if opts_match:
                opts_html = opts_match.group(1).replace('`', '"')
                opts_soup = BeautifulSoup(opts_html, 'html.parser')
                
                for option in opts_soup.find_all('option'):
                    parcel = self._parse_option(option)
                    if parcel:
                        parcels.append(parcel)
            
            # Fallback: direct option parsing
            if not parcels:
                options = soup.find_all('option')
                for option in options:
                    parcel = self._parse_option(option)
                    if parcel:
                        parcels.append(parcel)
            
            return parcels
            
        except Exception as e:
            print(f"Error parsing HTML privilege page: {e}")
            return []
    
    def _parse_option(self, option) -> Optional[Dict[str, Any]]:
        """Parse a single option element."""
        value = option.get('value', '')
        text = option.get_text(strip=True)
        
        if not value or not text or 'block=' not in value:
            return None
        
        # Parse parameters
        params = {}
        for param in value.split('&'):
            if '=' in param:
                key, val = param.split('=', 1)
                params[key] = val
        
        # Parse Hebrew text
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
        
        # Extract structured information
        self._extract_parcel_details(text, parcel_info)
        
        return parcel_info
    
    def _extract_parcel_details(self, text: str, parcel_info: Dict[str, Any]) -> None:
        """Extract detailed information from Hebrew text."""
        # Extract parcel number
        parcel_match = re.search(r'מגרש:\s*(\d+)', text)
        if parcel_match:
            parcel_info['parcel_number'] = parcel_match.group(1)
        
        # Extract status
        status_match = re.search(r'(\w+)\s*-\s*', text)
        if status_match:
            parcel_info['parcel_status'] = status_match.group(1)
        
        # Extract street name
        street_match = re.search(r'-\s*([^(]+?)\s*\(', text)
        if street_match:
            parcel_info['street_name'] = street_match.group(1).strip()
        
        # Extract house number
        house_match = re.search(r'מס.?\s*(\d+)', text)
        if house_match:
            parcel_info['house_number'] = house_match.group(1)
        
        # Extract land use and area
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
        """Parse a Zchuyot PDF file and return structured data."""
        try:
            # Extract text
            text = self.text_extractor.extract_text(pdf_path)
            text = TextNormalizer.normalize(text)
            
            # Parse basic information
            basic_info = self.header_parser.parse(text)
            
            # Split into sections
            sections = self.section_splitter.split_sections(text)
            
            # Extract URLs
            all_urls = PatternMatcher.find_all_urls(text)
            
            # Parse plans
            plans_data = self._parse_plans(sections)
            
            # Parse alerts
            alerts = self.alerts_parser.parse(sections.get("alerts", ""))
            
            # Parse policy
            policy = self.policy_parser.parse(sections.get("policy", ""))
            
            # Parse rights
            rights = self.rights_parser.parse_rights(
                sections.get("rights", "") + "\n" + sections.get("permit_terms", "")
            )
            
            # Parse privilege table directly
            direct_rights = self.rights_parser.parse_privilege_table_directly(text)
            
            # Merge rights data
            rights = self._merge_rights_data(rights, direct_rights)
            
            # Attach URLs to plans
            plans_data = self._attach_urls_to_plans(plans_data, all_urls)
            
            # Build result
            result = {
                "source_file": os.path.abspath(pdf_path),
                "extracted_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "basic": basic_info,
                "alerts": alerts,
                "plans": plans_data,
                "policy": policy,
                "rights": rights,
                "all_links": all_urls,
                "raw_preview": text[:2000],
            }
            
            return result
            
        except Exception as e:
            raise RuntimeError(f"Failed to parse PDF: {e}")
    
    def _parse_plans(self, sections: Dict[str, str]) -> Dict[str, Any]:
        """Parse all plan sections."""
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
        """Merge direct parsing results with section-based parsing."""
        for key, value in direct_rights.items():
            if key in rights:
                if isinstance(value, list) and isinstance(rights[key], list):
                    rights[key].extend(value)
                elif isinstance(value, dict) and isinstance(rights[key], dict):
                    rights[key].update(value)
                else:
                    rights[key] = value  # Override with direct parsing result
            else:
                rights[key] = value
        
        return rights
    
    def _attach_urls_to_plans(self, plans_data: Dict[str, Any], all_urls: List[str]) -> Dict[str, Any]:
        """Attach URLs to plans based on plan numbers."""
        for plan_category in plans_data.values():
            if isinstance(plan_category, dict):
                for plan_list in plan_category.values():
                    if isinstance(plan_list, list):
                        for plan in plan_list:
                            plan_urls = []
                            plan_number = plan.get("plan_number", "")
                            
                            for url in all_urls:
                                if plan_number and plan_number in url:
                                    plan_urls.append(url)
                            
                            if plan_urls:
                                # Deduplicate URLs
                                unique_urls = []
                                seen = set()
                                for url in plan_urls:
                                    if url not in seen:
                                        seen.add(url)
                                        unique_urls.append(url)
                                plan["urls"] = unique_urls
        
        return plans_data


class CSVExporter:
    """Handles CSV export functionality."""
    
    @staticmethod
    def export_plans_csv(plans_data: Dict[str, Any], output_path: str) -> None:
        """Export plans to CSV file."""
        all_plans = (
            plans_data["in_force"]["local"] +
            plans_data["in_force"]["citywide"] +
            plans_data["in_force"]["national_regional"] +
            plans_data["in_force"]["architectural"]
        )
        
        fields = ["plan_number", "name", "deposit_date", "effective_date", "urls"]
        
        # Stringify URLs
        for plan in all_plans:
            if "urls" in plan and isinstance(plan["urls"], list):
                plan["urls"] = " | ".join(plan["urls"])
        
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for plan in all_plans:
                writer.writerow({field: plan.get(field) for field in fields})


# Compatibility functions for backward compatibility
def parse_zchuyot(pdf_path: str) -> Dict[str, Any]:
    """Parse a Zchuyot PDF file - compatibility wrapper for the new OOP parser."""
    parser = ZchuyotParser(ocr_available=True)
    return parser.parse(pdf_path)


def parse_html_privilege_page(html_content: str) -> List[Dict[str, Any]]:
    """Parse HTML privilege page - compatibility wrapper for the new OOP parser."""
    parser = HTMLPrivilegePageParser()
    return parser.parse(html_content)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Parse Tel-Aviv Zchuyot PDF → JSON")
    parser.add_argument("pdf", help="path to PDF")
    parser.add_argument("--json", help="output JSON file")
    parser.add_argument("--plans-csv", help="CSV of in-force plans (all types merged)")
    
    args = parser.parse_args()
    
    try:
        # Initialize parser
        zchuyot_parser = ZchuyotParser(ocr_available=True)
        
        # Parse PDF
        data = zchuyot_parser.parse(args.pdf)
        
        # Output JSON
        if args.json:
            with open(args.json, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"JSON saved to {args.json}")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        
        # Export CSV if requested
        if args.plans_csv:
            CSVExporter.export_plans_csv(data["plans"], args.plans_csv)
            print(f"Plans CSV saved to {args.plans_csv}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()
