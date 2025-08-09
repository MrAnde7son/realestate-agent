from datetime import datetime
from yad2.core.models import RealEstateListing


def test_real_estate_listing_to_dict_and_str():
    listing = RealEstateListing()
    listing.title = 'Cozy Apartment'
    listing.price = 1200000
    listing.address = 'Main St, Tel Aviv'
    listing.rooms = 3

    data = listing.to_dict()
    assert data['title'] == 'Cozy Apartment'
    assert data['price'] == 1200000
    assert data['address'] == 'Main St, Tel Aviv'
    assert 'scraped_at' in data
    # ensure scraped_at is isoformat
    datetime.fromisoformat(data['scraped_at'])

    text = str(listing)
    assert 'Cozy Apartment' in text
    assert '1200000' in text
    assert 'Main St, Tel Aviv' in text
    assert repr(listing) == text
