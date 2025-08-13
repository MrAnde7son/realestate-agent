import pytest
from bs4 import BeautifulSoup

from utils.yad2_scraper import Yad2Parser
from utils.madlan_scraper import MadlanParser


def test_yad2_parse_listing_card_handles_missing_sqm():
    html = """
    <div class='card_cardBox__KLi9I'>
        <span data-testid='price'>1,000,000 ₪</span>
        <span class='item-data-content_heading__tphH4'>Main St</span>
        <span class='item-data-content_itemInfoLine__AeoPP'>desc line 1</span>
        <span class='item-data-content_itemInfoLine__AeoPP'>3 חד • 1 קומה</span>
    </div>
    """
    card = BeautifulSoup(html, 'html.parser')
    result = Yad2Parser.parse_listing_card(card)
    assert result["price"] == "1,000,000 ₪"
    assert result["address"] == "Main St"
    assert result["address_description"] == "desc line 1"
    assert result["bedroom"] is None
    assert result["floor"] == "3 חד"
    assert result["sqm"] == "1 קומה"


def test_yad2_extract_helpers():
    html = """
    <div>
        <dd class='item-detail_label__FnhAu'>חדרים</dd>
        <dt class='item-detail_value__QHPml'>4</dt>
        <dd class='item-detail_label__FnhAu'>מ"ר</dd>
        <dt class='item-detail_value__QHPml'>100</dt>
    </div>
    <ul>
        <li data-testid='in-property-item'><span class='in-property-item_text__aLvx0'>מרפסת</span></li>
        <li data-testid='in-property-item'></li>
    </ul>
    """
    soup = BeautifulSoup(html, 'html.parser')
    details = Yad2Parser.extract_item_details(soup)
    assert details == {"חדרים": "4", 'מ"ר': "100"}
    features = Yad2Parser.extract_features(soup)
    assert features == ["מרפסת"]


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
