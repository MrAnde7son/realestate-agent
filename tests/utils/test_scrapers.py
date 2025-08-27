from bs4 import BeautifulSoup

from utils.madlan_scraper import MadlanParser


def test_madlan_extract_listing_card_and_details():
    card_html = """
    <div>
        <div data-auto='property-price'>1,200,000₪</div>
        <div data-auto='property-address'>רחוב הדגמה</div>
        <div data-auto='property-rooms'>4</div>
        <div data-auto='property-floor'>2</div>
        <div data-auto='property-size'>100</div>
    </div>
    """
    card = BeautifulSoup(card_html, 'html.parser')
    info = MadlanParser.extract_listing_card_info(card)
    assert info == {
        "price": "1,200,000₪",
        "address": "רחוב הדגמה",
        "rooms": "4",
        "floor": "2",
        "area_sqm": "100",
        "property_type": None,
    }

    detail_html = """
    <div data-testid='description'>תיאור</div>
    <div data-testid='feature'>מעלית</div>
    <dl>
        <dt>גג</dt><dd>יש</dd>
    </dl>
    """
    soup = BeautifulSoup(detail_html, 'html.parser')
    details = MadlanParser.extract_detailed_info(soup)
    assert details["description"] == "תיאור"
    assert details["features"] == ["מעלית"]
    assert details["additional_details"] == {"גג": "יש"}
