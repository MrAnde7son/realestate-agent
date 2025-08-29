from typing import IO, Dict, Iterable, List

import pdfplumber


def parse_tabu_pdf(file: IO) -> List[Dict[str, str]]:
    """Parse a Tabu (land registry) PDF into a list of rows.

    Each line formatted as ``key: value`` becomes a row ``{"field": key, "value": value}``.
    Non-conforming lines are ignored.
    The function accepts a file-like object positioned at the start of the PDF.
    """
    rows: List[Dict[str, str]] = []
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if not line or ':' not in line:
                    continue
                key, value = line.split(':', 1)
                rows.append({'field': key.strip(), 'value': value.strip()})
    return rows


def search_rows(rows: Iterable[Dict[str, str]], term: str) -> List[Dict[str, str]]:
    """Filter rows to those containing ``term`` in either field or value."""
    if not term:
        return list(rows)
    term_lower = term.lower()
    return [r for r in rows if term_lower in r['field'].lower() or term_lower in r['value'].lower()]
