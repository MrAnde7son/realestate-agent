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
        start = section_index.get("rights")
        if start is None:
            return {"text": None}
        rights_text = "\n".join(line for line in lines[start + 1 :])
        return {"text": rights_text.strip() or None}


# --------------------------------------------------------------------------- #
# public convenience functions
# --------------------------------------------------------------------------- #

def parse_zchuyot(pdf_path: str) -> Dict[str, Any]:
    parser = ZchuyotParser()
    return parser.parse(pdf_path)


def parse_html_privilege_page(html_content: str) -> List[Dict[str, Any]]:
    """
    Backwards-compatibility shim.  The Tel-Aviv GIS client imports this helper,
    but the current workflow no longer relies on HTML privilege dropdown pages.
    Returning an empty list keeps the import surface identical without
    re-introducing the legacy parser.
    """

    return []


def main(argv: Optional[Sequence[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    cli = argparse.ArgumentParser(description="Parse Tel-Aviv privilege (זכויות) PDF into structured JSON.")
    cli.add_argument("pdf", help="Path to PDF document")
    cli.add_argument("--json", help="Optional output JSON path")
    args = cli.parse_args(argv)

    data = parse_zchuyot(args.pdf)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
