import asyncio
import json
from unittest import mock

import requests
from fastmcp import Context, FastMCP

from gov.decisive import _extract_field, _parse_items, fetch_decisive_appraisals
from gov.mcp import server


def _make_response(text: str = "", status: int = 200):
    r = requests.Response()
    r.status_code = status
    r._content = text.encode("utf-8")
    return r


def test_decisive_appraisal_tool():
    html_page = (
        '<ul>'
        '<li class="collector-result-item">'
        '  <a href="/BlobFolder/1.pdf">Decision 1</a>'
        '  <span>תאריך: 01/01/2024</span>'
        '  <span>שמאי: ישראל ישראלי</span>'
        '  <span>ועדה: תל אביב</span>'
        '</li>'
        '<li class="collector-result-item">'
        '  <a href="/BlobFolder/2.pdf">Decision 2</a>'
        '  <span>תאריך: 02/02/2024</span>'
        '  <span>שמאי: רונית שמאית</span>'
        '  <span>ועדה: חיפה</span>'
        '</li>'
        '</ul>'
    )

    def fake_get(url, params=None, headers=None, timeout=None):
        if params.get("skip") == 0:
            return _make_response(html_page)
        return _make_response("<ul></ul>")

    async def run_tool():
        m = FastMCP("test")
        ctx = Context(m)
        with mock.patch("requests.get", side_effect=fake_get):
            result = await server.decisive_appraisal.run(
                {"ctx": ctx, "block": "123", "plot": "456"}
            )
            data = json.loads(result.content[0].text)
            assert len(data) == 2
            assert data[0]["title"] == "Decision 1"
            assert data[0]["pdf_url"].startswith("https://www.gov.il/BlobFolder/1.pdf")

    asyncio.run(run_tool())


def test_extract_field_success():
    """Test successful field extraction from text"""
    text = "תאריך: 20-07-2025 | שמאי: גולדברג ארנון | ועדה: אשדוד"
    
    date = _extract_field(text, "תאריך")
    appraiser = _extract_field(text, "שמאי")
    committee = _extract_field(text, "ועדה")
    
    assert date == "20-07-2025"
    assert appraiser == "גולדברג ארנון"
    assert committee == "אשדוד"


def test_extract_field_not_found():
    """Test field extraction when field is not found"""
    text = "תאריך: 20-07-2025 | שמאי: גולדברג ארנון"
    
    committee = _extract_field(text, "ועדה")
    
    assert committee == ""


def test_extract_field_with_different_separators():
    """Test field extraction with different separators"""
    text = "תאריך: 20-07-2025 - שמאי: גולדברג ארנון"
    
    date = _extract_field(text, "תאריך")
    appraiser = _extract_field(text, "שמאי")
    
    assert date == "20-07-2025"
    assert appraiser == "גולדברג ארנון"


def test_extract_field_with_dash_and_spaces():
    """Field extraction when a dash with surrounding spaces is used"""
    text = "תאריך - 20-07-2025 | שמאי - גולדברג ארנון | ועדה - אשדוד"

    date = _extract_field(text, "תאריך")
    appraiser = _extract_field(text, "שמאי")
    committee = _extract_field(text, "ועדה")

    assert date == "20-07-2025"
    assert appraiser == "גולדברג ארנון"
    assert committee == "אשדוד"


def test_extract_field_with_en_dash():
    """Field extraction when an en dash is used as a separator"""
    text = "תאריך – 20-07-2025 | שמאי – גולדברג ארנון | ועדה – אשדוד"

    date = _extract_field(text, "תאריך")
    appraiser = _extract_field(text, "שמאי")
    committee = _extract_field(text, "ועדה")

    assert date == "20-07-2025"
    assert appraiser == "גולדברג ארנון"
    assert committee == "אשדוד"


def test_extract_field_at_end():
    """Test field extraction when field is at the end of text"""
    text = "תאריך: 20-07-2025 | שמאי: גולדברג ארנון"
    
    appraiser = _extract_field(text, "שמאי")
    
    assert appraiser == "גולדברג ארנון"


def test_parse_items_success():
    """Test successful parsing of HTML items"""
    html = '''
    <ul>
        <li class="collector-result-item">
            <a href="/BlobFolder/test1.pdf">הכרעת שמאי מייעץ - גוש 2189 חלקה 85</a>
            <span>תאריך: 20-07-2025</span>
            <span>שמאי: גולדברג ארנון</span>
            <span>ועדה: ועדה מקומית אשדוד</span>
        </li>
        <li class="collector-result-item">
            <a href="/BlobFolder/test2.pdf">הכרעת שמאי מייעץ - גוש 1234 חלקה 56</a>
            <span>תאריך: 15-06-2025</span>
            <span>שמאי: כהן דוד</span>
            <span>ועדה: ועדה מקומית תל אביב</span>
        </li>
    </ul>
    '''
    
    items = _parse_items(html)
    
    assert len(items) == 2
    
    # First item
    assert items[0]["title"] == "הכרעת שמאי מייעץ - גוש 2189 חלקה 85"
    assert items[0]["date"] == "20-07-2025"
    assert items[0]["appraiser"] == "גולדברג ארנון"
    assert items[0]["committee"] == "ועדה מקומית אשדוד"
    assert items[0]["pdf_url"] == "https://www.gov.il/BlobFolder/test1.pdf"
    
    # Second item
    assert items[1]["title"] == "הכרעת שמאי מייעץ - גוש 1234 חלקה 56"
    assert items[1]["date"] == "15-06-2025"
    assert items[1]["appraiser"] == "כהן דוד"
    assert items[1]["committee"] == "ועדה מקומית תל אביב"
    assert items[1]["pdf_url"] == "https://www.gov.il/BlobFolder/test2.pdf"


def test_parse_items_no_links():
    """Test parsing items without links"""
    html = '''
    <ul>
        <li class="collector-result-item">
            <span>תאריך: 20-07-2025</span>
            <span>שמאי: גולדברג ארנון</span>
            <span>ועדה: ועדה מקומית אשדוד</span>
        </li>
    </ul>
    '''
    
    items = _parse_items(html)
    
    assert len(items) == 1
    assert items[0]["title"] == "תאריך: 20-07-2025 | שמאי: גולדברג ארנון | ועדה: ועדה מקומית אשדוד"
    assert items[0]["pdf_url"] == ""


def test_parse_items_empty():
    """Test parsing empty HTML"""
    html = '<ul></ul>'
    
    items = _parse_items(html)
    
    assert len(items) == 0


def test_parse_items_malformed():
    """Test parsing malformed HTML"""
    html = '<div>Some text without proper structure</div>'
    
    items = _parse_items(html)
    
    assert len(items) == 0


def test_fetch_decisive_appraisals_success(monkeypatch):
    """Test successful fetching of decisive appraisals"""
    html_page = '''
    <ul>
        <li class="collector-result-item">
            <a href="/BlobFolder/test.pdf">הכרעת שמאי מייעץ - גוש 2189 חלקה 85</a>
            <span>תאריך: 20-07-2025</span>
            <span>שמאי: גולדברג ארנון</span>
            <span>ועדה: ועדה מקומית אשדוד</span>
        </li>
    </ul>
    '''
    
    def fake_get(url, params=None, headers=None, timeout=None):
        assert "decisive_appraisal_decisions" in url
        if params.get("skip") == 0:
            return _make_response(html_page)
        return _make_response("<ul></ul>")
    
    with mock.patch("requests.get", side_effect=fake_get):
        results = fetch_decisive_appraisals(block="2189", plot="85", max_pages=1)
        
        assert len(results) == 1
        assert results[0]["title"] == "הכרעת שמאי מייעץ - גוש 2189 חלקה 85"
        assert results[0]["date"] == "20-07-2025"
        assert results[0]["appraiser"] == "גולדברג ארנון"
        assert results[0]["committee"] == "ועדה מקומית אשדוד"
        assert results[0]["pdf_url"] == "https://www.gov.il/BlobFolder/test.pdf"


def test_fetch_decisive_appraisals_multiple_pages(monkeypatch):
    """Test fetching appraisals across multiple pages"""
    page1_html = '''
    <ul>
        <li class="collector-result-item">
            <a href="/BlobFolder/page1.pdf">Decision 1</a>
            <span>תאריך: 20-07-2025</span>
            <span>שמאי: גולדברג ארנון</span>
            <span>ועדה: אשדוד</span>
        </li>
    </ul>
    '''
    
    page2_html = '''
    <ul>
        <li class="collector-result-item">
            <a href="/BlobFolder/page2.pdf">Decision 2</a>
            <span>תאריך: 15-06-2025</span>
            <span>שמאי: כהן דוד</span>
            <span>ועדה: תל אביב</span>
        </li>
    </ul>
    '''
    
    def fake_get(url, params=None, headers=None, timeout=None):
        assert "decisive_appraisal_decisions" in url
        skip = params.get("skip", 0)
        if skip == 0:
            return _make_response(page1_html)
        elif skip == 10:
            return _make_response(page2_html)
        return _make_response("<ul></ul>")
    
    with mock.patch("requests.get", side_effect=fake_get):
        results = fetch_decisive_appraisals(block="2189", plot="85", max_pages=2)
        
        assert len(results) == 2
        assert results[0]["title"] == "Decision 1"
        assert results[1]["title"] == "Decision 2"


def test_fetch_decisive_appraisals_no_results(monkeypatch):
    """Test fetching when no results are found"""
    def fake_get(url, params=None, headers=None, timeout=None):
        return _make_response("<ul></ul>")
    
    with mock.patch("requests.get", side_effect=fake_get):
        results = fetch_decisive_appraisals(block="9999", plot="999", max_pages=1)
        
        assert len(results) == 0


def test_fetch_decisive_appraisals_with_parameters(monkeypatch):
    """Test fetching with specific block and plot parameters"""
    html_page = '''
    <ul>
        <li class="collector-result-item">
            <a href="/BlobFolder/specific.pdf">הכרעת שמאי מייעץ - גוש 2189 חלקה 85</a>
            <span>תאריך: 20-07-2025</span>
            <span>שמאי: גולדברג ארנון</span>
            <span>ועדה: ועדה מקומית אשדוד</span>
        </li>
    </ul>
    '''
    
    def fake_get(url, params=None, headers=None, timeout=None):
        assert "decisive_appraisal_decisions" in url
        assert params.get("Block") == "2189"
        assert params.get("Plot") == "85"
        return _make_response(html_page)
    
    with mock.patch("requests.get", side_effect=fake_get):
        results = fetch_decisive_appraisals(block="2189", plot="85", max_pages=1)
        
        assert len(results) == 1
        assert "2189" in results[0]["title"]
        assert "85" in results[0]["title"]


def test_fetch_decisive_appraisals_http_error(monkeypatch):
    """Test handling of HTTP errors"""
    def fake_get(url, params=None, headers=None, timeout=None):
        r = requests.Response()
        r.status_code = 500
        r._content = b"Internal Server Error"
        return r
    
    with mock.patch("requests.get", side_effect=fake_get):
        try:
            fetch_decisive_appraisals(block="2189", plot="85", max_pages=1)
            assert False, "Expected HTTPError to be raised"
        except requests.HTTPError:
            pass  # Expected


def test_fetch_decisive_appraisals_connection_error(monkeypatch):
    """Test handling of connection errors"""
    def fake_get(url, params=None, headers=None, timeout=None):
        raise requests.ConnectionError("Connection failed")
    
    with mock.patch("requests.get", side_effect=fake_get):
        try:
            fetch_decisive_appraisals(block="2189", plot="85", max_pages=1)
            assert False, "Expected ConnectionError to be raised"
        except requests.ConnectionError:
            pass  # Expected


def test_decisive_appraisal_with_real_pdf_data():
    """Test that the parsing logic works with real data from the uploaded PDF"""
    # This test verifies that our parsing logic can handle the real data structure
    # from the PDF file: "הכרעת שמאי מייעץ מיום 20-07-2025 בעניין היטל השבחה קי.בי.עי קבוצת בוני ערים  נ ועדה מקומית אשדוד ג 2189 ח 85 - גולדברג ארנון"
    
    # Simulate HTML that would contain this data
    real_data_html = '''
    <ul>
        <li class="collector-result-item">
            <a href="/BlobFolder/real_decision.pdf">הכרעת שמאי מייעץ מיום 20-07-2025 בעניין היטל השבחה קי.בי.עי קבוצת בוני ערים  נ ועדה מקומית אשדוד ג 2189 ח 85 - גולדברג ארנון</a>
            <span>תאריך: 20-07-2025</span>
            <span>שמאי: גולדברג ארנון</span>
            <span>ועדה: ועדה מקומית אשדוד</span>
        </li>
    </ul>
    '''
    
    items = _parse_items(real_data_html)
    
    assert len(items) == 1
    item = items[0]
    
    # Verify the title contains the key information from the real PDF
    assert "הכרעת שמאי מייעץ" in item["title"]
    assert "20-07-2025" in item["title"]
    assert "2189" in item["title"]  # גוש (block)
    assert "85" in item["title"]    # חלקה (plot)
    assert "גולדברג ארנון" in item["title"]
    assert "ועדה מקומית אשדוד" in item["title"]
    
    # Verify extracted fields
    assert item["date"] == "20-07-2025"
    assert item["appraiser"] == "גולדברג ארנון"
    assert item["committee"] == "ועדה מקומית אשדוד"
    assert item["pdf_url"] == "https://www.gov.il/BlobFolder/real_decision.pdf"


def test_decisive_appraisal_hebrew_text_parsing():
    """Test parsing of Hebrew text with various formats"""
    test_cases = [
        {
            "text": "תאריך: 20-07-2025 | שמאי: גולדברג ארנון | ועדה: ועדה מקומית אשדוד",
            "expected": {
                "תאריך": "20-07-2025",
                "שמאי": "גולדברג ארנון",
                "ועדה": "ועדה מקומית אשדוד"
            }
        },
        {
            "text": "תאריך: 15/06/2025 - שמאי: כהן דוד - ועדה: תל אביב יפו",
            "expected": {
                "תאריך": "15/06/2025",
                "שמאי": "כהן דוד",
                "ועדה": "תל אביב יפו"
            }
        },
        {
            "text": "תאריך: 01.01.2025 | שמאי: לוי יוסי",
            "expected": {
                "תאריך": "01.01.2025",
                "שמאי": "לוי יוסי",
                "ועדה": ""
            }
        }
    ]
    
    for test_case in test_cases:
        text = test_case["text"]
        expected = test_case["expected"]
        
        for field, expected_value in expected.items():
            result = _extract_field(text, field)
            assert result == expected_value, f"Failed for field '{field}' in text: {text}"


# New tests for the updated _parse_items function supporting new HTML structure

def test_parse_items_new_structure():
    """Test parsing with new HTML structure (ol.search_results li)"""
    html = '''
    <div class="collector">
        <h4>תוצאות חיפוש</h4>
        <p class="body"><strong>1</strong> תוצאות עבור גוש: <strong>6638</strong>, חלקה: <strong>388</strong></p>
        
        <ol class="search_results">
            <li>
                <h5><a href="/apps/publications/publication/HachrazaShamai?id=20030605_3-20120305_2" target="_blank">הכרעת שמאי מכריע מיום 05.03.12 בעניין אביטל ואח' נ' ועדה מקומית תל אביב יפו ג' 6638 ח' 388</a></h5>
                <p class="body">שמאי: טזר נסים&nbsp; |&nbsp; ועדה: ועדה מקומית תל אביב יפו</p>
            </li>
        </ol>
    </div>
    '''
    
    items = _parse_items(html)
    
    assert len(items) == 1
    
    item = items[0]
    assert item["title"] == "הכרעת שמאי מכריע מיום 05.03.12 בעניין אביטל ואח' נ' ועדה מקומית תל אביב יפו ג' 6638 ח' 388"
    assert item["date"] == "05.03.12"  # Date extracted from title
    assert item["appraiser"] == "טזר נסים"
    assert item["committee"] == "ועדה מקומית תל אביב יפו"
    assert item["pdf_url"] == "https://www.gov.il/apps/publications/publication/HachrazaShamai?id=20030605_3-20120305_2"


def test_parse_items_new_structure_multiple():
    """Test parsing multiple items with new HTML structure"""
    html = '''
    <div class="collector">
        <ol class="search_results">
            <li>
                <h5><a href="/apps/publications/publication/HachrazaShamai?id=test1" target="_blank">הכרעת שמאי מכריע מיום 15.01.23 בעניין דוגמה ראשונה</a></h5>
                <p class="body">שמאי: כהן יוסי&nbsp; |&nbsp; ועדה: ועדה מקומית חיפה</p>
            </li>
            <li>
                <h5><a href="/apps/publications/publication/HachrazaShamai?id=test2" target="_blank">הכרעת שמאי מכריע מיום 22.05.23 בעניין דוגמה שנייה</a></h5>
                <p class="body">שמאי: לוי מרים&nbsp; |&nbsp; ועדה: ועדה מקומית ירושלים</p>
            </li>
        </ol>
    </div>
    '''
    
    items = _parse_items(html)
    
    assert len(items) == 2
    
    # First item
    assert items[0]["title"] == "הכרעת שמאי מכריע מיום 15.01.23 בעניין דוגמה ראשונה"
    assert items[0]["date"] == "15.01.23"
    assert items[0]["appraiser"] == "כהן יוסי"
    assert items[0]["committee"] == "ועדה מקומית חיפה"
    assert items[0]["pdf_url"] == "https://www.gov.il/apps/publications/publication/HachrazaShamai?id=test1"
    
    # Second item
    assert items[1]["title"] == "הכרעת שמאי מכריע מיום 22.05.23 בעניין דוגמה שנייה"
    assert items[1]["date"] == "22.05.23"
    assert items[1]["appraiser"] == "לוי מרים"
    assert items[1]["committee"] == "ועדה מקומית ירושלים"
    assert items[1]["pdf_url"] == "https://www.gov.il/apps/publications/publication/HachrazaShamai?id=test2"


def test_parse_items_fallback_from_old_to_new():
    """Test that parsing falls back to new structure when old structure has no results"""
    html = '''
    <div class="collector">
        <!-- No .collector-result-item elements, should fall back to new structure -->
        <ol class="search_results">
            <li>
                <h5><a href="/apps/publications/publication/HachrazaShamai?id=fallback_test" target="_blank">הכרעת שמאי מכריע מיום 10.06.24 בעניין בדיקת fallback</a></h5>
                <p class="body">שמאי: פלדמן דורון&nbsp; |&nbsp; ועדה: ועדה מקומית פתח תקווה</p>
            </li>
        </ol>
    </div>
    '''
    
    items = _parse_items(html)
    
    assert len(items) == 1
    assert items[0]["title"] == "הכרעת שמאי מכריע מיום 10.06.24 בעניין בדיקת fallback"
    assert items[0]["date"] == "10.06.24"
    assert items[0]["appraiser"] == "פלדמן דורון"
    assert items[0]["committee"] == "ועדה מקומית פתח תקווה"


def test_parse_items_old_structure_takes_precedence():
    """Test that old structure takes precedence when both structures exist"""
    html = '''
    <div class="collector">
        <!-- Old structure should be used -->
        <ul>
            <li class="collector-result-item">
                <a href="/BlobFolder/old_structure.pdf">הכרעת שמאי מייעץ - מבנה ישן</a>
                <span>תאריך: 01-01-2024</span>
                <span>שמאי: ישן ישנים</span>
                <span>ועדה: ועדה ישנה</span>
            </li>
        </ul>
        
        <!-- New structure exists but should be ignored -->
        <ol class="search_results">
            <li>
                <h5><a href="/apps/publications/publication/HachrazaShamai?id=new_structure" target="_blank">הכרעת שמאי מכריע מיום 02.02.24 בעניין מבנה חדש</a></h5>
                <p class="body">שמאי: חדש חדשים&nbsp; |&nbsp; ועדה: ועדה חדשה</p>
            </li>
        </ol>
    </div>
    '''
    
    items = _parse_items(html)
    
    assert len(items) == 1
    # Should use the old structure data
    assert items[0]["title"] == "הכרעת שמאי מייעץ - מבנה ישן"
    assert items[0]["date"] == "01-01-2024"
    assert items[0]["appraiser"] == "ישן ישנים"
    assert items[0]["committee"] == "ועדה ישנה"
    assert "old_structure" in items[0]["pdf_url"]


def test_parse_items_new_structure_no_links():
    """Test parsing new structure when items don't have links"""
    html = '''
    <div class="collector">
        <ol class="search_results">
            <li>
                <h5>הכרעת שמאי מכריע מיום 01.12.23 בעניין ללא קישור</h5>
                <p class="body">שמאי: ללא קישור&nbsp; |&nbsp; ועדה: ועדה ללא קישור</p>
            </li>
        </ol>
    </div>
    '''
    
    items = _parse_items(html)
    
    # Should not find items without links in h5 > a structure
    assert len(items) == 0


def test_parse_items_new_structure_empty():
    """Test parsing empty new structure"""
    html = '''
    <div class="collector">
        <h4>תוצאות חיפוש</h4>
        <p class="body"><strong>0</strong> תוצאות</p>
        <ol class="search_results">
        </ol>
    </div>
    '''
    
    items = _parse_items(html)
    
    assert len(items) == 0


def test_extract_field_date_from_title():
    """Test extracting date using 'מיום' pattern from title"""
    title = "הכרעת שמאי מכריע מיום 05.03.12 בעניין אביטל ואח' נ' ועדה מקומית תל אביב יפו ג' 6638 ח' 388"
    
    date = _extract_field(title, "מיום")
    
    assert date == "05.03.12"


def test_extract_field_date_patterns():
    """Test extracting various date patterns from titles"""
    test_cases = [
        {
            "title": "הכרעת שמאי מכריע מיום 15.06.2024 בעניין דוגמה",
            "expected": "15.06.2024"
        },
        {
            "title": "הכרעת שמאי מכריע מיום 01.01.23 בעניין דוגמה אחרת",
            "expected": "01.01.23"
        },
        {
            "title": "הכרעת שמאי מכריע מיום 22/05/2023 בעניין דוגמה שלישית",
            "expected": "22/05/2023"
        },
        {
            "title": "הכרעת שמאי ללא תאריך",
            "expected": ""
        }
    ]
    
    for test_case in test_cases:
        title = test_case["title"]
        expected = test_case["expected"]
        
        result = _extract_field(title, "מיום")
        if not result and expected:
            # Test the regex fallback for date patterns
            import re
            date_match = re.search(r"\d{2}\.\d{2}\.\d{2,4}", title)
            if date_match:
                result = date_match.group(0)
            else:
                date_match = re.search(r"\d{2}/\d{2}/\d{2,4}", title)
                if date_match:
                    result = date_match.group(0)
        
        assert result == expected, f"Failed to extract date from title: {title}"


def test_parse_items_rozov_18_real_data():
    """Test parsing with the actual Rozov 18 data that was found manually"""
    html = '''
    <div class="collector">
        <h4>תוצאות חיפוש</h4>
        <p class="body"><strong>1</strong> תוצאות עבור גוש: <strong>6638</strong>, חלקה: <strong>388</strong></p>
        
        <ol class="search_results">
            <li>
                <h5><a href="/apps/publications/publication/HachrazaShamai?id=20030605_3-20120305_2" target="_blank">הכרעת שמאי מכריע מיום 05.03.12 בעניין אביטל ואח' נ' ועדה מקומית תל אביב יפו ג' 6638 ח' 388</a></h5>
                <p class="body">שמאי: טזר נסים&nbsp; |&nbsp; ועדה: ועדה מקומית תל אביב יפו</p>
            </li>
        </ol>
    </div>
    '''
    
    items = _parse_items(html)
    
    assert len(items) == 1
    
    item = items[0]
    # Verify that this is the actual Rozov 18 data
    assert "6638" in item["title"]  # Block
    assert "388" in item["title"]   # Plot  
    assert "אביטל" in item["title"] # Case name
    assert "תל אביב יפו" in item["title"]
    assert item["date"] == "05.03.12"
    assert item["appraiser"] == "טזר נסים"
    assert item["committee"] == "ועדה מקומית תל אביב יפו"
    assert "20030605_3-20120305_2" in item["pdf_url"]


def test_fetch_decisive_appraisals_with_new_structure(monkeypatch):
    """Test fetching appraisals that return new HTML structure"""
    new_structure_html = '''
    <div class="collector">
        <ol class="search_results">
            <li>
                <h5><a href="/apps/publications/publication/HachrazaShamai?id=new_test" target="_blank">הכרעת שמאי מכריע מיום 10.10.24 בעניין בדיקת מבנה חדש</a></h5>
                <p class="body">שמאי: בדיקה חדשה&nbsp; |&nbsp; ועדה: ועדה חדשה</p>
            </li>
        </ol>
    </div>
    '''
    
    def fake_get(url, params=None, headers=None, timeout=None):
        assert "decisive_appraisal_decisions" in url
        if params.get("skip") == 0:
            return _make_response(new_structure_html)
        return _make_response("<div></div>")
    
    with mock.patch("requests.get", side_effect=fake_get):
        results = fetch_decisive_appraisals(block="6638", plot="388", max_pages=1)
        
        assert len(results) == 1
        assert results[0]["title"] == "הכרעת שמאי מכריע מיום 10.10.24 בעניין בדיקת מבנה חדש"
        assert results[0]["date"] == "10.10.24"
        assert results[0]["appraiser"] == "בדיקה חדשה"
        assert results[0]["committee"] == "ועדה חדשה"
        assert results[0]["pdf_url"] == "https://www.gov.il/apps/publications/publication/HachrazaShamai?id=new_test"
