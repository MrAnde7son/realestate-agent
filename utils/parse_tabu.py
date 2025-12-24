"""Utilities for parsing Israeli land‑registry (Tabu) PDF documents.

This module exposes a single function, :func:`parse_tabu_pdf`, which
accepts a file‑like object positioned at the start of a PDF and returns
a list of dictionaries representing the structured data extracted from
the document.  Each dictionary has two keys: ``field`` and ``value``.

The parser is designed to handle a variety of Tabu formats without
prior knowledge of specific ID numbers or parcel information.  It
attempts to recognise common fields such as the block number (``גוש``),
parcel (``חלקה``), sub‑parcel (``תת חלקה``), ownership shares,
identification numbers, dates, owner names and actions.  It also
captures generic key/value lines that follow a ``key: value`` pattern.

Because the underlying PDFs are generated in Hebrew and often contain
right‑to‑left text, the parser uses flexible regular expressions to
match numbers appearing either before or after the Hebrew field names.
For example, both ``6336 :גוש`` and ``גוש: 6336`` will be recognised as
the block number.

The function does *not* assume any specific ID numbers or owner names
and therefore works on any Tabu document.

Example usage::

    with open("/path/to/tabu.pdf", "rb") as f:
        rows = parse_tabu_pdf(f)
        for row in rows:
            print(f"{row['field']}: {row['value']}")

Note that this module depends on ``pdfplumber`` to extract text from
PDFs.  Ensure it is installed in your environment.
"""

from __future__ import annotations

from typing import IO, Dict, Iterable, List, Set, Tuple, Optional
import re

import pdfplumber


def _reverse_hebrew_text(text: str) -> str:
    """Reverse Hebrew text that has been incorrectly extracted from PDF."""
    # Split by spaces and reverse each word
    words = text.split()
    reversed_words = []

    for word in words:
        # Check if word contains Hebrew characters
        if any("\u0590" <= char <= "\u05ff" for char in word):
            # Reverse Hebrew words
            reversed_words.append(word[::-1])
        else:
            # Keep non-Hebrew words as is
            reversed_words.append(word)

    return " ".join(reversed_words)


def _extract_number_near_field(line: str, keyword: str) -> str | None:
    """Extract a numeric value that appears adjacent to a Hebrew keyword.

    In Tabu PDFs the field labels (such as ``גוש`` for the block
    number) can appear either before or after the number depending on
    text direction.  This helper searches for digits appearing on
    either side of ``keyword`` separated by optional whitespace or a
    colon.

    Args:
        line: The text line to search.
        keyword: The Hebrew keyword (e.g. ``'גוש'``, ``'חלקה'``).

    Returns:
        The first matching number as a string, or ``None`` if not found.
    """
    # Try to match when the number comes after the keyword (e.g. "גוש: 6336")
    # Require at least one whitespace character between the keyword and the digits when
    # matching numbers that follow the keyword.  Without this, patterns like
    # ``תת חלקה497`` (where the digits belong to a different field) can be
    # misinterpreted as belonging to ``תת חלקה``.  Using ``\s+`` avoids
    # matching digits glued directly to the word.
    pattern_after = rf"{re.escape(keyword)}\s*:?\s+(\d+)"
    match = re.search(pattern_after, line)
    if match:
        return match.group(1)
    # Try to match when the number comes before the keyword (e.g. "6336 :גוש")
    pattern_before = rf"(\d+)\s*:?\s*{re.escape(keyword)}"
    match = re.search(pattern_before, line)
    if match:
        return match.group(1)
    return None


def _extract_owner_line(line: str) -> Tuple[str | None, str | None, str | None]:
    """Extract an owner name, action and date from a line of text.

    This function attempts to split a line into a name, an action and a
    date.  It searches for the first occurrence of either a known
    action keyword (``מכר``, ``משכנתה``, ``מתנה``, ``הקניית``, ``הערת``)
    or a date (in ``DD/MM/YYYY`` format).  The portion of the line
    before that index is considered the candidate name.  If no action
    or date is present the function returns ``(None, None, None)``.

    Args:
        line: A single line of text from the PDF.

    Returns:
        A tuple ``(name, action, date)``.  ``name`` will be ``None`` if
        it does not contain at least two Hebrew characters or resembles
        a header.  ``action`` and ``date`` will be ``None`` if not
        present in the line.
    """
    # Define the list of action keywords and compile a regex to find them
    action_keywords = ["מכר", "משכנתה", "מתנה", "הקניית", "הערת"]
    action_re = re.compile("|".join(map(re.escape, action_keywords)))
    # Find the first action keyword in the line, if any
    action_match = action_re.search(line)
    # Find the first date in the line, if any
    date_match = re.search(r"\d{2}/\d{2}/\d{4}", line)
    # Determine the index where the name ends and the rest begins
    split_index = None
    action = None
    if action_match and (not date_match or action_match.start() <= date_match.start()):
        split_index = action_match.start()
        action = action_match.group(0)
    elif date_match:
        split_index = date_match.start()
    # If neither action nor date is present, we cannot reliably extract
    # an owner name
    if split_index is None:
        return None, None, None
    # Candidate name is everything before the split index
    name = line[:split_index].strip()
    # Extract the date if present anywhere in the line
    date = date_match.group(0) if date_match else None
    # Validate the candidate name: it must contain Hebrew letters,
    # must not be a known header and must include at least two Hebrew
    # characters (ignoring spaces and hyphens)
    if name and re.search(r"[א-ת]", name):
        if name in {"בעלים", "הבעלים", "בעלי המשכנתה"}:
            name = None
        else:
            hebrew_only = "".join(ch for ch in name if "א" <= ch <= "ת")
            if len(hebrew_only) < 2:
                name = None
    else:
        name = None
    return name, action, date


class TabuParser:
    """Object‑oriented parser for Israeli land‑registry (Tabu) PDFs.

    A ``TabuParser`` instance encapsulates all parsing logic.  The
    :meth:`parse` method extracts parcel identifiers, ownership shares,
    identification numbers, dates, owner names and generic key/value
    pairs from the provided PDF.  Results are stored on the instance
    and can be retrieved via :attr:`rows` or searched via
    :meth:`search`.

    Example:

        with open("/path/to/tabu.pdf", "rb") as f:
            parser = TabuParser(f)
            parser.parse()
            for row in parser.rows:
                print(row['field'], row['value'])

    """

    def __init__(self, file: IO) -> None:
        #: The PDF file to parse (a file‑like object positioned at the start)
        self._file: IO = file
        #: Internal storage for parsed rows
        self.rows: List[Dict[str, str]] = []
        #: Internal set for deduplication
        self._seen: Set[Tuple[str, str]] = set()

    def _extract_number_near_field(self, line: str, keyword: str) -> Optional[str]:
        """Instance method wrapper for the standalone helper.

        Delegates to the module‑level :func:`_extract_number_near_field` to
        preserve existing logic.

        Args:
            line: A line of text.
            keyword: The Hebrew keyword to search for.

        Returns:
            The matched number or ``None``.
        """
        return _extract_number_near_field(line, keyword)

    def _extract_owner_line(
        self, line: str
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Instance method wrapper for the standalone owner extractor.

        Args:
            line: A line of text potentially containing an owner, an action and a date.

        Returns:
            A tuple ``(name, action, date)`` where each element may be ``None``.
        """
        return _extract_owner_line(line)

    def parse(self) -> List[Dict[str, str]]:
        """Parse the PDF associated with this parser.

        Repeated calls will clear previous results and re‑run the
        extraction.  Parsed rows are stored on :attr:`rows` and also
        returned.

        Returns:
            A list of dictionaries, each with ``field`` and ``value`` keys.
        """
        # Reset state
        self.rows = []
        self._seen = set()
        with pdfplumber.open(self._file) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                lines = [
                    re.sub(r"\s+", " ", line.strip())
                    for line in text.splitlines()
                    if line.strip()
                ]
                for line in lines:
                    # Fix Hebrew text reversal before processing
                    line = _reverse_hebrew_text(line)
                    self._process_line(line)
        return self.rows

    def _add_row(self, field: str, value: str) -> None:
        """Add a (field, value) pair to the results if not already seen."""
        if (field, value) not in self._seen:
            self.rows.append({"field": field, "value": value})
            self._seen.add((field, value))

    def _process_line(self, line: str) -> None:
        """Process a single normalised line of text and extract data points."""
        # 1. Parcel identifiers
        for keyword, field_name in [
            ("גוש", "גוש"),
            ("חלקה", "חלקה"),
            ("תת חלקה", "תת חלקה"),
        ]:
            value = self._extract_number_near_field(line, keyword)
            if value:
                self._add_row(field_name, value)

        # 2. Ownership share fractions
        frac_match = re.search(r"\b(\d{1,3})\s*/\s*(\d{1,3})\b(?!\s*/)", line)
        if frac_match:
            frac_value = f"{frac_match.group(1)}/{frac_match.group(2)}"
            self._add_row("החלק בנכס", frac_value)
        # Special case for full ownership
        if "בשלמות" in line:
            self._add_row("החלק בנכס", "בשלמות")

        # 3. Identification numbers (Israeli IDs)
        for id_match in re.findall(r"\b\d{8,9}\b", line):
            self._add_row("מספר זיהוי", id_match)

        # 4. Dates
        for date_match in re.findall(r"\b\d{2}/\d{2}/\d{4}\b", line):
            self._add_row("תאריך", date_match)

        # 5. Owner names and actions
        if re.search(r"[א-ת]", line) and re.search(r"\d", line):
            has_date = bool(re.search(r"\b\d{2}/\d{2}/\d{4}\b", line))
            action_keywords = ["מכר", "משכנתה", "מתנה", "הקניית", "הערת"]
            has_action = any(act in line for act in action_keywords)
            if has_date or has_action:
                name, action, date = self._extract_owner_line(line)
                if name:
                    # Check if this is a mortgage entry, not an ownership entry
                    if "משכנתה" in line:
                        self._add_row("בעלי המשכנתה", name)
                    else:
                        self._add_row("בעלים", name)
                if action:
                    self._add_row("מהות פעולה", action)
                if date:
                    self._add_row("תאריך", date)

        # 6. Area information extraction
        # Look for area-related fields in Hebrew
        area_keywords = ["שטח", "מ״ר", "מטר", "שטח כולל", "שטח נטו", "שטח בנוי"]
        for keyword in area_keywords:
            if keyword in line:
                # Extract numeric value near the keyword
                value = self._extract_number_near_field(line, keyword)
                if value:
                    if "כולל" in keyword or "כולל" in line:
                        self._add_row("שטח כולל", value)
                    elif "נטו" in keyword or "נטו" in line:
                        self._add_row("שטח נטו", value)
                    elif "בנוי" in keyword or "בנוי" in line:
                        self._add_row("שטח בנוי", value)
                    else:
                        self._add_row("שטח", value)

        # 7. Specific area patterns from Tabu documents (after Hebrew reversal)
        # Pattern: "ירימ 653.00 ופי- ביבא לת תייריע" → "מירי 653.00 -יפו אביב תל עיריית" (Total area)
        total_area_match = re.search(r"מירי\s+(\d+(?:\.\d+)?)", line)
        if total_area_match:
            self._add_row("שטח כולל", total_area_match.group(1))

        # Pattern: "324.00 עקרק ב" → "324.00 קרקע ב" (Subparcel area)
        subparcel_area_match = re.search(r"(\d+(?:\.\d+)?)\s+קרקע\s+ב", line)
        if subparcel_area_match:
            self._add_row("שטח נטו", subparcel_area_match.group(1))

        # Pattern: "1/2 95.40 - הריד" → "1/2 95.40 - דירה" (Built area)
        built_area_match = re.search(r"(\d+(?:\.\d+)?)\s*-\s*דירה", line)
        if built_area_match:
            self._add_row("שטח בנוי", built_area_match.group(1))

        # 8. Generic key/value pairs separated by a single colon
        if ":" in line and line.count(":") == 1:
            key, value = [part.strip() for part in line.split(":", 1)]
            if key and value and not any(k in key for k in ["גוש", "חלקה", "תת חלקה"]):
                self._add_row(key, value)

    def search(self, term: str) -> List[Dict[str, str]]:
        """Filter the parsed rows by a search term.

        Args:
            term: The term to search for (case‑insensitive).  If empty, all
                rows are returned.

        Returns:
            A list of rows where the term appears in either the field or value.
        """
        if not term:
            return list(self.rows)
        term_lower = term.lower()
        return [
            row
            for row in self.rows
            if term_lower in row["field"].lower() or term_lower in row["value"].lower()
        ]


def parse_tabu_pdf(file: IO) -> List[Dict[str, str]]:
    """Convenience wrapper around :class:`TabuParser` for backward compatibility.

    This function constructs a :class:`TabuParser`, invokes its
    :meth:`parse` method and returns the resulting rows.

    Args:
        file: A file‑like object positioned at the start of the PDF.

    Returns:
        A list of dictionaries containing the parsed rows.
    """
    parser = TabuParser(file)
    return parser.parse()


def search_rows(rows: Iterable[Dict[str, str]], term: str) -> List[Dict[str, str]]:
    """Filter rows to those containing ``term`` in either field or value.

    This helper makes the search case‑insensitive.  If ``term`` is
    falsy, all rows are returned.

    Args:
        rows: An iterable of row dictionaries as returned by
            :func:`parse_tabu_pdf`.
        term: The search term.

    Returns:
        A list of rows matching the search term.
    """
    if not term:
        return list(rows)
    term_lower = term.lower()
    return [
        r
        for r in rows
        if term_lower in r["field"].lower() or term_lower in r["value"].lower()
    ]
