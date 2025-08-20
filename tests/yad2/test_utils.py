from yad2.core.utils import URLUtils, DataUtils
from yad2.core.models import RealEstateListing


def make_listing(price=None, rooms=None, address=None):
    listing = RealEstateListing()
    listing.price = price
    listing.rooms = rooms
    listing.address = address
    return listing


def test_urlutils_clean_price():
    assert URLUtils.clean_price('₪1,200,000') == 1200000
    assert URLUtils.clean_price('NIS 950000') == 950000
    assert URLUtils.clean_price('10,500,000 שח') == 10500000
    assert URLUtils.clean_price('') is None
    # Non-numeric price should be returned as cleaned text
    assert URLUtils.clean_price('approx') == 'approx'


def test_urlutils_extract_number():
    assert URLUtils.extract_number('3 Rooms') == 3.0
    assert URLUtils.extract_number('No number') is None
    assert URLUtils.extract_number(None) is None


def test_urlutils_extract_listing_id():
    assert URLUtils.extract_listing_id('https://www.yad2.co.il/item/1234567') == '1234567'
    assert URLUtils.extract_listing_id('https://www.yad2.co.il/item/1234567/') == '1234567'
    assert URLUtils.extract_listing_id('https://example.com') is None
    assert URLUtils.extract_listing_id(None) is None


def test_datautils_calculate_price_stats():
    listings = [make_listing(price=p) for p in (100, 200, 300)]
    stats = DataUtils.calculate_price_stats(listings)
    assert stats['count'] == 3
    assert stats['average'] == 200
    assert stats['median'] == 200
    assert stats['min'] == 100
    assert stats['max'] == 300
    assert DataUtils.calculate_price_stats([make_listing()]) is None


def test_datautils_group_and_filter():
    listings = [
        make_listing(price=100, rooms=2, address='Street A, Tel Aviv'),
        make_listing(price=200, rooms=3, address='Street B, Haifa'),
        make_listing(price=300, rooms=4, address='Street C, Tel Aviv'),
    ]
    groups = DataUtils.group_by_location(listings)
    assert set(groups.keys()) == {'Tel Aviv', 'Haifa'}
    assert len(groups['Tel Aviv']) == 2
    filtered = DataUtils.filter_by_criteria(listings, min_price=150, max_price=250)
    assert len(filtered) == 1 and filtered[0].price == 200
    room_filtered = DataUtils.filter_by_criteria(listings, min_rooms=3, max_rooms=4)
    assert [l.rooms for l in room_filtered] == [3, 4]
    # Ensure listings with too many rooms are excluded
    limited_rooms = DataUtils.filter_by_criteria(listings, max_rooms=3)
    assert [l.rooms for l in limited_rooms] == [2, 3]
