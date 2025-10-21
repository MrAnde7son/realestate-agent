# -*- coding: utf-8 -*-
"""
Lightweight parser that extracts core “Zchuyot” information from Tel-Aviv
privilege PDF files.  The parser focuses on the information the MCP backend
actually uses today:

* parcel identification (block / parcel / parcel area)
* parcel level details (street lines, land-use)
* alert list
* plans in force (local / citywide / national-regional)
* plans in planning (citywide / national-regional)
* planning policies
* rights section (kept as raw text for downstream processing)

The code intentionally avoids heavy dependencies (OCR, NLP, etc.) and relies on
pdfplumber to get the textual content.  To cope with the bidi quirks of Hebrew
PDFs we normalise every extracted line: token order is flipped, Hebrew words are
reversed character-wise, numeric fragments are restored, and well-known plan
codes (e.g. תמ\"א/70) are canonicalised.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pdfplumber


DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")
HEBREW_RE = re.compile(r"[\u0590-\u05FF]")
PLAN_PREFIXES = ("תמ\"א", "תמא", "תת\"ל", "תתל")


# --------------------------------------------------------------------------- #
# helpers for bidi/hebrew token clean-up
# --------------------------------------------------------------------------- #

def _reverse_digits(value: str) -> str:
    """Reverse every numeric sequence in the token."""

    def _flip(match: re.Match[str]) -> str:
        return match.group(0)[::-1]

    return re.sub(r"\d+", _flip, value)


def _fix_plan_code(token: str) -> str:
    """Canonicalise plan code fragments after bidi reversal."""
    mapping = {
        'א"מת': 'תמ"א',
        "אמת": "תמא",
        'א"לתת': 'תת"ל',
        "אלתת": "תתל",
    }

    for suffix, canonical in mapping.items():
        if token.endswith("/" + suffix):
            parts = token.split("/")
            rest = "/".join(reversed(parts[:-1]))
            return f"{canonical}/{rest}"
        if token.startswith(suffix + "/"):
            parts = token.split("/")
            rest = "/".join(parts[1:])
            return f"{canonical}/{rest}"
    return token


def _looks_like_plan_number(token: str) -> bool:
    """Heuristic that recognises common plan number formats."""
    if token.startswith(PLAN_PREFIXES):
        return True
    if token.startswith("תמ\"א") or token.startswith("תמא"):
        return True
    if re.fullmatch(r"[א-ת]\d{1,4}", token):
        return True
    if re.fullmatch(r"\d{3,}[א-ת]?", token):
        return True
    if re.fullmatch(r"[א-ת]{1,2}\d{1,4}", token):
        return True
    if "/" in token and any(prefix in token for prefix in PLAN_PREFIXES):
        return True
    return False


def _normalize_plan_number(value: str) -> str:
    """Ensure plan numbers such as ג1 are reported as 1ג, keep others as-is."""
    value = value.strip()
    match = re.fullmatch(r"([א-ת]+)(\d+)", value)
    if match:
        return f"{match.group(2)}{match.group(1)}"
    return value


def _format_date(value: Optional[str]) -> Optional[str]:
    """Convert DD/MM/YYYY strings into ISO 8601 (YYYY-MM-DD)."""
    if not value:
        return None
    try:
        day, month, year = value.split("/")
        return f"{year}-{month}-{day}"
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# line extraction & normalisation
# --------------------------------------------------------------------------- #

class LineExtractor:
    """Extracts and normalises PDF text into a simple list of lines."""

    def __init__(self, x_tolerance: float = 1.0, y_tolerance: float = 3.0) -> None:
        self.x_tolerance = x_tolerance
        self.y_tolerance = y_tolerance

    def extract(self, pdf_path: str) -> List[str]:
        lines: List[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(
                    layout=True,
                    x_tolerance=self.x_tolerance,
                    y_tolerance=self.y_tolerance,
                )
                if not text:
                    continue
                for raw_line in text.splitlines():
                    norm = self._normalize_line(raw_line)
                    if norm:
                        lines.append(norm)
        return lines

    def _normalize_line(self, line: str) -> str:
        line = (
            line.replace("\u200f", "")
            .replace("\u200e", "")
            .replace("\u008a", " ")
            .replace("`", '"')
        )
        line = re.sub(r"\s+", " ", line).strip()
        if not line:
            return ""
        if HEBREW_RE.search(line):
            tokens = [tok for tok in line.split(" ") if tok]
            tokens.reverse()
            fixed: List[str] = []
            for token in tokens:
                if HEBREW_RE.search(token):
                    token = token[::-1]
                    token = _reverse_digits(token)
                    match = re.match(r"^(\d+)([א-ת]+)$", token)
                    if match:
                        token = f"{match.group(2)}{match.group(1)}"
                    token = _fix_plan_code(token)
                fixed.append(token)
            line = " ".join(fixed)
        return line.strip()


# --------------------------------------------------------------------------- #
# data classes
# --------------------------------------------------------------------------- #

@dataclass
class PlanEntry:
    plan_number: str
    name: str
    deposit_date: Optional[str] = None
    effective_date: Optional[str] = None
    publication: Optional[str] = None
    mbat_number: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        payload = {
            "plan_number": self.plan_number,
            "name": self.name,
            "deposit_date": self.deposit_date,
            "effective_date": self.effective_date,
        }
        if self.publication:
            payload["publication"] = self.publication
        if self.mbat_number:
            payload["mbat_number"] = self.mbat_number
        return payload


# --------------------------------------------------------------------------- #
# core parser
# --------------------------------------------------------------------------- #

class ZchuyotParser:
    """High level orchestrator."""

    SECTION_LABELS = {
        "alerts": "התראות",
        "plans_header": "תכניות בתוקף",
        "plans_local": "תכניות מקומיות בתוקף",
        "plans_citywide": "כלל עירוניות בתוקף",
        "plans_natreg": "תכניות מתאר ארציות ומחוזיות בתוקף",
        "plans_in_planning_header": "תכניות בתכנון",
        "plans_in_planning_citywide": "כלל עירוניות בתכנון",
        "plans_in_planning_natreg": "תכניות מתאר ארציות ומחוזיות בתכנון",
        "policy": "מדיניות תכנונית",
        "rights": "פירוט זכויות",
    }

    TABLE_HEADER_KEYWORDS = (
        "מס\"",
        "שם תוכנית",
        "שם תכנית",
        "תאריך",
        "תוקף",
        "הפקדה",
        "פירסומים",
        "פרסום",
        "מבא\"\"ת",
        "י.פ.",
        "סעיף",
    )

    def __init__(self) -> None:
        self.extractor = LineExtractor()

    # -- public API --------------------------------------------------------- #
    def parse(self, pdf_path: str) -> Dict[str, Any]:
        lines = self.extractor.extract(pdf_path)
        section_index = self._index_sections(lines)

        basic_info, address_lines = self._parse_basic(lines)
        land_use = self._parse_land_use(lines)
        alerts = self._parse_alerts(lines, section_index)

        plans_in_force = {
            "local": self._parse_plan_table(
                lines,
                section_index,
                "plans_local",
                ["plans_citywide", "plans_natreg", "plans_in_planning_header"],
            ),
            "citywide": self._parse_plan_table(
                lines,
                section_index,
                "plans_citywide",
                ["plans_natreg", "plans_in_planning_header"],
            ),
            "national_regional": self._parse_plan_table(
                lines,
                section_index,
                "plans_natreg",
                ["plans_in_planning_header"],
            ),
        }

        plans_in_planning = {
            "citywide": self._parse_city_planning(
                lines, section_index, "plans_in_planning_citywide", ["plans_in_planning_natreg", "policy"]
            ),
            "national_regional": self._parse_plan_table(
                lines,
                section_index,
                "plans_in_planning_natreg",
                ["policy"],
            ),
        }

        policies = self._parse_policies(lines, section_index)
        rights = self._parse_rights(lines, section_index)

        result: Dict[str, Any] = {
            "source_file": os.path.abspath(pdf_path),
            "extracted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "basic": {
                **basic_info,
                "land_use": land_use,
            },
            "details": {
                "addresses": address_lines,
            },
            "alerts": alerts,
            "plans": {
                "in_force": {
                    "local": [p.as_dict() for p in plans_in_force["local"]],
                    "citywide": [p.as_dict() for p in plans_in_force["citywide"]],
                    "national_regional": [p.as_dict() for p in plans_in_force["national_regional"]],
                },
                "in_planning": {
                    "citywide": [p.as_dict() for p in plans_in_planning["citywide"]],
                    "national_regional": [p.as_dict() for p in plans_in_planning["national_regional"]],
                },
            },
            "policies": policies,
            "rights": rights,
            "raw_preview": "\n".join(lines[:200]),
        }
        return result

    # -- section helpers ---------------------------------------------------- #
    def _index_sections(self, lines: Sequence[str]) -> Dict[str, int]:
        indices: Dict[str, int] = {}
        for idx, line in enumerate(lines):
            for key, label in self.SECTION_LABELS.items():
                if key not in indices and line.strip().startswith(label):
                    indices[key] = idx
        return indices

    def _slice_section(
        self,
        lines: Sequence[str],
        section_index: Dict[str, int],
        key: str,
        next_keys: Optional[Sequence[str]] = None,
    ) -> List[str]:
        start = section_index.get(key)
        if start is None:
            return []
        end = len(lines)
        if next_keys:
            for nk in next_keys:
                candidate = section_index.get(nk)
                if candidate is not None and candidate > start:
                    end = min(end, candidate)
        return list(lines[start + 1 : end])

    # -- basic info --------------------------------------------------------- #
    def _parse_basic(self, lines: Sequence[str]) -> Tuple[Dict[str, Any], List[str]]:
        basic: Dict[str, Any] = {
            "issue_date": None,
            "block": None,
            "parcel": None,
            "parcel_area_sqm": None,
        }
        addresses: List[str] = []

        for line in lines:
            issue = re.search(r"תאריך הפקה:\s*(\d{2}/\d{2}/\d{4})", line)
            if issue and not basic["issue_date"]:
                basic["issue_date"] = _format_date(issue.group(1))

            ids = re.search(r"גוש:\s*(\d+).*חלקה:\s*(\d+)", line)
            if ids:
                basic["block"] = int(ids.group(1))
                basic["parcel"] = int(ids.group(2))

        try:
            idx = lines.index("פרטי קרקע")
            for candidate in lines[idx + 1 : idx + 6]:
                if candidate.startswith("גוש חלקה") or candidate.startswith("התראות"):
                    break
                if candidate:
                    addresses.append(candidate)
        except ValueError:
            addresses = []

        for idx, line in enumerate(lines):
            if "שטח לחישוב זכויות" in line:
                if idx + 1 < len(lines):
                    parts = [p for p in lines[idx + 1].split() if p.replace(".", "", 1).isdigit()]
                    if parts:
                        try:
                            basic["parcel_area_sqm"] = float(parts[0])
                        except ValueError:
                            pass
                break

        return basic, addresses

    # -- land use ----------------------------------------------------------- #
    def _parse_land_use(self, lines: Sequence[str]) -> Optional[str]:
        for idx, line in enumerate(lines):
            if line.startswith("יעוד קרקע"):
                collected: List[str] = []
                for candidate in lines[idx + 1 : idx + 6]:
                    if not candidate:
                        break
                    if candidate.startswith("תכניות") or candidate.startswith("מסמכי") or candidate.startswith("פירוט"):
                        break
                    if candidate.startswith("זכות "):
                        break
                    if candidate.startswith("יעוד קרקע"):
                        continue
                    collected.append(candidate)
                    if len(collected) >= 1:
                        break
                if collected:
                    return " ".join(collected).strip()
        return None

    # -- alerts ------------------------------------------------------------- #
    def _parse_alerts(self, lines: Sequence[str], section_index: Dict[str, int]) -> List[str]:
        alerts = self._slice_section(lines, section_index, "alerts", ["plans_header", "plans_local"])
        cleaned: List[str] = []
        for line in alerts:
            if not line or line.startswith("תכניות"):
                break
            if "הערה להתראה" in line or "הוראות" in line:
                continue
            if line.strip() == "":
                continue
            cleaned.append(line)
        return cleaned

    # -- plans in force ----------------------------------------------------- #
    def _parse_plan_table(
        self,
        lines: Sequence[str],
        section_index: Dict[str, int],
        key: str,
        next_keys: Optional[Sequence[str]] = None,
    ) -> List[PlanEntry]:
        section_lines = self._slice_section(lines, section_index, key, next_keys)
        plans: List[PlanEntry] = []
        name_buffer: List[str] = []

        for line in section_lines:
            if not line:
                continue
            if self._is_table_header(line):
                continue
            if self._is_plan_row(line):
                plan = self._parse_plan_row(line, name_buffer)
                if plan:
                    plans.append(plan)
                name_buffer = []
            else:
                name_buffer.append(line)
        return plans

    def _is_table_header(self, line: str) -> bool:
        return any(keyword in line for keyword in self.TABLE_HEADER_KEYWORDS)

    def _is_plan_row(self, line: str) -> bool:
        tokens = line.split()
        if not tokens:
            return False
        first = tokens[0]
        if _looks_like_plan_number(first):
            return True
        if DATE_RE.search(line):
            return True
        return False

    def _parse_plan_row(self, line: str, name_buffer: Sequence[str]) -> Optional[PlanEntry]:
        tokens = line.split()
        if not tokens:
            return None

        plan_number = _normalize_plan_number(tokens[0])

        remainder = tokens[1:]
        dates = [tok for tok in remainder if DATE_RE.fullmatch(tok)]
        deposit_date = _format_date(dates[0]) if dates else None
        effective_date = _format_date(dates[1]) if len(dates) > 1 else None

        remainder = [tok for tok in remainder if tok not in dates]
        publication = None
        mbat_number = None

        if remainder and remainder[-1].isdigit():
            publication = remainder.pop()

        inline_name = " ".join(remainder).strip()
        full_name_parts = [part for part in name_buffer if part and not self._is_table_header(part)]
        if inline_name:
            full_name_parts.append(inline_name)

        name = " ".join(full_name_parts).strip() or plan_number

        return PlanEntry(
            plan_number=plan_number,
            name=name,
            deposit_date=deposit_date,
            effective_date=effective_date,
            publication=publication,
            mbat_number=mbat_number,
        )

    # -- plans in planning -------------------------------------------------- #
    def _parse_city_planning(
        self,
        lines: Sequence[str],
        section_index: Dict[str, int],
        key: str,
        next_keys: Optional[Sequence[str]] = None,
    ) -> List[PlanEntry]:
        section_lines = self._slice_section(lines, section_index, key, next_keys)
        plans: List[PlanEntry] = []
        buffer: List[str] = []

        for line in section_lines:
            if not line or self._is_table_header(line):
                continue
            if re.fullmatch(r"[0-9-]+\s+\d+", line):
                parts = line.split()
                mbat = parts[0]
                plan_number = _normalize_plan_number(parts[1])
                name = " ".join(buffer).strip() or plan_number
                plans.append(
                    PlanEntry(
                        plan_number=plan_number,
                        name=name,
                        mbat_number=mbat,
                    )
                )
                buffer = []
            else:
                buffer.append(line)
        return plans

    # -- policies ----------------------------------------------------------- #
    def _parse_policies(self, lines: Sequence[str], section_index: Dict[str, int]) -> List[Dict[str, Any]]:
        policy_lines = self._slice_section(lines, section_index, "policy", ["rights"])
        policies: List[Dict[str, Any]] = []
        for line in policy_lines:
            if not line or self._is_table_header(line):
                continue
            tokens = line.split()
            if len(tokens) < 3:
                continue
            number = tokens[0] if tokens[0].isdigit() else None
            date_candidate = tokens[-1] if DATE_RE.fullmatch(tokens[-1]) else None
            decision_candidate = tokens[-2] if len(tokens) >= 2 else None
            if decision_candidate and not re.search(r"\d", decision_candidate):
                decision_candidate = None
            name_tokens = tokens[1 : -2 if (date_candidate and decision_candidate) else -1]
            name = " ".join(name_tokens).strip() if name_tokens else None
            policies.append(
                {
                    "policy_number": number,
                    "name": name,
                    "decision_number": decision_candidate if decision_candidate and decision_candidate != number else None,
                    "approval_date": _format_date(date_candidate) if date_candidate else None,
                }
            )
        return policies

    # -- rights ------------------------------------------------------------- #
    def _parse_rights(self, lines: Sequence[str], section_index: Dict[str, int]) -> Dict[str, Any]:
        section_lines = self._slice_section(lines, section_index, "rights")
        if not section_lines:
            return {"text": None}

        rights_text = "\n".join(section_lines).strip()
        working: Dict[str, Any] = {
            "building_lines": [],
            "building_lines_detailed": [],
            "floor_percentages": [],
            "floor_percentages_detailed": [],
            "minimum_values": [],
            "maximum_values": [],
            "minmax_values": [],
            "parking_requirements": [],
            "notes": [],
        }

        for line in section_lines:
            if not line or self._is_table_header(line):
                continue
            working["notes"].append({"text": line, "type": "general"})
            self._extract_building_lines(line, working)
            self._extract_floor_percentages(line, working)
            self._extract_minmax_values(line, working)
            self._extract_dwelling_units(line, working)
            self._extract_number_of_floors(line, working)
            self._extract_building_coverage(line, working)
            self._extract_parking(line, working)
            self._extract_auxiliary_building(line, working)

        result: Dict[str, Any] = {"text": rights_text or None}

        for key in (
            "building_lines",
            "building_lines_detailed",
            "floor_percentages",
            "floor_percentages_detailed",
            "minimum_values",
            "maximum_values",
            "minmax_values",
            "parking_requirements",
            "notes",
        ):
            values = working.get(key)
            if values:
                result[key] = values

        if working.get("dwelling_units") is not None:
            result["dwelling_units"] = working["dwelling_units"]

        if working.get("number_of_floors") is not None:
            result["number_of_floors"] = working["number_of_floors"]
            result["floors"] = working["number_of_floors"]

        if working.get("building_coverage_percentage") is not None:
            coverage = working["building_coverage_percentage"]
            result["building_coverage_percentage"] = coverage
            result["coverage"] = coverage

        if working.get("auxiliary_building_area") is not None:
            area = working["auxiliary_building_area"]
            result["auxiliary_building_area"] = area
            result["auxiliary_building"] = area

        # dedupe simple list fields
        if "building_lines" in result:
            result["building_lines"] = list(dict.fromkeys(result["building_lines"]))

        if "minmax_values" in result:
            # ensure min/max entries keep consistent structure
            result["minmax_values"] = [
                {k: v for k, v in entry.items() if k != "bound"} for entry in result["minmax_values"]
            ]

        return result

    def _extract_building_lines(self, line: str, rights: Dict[str, Any]) -> None:
        if "קו" not in line or "בניין" not in line:
            return

        lines = rights.setdefault("building_lines", [])
        if line not in lines:
            lines.append(line)

        type_keywords = {
            "חזית": "חזית",
            "צדדי": "צדדי",
            "צידי": "צדדי",
            "אחורי": "אחורי",
            "אחורית": "אחורי",
            "קדמי": "קדמי",
        }
        line_type = None
        for keyword, canonical in type_keywords.items():
            if keyword in line:
                line_type = canonical
                break

        distance: Optional[float] = None
        patterns = [
            r"קו\s+בניין(?:\s+(?:חזית|צדדי|צידי|אחורי|קדמי)\s*\d*)?\s*(\d+(?:\.\d+)?)\s*מ",
            r"(\d+(?:\.\d+)?)\s*מ[\"׳״']?\s*(?:קו\s+בניין)",
        ]
        for pat in patterns:
            match = re.search(pat, line)
            if match:
                distance = self._coerce_number(match.group(1))
                break

        if distance is None:
            # fallback: last number before the keyword "קו בניין"
            idx = line.find("קו בניין")
            if idx != -1:
                numbers = re.findall(r"(\d+(?:\.\d+)?)", line[:idx])
                if numbers:
                    distance = self._coerce_number(numbers[-1])

        if distance is None:
            return

        detailed = rights.setdefault("building_lines_detailed", [])
        if not any(entry.get("raw_text") == line for entry in detailed):
            detailed.append(
                {
                    "type": line_type,
                    "distance_meters": distance,
                    "raw_text": line,
                }
            )

    def _extract_floor_percentages(self, line: str, rights: Dict[str, Any]) -> None:
        if "קומ" not in line:
            return
        if "מספר קומות" in line or "קומות מספר" in line:
            return
        if "שטח קומה" not in line and "אחוז" not in line:
            return

        tokens_after = None
        if "שטח קומה" in line:
            after = line.split("שטח קומה", 1)[1].strip()
            tokens_after = after.split()
        elif "קומה" in line:
            after = line.split("קומה", 1)[1].strip()
            tokens_after = after.split()

        if not tokens_after:
            return

        floor_tokens: List[str] = []
        numeric_token: Optional[str] = None
        for tok in tokens_after:
            if self._is_numeric_token(tok):
                numeric_token = tok
                break
            floor_tokens.append(tok)

        if not numeric_token:
            return

        floor_label = " ".join(floor_tokens).strip()
        if not floor_label:
            return

        percentage_value = self._coerce_number(numeric_token)
        if percentage_value is None:
            return

        detailed_entry = {
            "floor": floor_label,
            "percentage": percentage_value,
            "raw_text": line,
        }
        detailed = rights.setdefault("floor_percentages_detailed", [])
        if not any(entry.get("raw_text") == line for entry in detailed):
            detailed.append(detailed_entry)
            rights.setdefault("floor_percentages", []).append(percentage_value)

    def _extract_minmax_values(self, line: str, rights: Dict[str, Any]) -> None:
        keywords = [
            ("מינימום", "minimum"),
            ("םינימום", "minimum"),
            ("םומינימ", "minimum"),
            ("מקסימום", "maximum"),
            ("םקסימום", "maximum"),
            ("םומיסקמ", "maximum"),
        ]
        for keyword, bound in keywords:
            idx = line.find(keyword)
            if idx == -1:
                continue
            value_str = self._value_before_index(line, idx)
            if value_str is None:
                continue
            value = self._coerce_number(value_str)
            if value is None:
                continue

            entry: Dict[str, Any] = {
                "value": value,
                "raw_text": line,
                "bound": bound,
            }
            entry_type = self._classify_minmax_entry(line)
            if entry_type:
                entry["type"] = entry_type

            rights.setdefault("minmax_values", []).append(entry.copy())

            target_key = "minimum_values" if bound == "minimum" else "maximum_values"
            rights.setdefault(target_key, []).append(
                {k: v for k, v in entry.items() if k not in {"bound"}}
            )

            if entry_type == "dwelling_units":
                rights["dwelling_units"] = int(value)
            if entry_type == "floors" and bound == "maximum":
                current = rights.get("number_of_floors")
                candidate = int(value)
                if current is None or candidate > current:
                    rights["number_of_floors"] = candidate
            if entry_type == "auxiliary_building_area":
                rights["auxiliary_building_area"] = value
            if entry_type == "parking":
                record = {"value": value, "raw_text": line}
                entries = rights.setdefault("parking_requirements", [])
                if not any(item.get("raw_text") == line for item in entries):
                    entries.append(record)
            if entry_type == "percentage":
                if any(term in line for term in ["אחוז משטח", "אחוז בנייה", "אחוזי בניה"]):
                    rights["building_coverage_percentage"] = value
            break

    def _extract_dwelling_units(self, line: str, rights: Dict[str, Any]) -> None:
        patterns = [
            r"(\d+)\s*יחידות?\s+דיור",
            r"יחידות?\s+דיור\s*(\d+)",
            r"מספר\s+יחידות\s+דיור\s*(\d+)",
        ]
        for pat in patterns:
            match = re.search(pat, line)
            if match:
                value = self._coerce_number(match.group(1))
                if value is not None:
                    rights["dwelling_units"] = int(value)
                return

    def _extract_number_of_floors(self, line: str, rights: Dict[str, Any]) -> None:
        if "מספר קומות" not in line and "קומות מספר" not in line:
            return
        match = re.search(r"(\d+)", line)
        if not match:
            return
        value = self._coerce_number(match.group(1))
        if value is not None:
            current = rights.get("number_of_floors")
            candidate = int(value)
            if current is None or candidate > current:
                rights["number_of_floors"] = candidate

    def _extract_building_coverage(self, line: str, rights: Dict[str, Any]) -> None:
        if "אחוז" not in line:
            return
        patterns = [
            r"(\d+(?:\.\d+)?)\s*%\s*אחוז(?:י)?\s*(?:בנייה|בניה|משטח)",
            r"(\d+(?:\.\d+)?)\s*אחוז(?:י)?\s*(?:בנייה|בניה|משטח)",
        ]
        for pat in patterns:
            match = re.search(pat, line)
            if match:
                value = self._coerce_number(match.group(1))
                if value is not None:
                    rights["building_coverage_percentage"] = value
                    return

    def _extract_parking(self, line: str, rights: Dict[str, Any]) -> None:
        if "חניה" not in line:
            return

        entries = rights.setdefault("parking_requirements", [])

        # --- 1) Qualitative: "חניה מותר/מותרת/אסור/אסורה" + optional plan ref (e.g., א2550, תמ"א/38) ---
        # Guard: only treat as qualitative if there is no nearby explicit numeric count.
        numeric_hint = re.search(
            r"(?:\d+\s*(?:מקומות|מקום)\s+חניה)|(?:חניה\s*(?:מותר(?:ת)?|מינימום|מקסימום)\s*\d)",
            line
        )

        qual = re.search(
            r"""חניה\s*
                (?P<status>מותר(?:ת)?|אסור(?:ה)?)      # permitted/forbidden (Hebrew variants)
                (?:\s*(?:בתכנית|עפ(?:י)?|לפי)?)\s*     # optional "per plan/according to"
                (?P<plan>(?:[א-ת"\/\-\s]?\d[\w"\/\-\s]*)?)\s*$   # optional plan ref (e.g., א2550, תמ"א/38)
            """,
            line, re.VERBOSE
        )

        if qual and not numeric_hint:
            status_he = qual.group("status")
            status = "permitted" if status_he.startswith("מותר") else "forbidden"
            plan_ref = (qual.group("plan") or "").strip()
            plan_ref = re.sub(r"\s+", "", plan_ref) if plan_ref else None

            if not any(item.get("raw_text") == line for item in entries):
                entries.append({
                    "type": "qualitative",
                    "status": status,  # "permitted" | "forbidden"
                    "source_plan": plan_ref,  # e.g., "א2550" (optional)
                    "value": None,  # keep schema tolerant for callers expecting "value"
                    "raw_text": line,
                })
            return

        # --- 2) Quantitative: your existing patterns ---
        patterns = [
            r"(\d+(?:\.\d+)?)\s*(?:מקומות|מקום)\s+חניה",
            r"חניה\s*(?:מותר(?:ת)?|מינימום|מקסימום)\s*(\d+(?:\.\d+)?)",
        ]
        for pat in patterns:
            match = re.search(pat, line)
            if match:
                value = self._coerce_number(match.group(1))
                if value is None:
                    continue
                if not any(item.get("raw_text") == line for item in entries):
                    entries.append({
                        "type": "quantitative",
                        "value": value,
                        "unit": "spaces",
                        "raw_text": line,
                    })
                return

    def _extract_auxiliary_building(self, line: str, rights: Dict[str, Any]) -> None:
        if "מבנה עזר" not in line:
            return
        match = re.search(
            r"מבנה\s+עזר\s+(\d+(?:\.\d+)?)\s*(?:מ\"ר|מטר(?:ים)?)?\s*(?:מינימום|מקסימום)",
            line,
        )
        if not match:
            return
        value = self._coerce_number(match.group(1))
        if value is None:
            return
        rights["auxiliary_building_area"] = value

    def _coerce_number(self, token: Optional[str]) -> Optional[float]:
        if token is None:
            return None
        clean = token.replace(",", "").replace("'", "").replace("״", "").replace("”", "")
        try:
            value = float(clean)
        except ValueError:
            return None
        if value.is_integer():
            return int(value)
        return value

    def _is_numeric_token(self, token: str) -> bool:
        return bool(re.fullmatch(r"\d+(?:\.\d+)?", token.replace(",", "")))

    def _value_before_index(self, line: str, idx: int) -> Optional[str]:
        segment = line[:idx]
        matches = re.findall(r"(\d+(?:\.\d+)?)", segment)
        return matches[-1] if matches else None

    def _classify_minmax_entry(self, line: str) -> Optional[str]:
        text = line.replace(" ", "")
        lower = line.lower()

        if re.search(r"מספר\s+קומות", line) or re.search(r"קומות\s*מספר", line) or "מספרקומות" in text or "תומוקרפסמ" in text:
            return "floors"

        dwelling_keywords = ["יחידותדיור", "דיור", "דירות", "יחידות"]
        if any(kw in text for kw in dwelling_keywords):
            return "dwelling_units"

        parking_keywords = ["חניה", "הינח", "חני", "חניות"]
        if any(kw in line for kw in parking_keywords):
            return "parking"

        auxiliary_keywords = ["מבנהעזר", "רזעהנבמ"]
        if any(kw in text for kw in auxiliary_keywords):
            return "auxiliary_building_area"

        percent_keywords = ["%", "אחוז", "זחוא", "percent"]
        if any(kw in line or kw in lower for kw in percent_keywords):
            return "percentage"

        area_keywords = ["מ\"ר", "מ״ר", "ר\"מ", "ר״מ", "שטח", "חטש", "בנייה", "בניה"]
        if any(kw in line or kw in text or kw in lower for kw in area_keywords):
            return "building_area"

        return None


# --------------------------------------------------------------------------- #
# public convenience functions
# --------------------------------------------------------------------------- #

def parse_zchuyot(pdf_path: str) -> Dict[str, Any]:
    parser = ZchuyotParser()
    return parser.parse(pdf_path)
    

def main(argv: Optional[Sequence[str]] = None) -> int:
    data = parse_zchuyot("backend-django/privilege_pages/privilege_block_6638_parcel_392.pdf")
    print(data)


if __name__ == "__main__":
    sys.exit(main())
