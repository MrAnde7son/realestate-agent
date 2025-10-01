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

from typing import IO, Dict, Iterable, List, Set, Tuple
import re

import pdfplumber


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
    if name and re.search(r'[א-ת]', name):
        if name in {"בעלים", "הבעלים", "בעלי המשכנתה"}:
            name = None
        else:
            hebrew_only = ''.join(ch for ch in name if 'א' <= ch <= 'ת')
            if len(hebrew_only) < 2:
                name = None
    else:
        name = None
    return name, action, date


def parse_tabu_pdf(file: IO) -> List[Dict[str, str]]:
    """Parse a Tabu (land registry) PDF into a list of rows.

    Each extracted piece of information is returned as a dictionary with
    two keys: ``field`` (the label) and ``value`` (the data).  The
    function attempts to extract parcel identifiers, ownership shares,
    identification numbers, dates, owner names and generic key/value
    pairs.  It does not rely on hard‑coded ID numbers or specific
    document layouts.

    Args:
        file: A file‑like object positioned at the start of the PDF.

    Returns:
        A list of dictionaries representing the extracted rows.
    """
    rows: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str]] = set()  # track (field, value) to avoid duplicates
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            # Split into non‑empty lines and normalise whitespace
            lines = [re.sub(r"\s+", " ", line.strip()) for line in text.splitlines() if line.strip()]
            for line in lines:
                # 1. Extract parcel information (גוש, חלקה, תת חלקה)
                for keyword, field_name in [("גוש", "גוש"), ("חלקה", "חלקה"), ("תת חלקה", "תת חלקה")]:
                    value = _extract_number_near_field(line, keyword)
                    if value and (field_name, value) not in seen:
                        rows.append({'field': field_name, 'value': value})
                        seen.add((field_name, value))

                # 2. Extract ownership share fractions like "1/2" or "68/509"
                # Look for ownership share fractions like "1/2" or "68/509".  To avoid
                # picking up dates or instrument numbers (e.g. "05/2013"), we require
                # both the numerator and denominator to be relatively short (1‑3 digits).
                # Look for ownership share fractions like "1/2" or "68/509".  To avoid
                # picking up dates (e.g. "28/12/2023") or instrument numbers (e.g. "18251/2013/1"), we
                # require both the numerator and denominator to be 1–3 digits and ensure the match
                # is not immediately followed by another slash.
                frac = re.search(r"\b(\d{1,3})\s*/\s*(\d{1,3})\b(?!\s*/)", line)
                if frac:
                    value = f"{frac.group(1)}/{frac.group(2)}"
                    field = 'החלק בנכס'
                    if (field, value) not in seen:
                        rows.append({'field': field, 'value': value})
                        seen.add((field, value))
                # Also handle the special case where the share is expressed as the
                # Hebrew word "בשלמות" (meaning full ownership).  This appears on its
                # own line and does not contain a fraction.
                if 'בשלמות' in line and ('החלק בנכס', 'בשלמות') not in seen:
                    rows.append({'field': 'החלק בנכס', 'value': 'בשלמות'})
                    seen.add(('החלק בנכס', 'בשלמות'))

                # 3. Extract ID numbers (8 or 9 digit numbers) that are not part of instrument numbers
                for id_match in re.findall(r"\b\d{8,9}\b", line):
                    field = 'מספר זיהוי'
                    value = id_match
                    if (field, value) not in seen:
                        rows.append({'field': field, 'value': value})
                        seen.add((field, value))

                # 4. Extract dates (DD/MM/YYYY)
                for date_match in re.findall(r"\b\d{2}/\d{2}/\d{4}\b", line):
                    field = 'תאריך'
                    value = date_match
                    if (field, value) not in seen:
                        rows.append({'field': field, 'value': value})
                        seen.add((field, value))

                # 5. Extract owner names, actions and dates from lines containing Hebrew letters and digits.
                #    Only attempt this heuristic if the line contains a known action keyword or a date; this
                #    avoids misclassifying unrelated lines (e.g. descriptions or headers) as names.
                if re.search(r'[א-ת]', line) and re.search(r'\d', line):
                    has_date = bool(re.search(r"\b\d{2}/\d{2}/\d{4}\b", line))
                    # List of action keywords as used in _extract_owner_line
                    _actions = ["מכר", "משכנתה", "מתנה", "הקניית", "הערת"]
                    has_action = any(act in line for act in _actions)
                    if has_date or has_action:
                        name, action, date = _extract_owner_line(line)
                        if name and ('בעלים', name) not in seen:
                            rows.append({'field': 'בעלים', 'value': name})
                            seen.add(('בעלים', name))
                        if action and ('מהות פעולה', action) not in seen:
                            rows.append({'field': 'מהות פעולה', 'value': action})
                            seen.add(('מהות פעולה', action))
                        if date and ('תאריך', date) not in seen:
                            rows.append({'field': 'תאריך', 'value': date})
                            seen.add(('תאריך', date))

                # 6. Generic key/value pairs separated by a single colon (exclude parcel keywords)
                if ':' in line and line.count(':') == 1:
                    key, value = [part.strip() for part in line.split(':', 1)]
                    if key and value:
                        # Skip if the key appears to be part of the parcel header (גוש/חלקה/תת חלקה)
                        if not any(k in key for k in ['גוש', 'חלקה', 'תת חלקה']):
                            if (key, value) not in seen:
                                rows.append({'field': key, 'value': value})
                                seen.add((key, value))
    return rows


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
    return [r for r in rows if term_lower in r['field'].lower() or term_lower in r['value'].lower()]