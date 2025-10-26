from datetime import datetime

from yad2.core.models import Contact, RealEstateListing


def test_real_estate_listing_to_dict_and_str():
    listing = RealEstateListing()
    listing.title = 'Cozy Apartment'
    listing.price = 1200000
    listing.address = 'Main St, Tel Aviv'
    listing.rooms = 3
    listing.documents = [{'type': 'tabu', 'url': 'http://example.com/tabu.pdf'}]
    listing.images = ['http://example.com/image.jpg']
    listing.video = 'http://example.com/video.mp4'
    listing.contact_info = Contact(name='Dana', phone='050-1234567')
    listing.listing_type = 'sale'
    listing.ad_type = 'private'
    listing.recent_deal = True

    data = listing.to_dict()
    assert data['title'] == 'Cozy Apartment'
    assert data['price'] == 1200000
    assert data['address'] == 'Main St, Tel Aviv'
    assert 'scraped_at' in data
    assert data['documents'] == [{'type': 'tabu', 'url': 'http://example.com/tabu.pdf'}]
    assert data['images'] == ['http://example.com/image.jpg']
    assert data['photos'] == ['http://example.com/image.jpg']
    assert data['video'] == 'http://example.com/video.mp4'
    assert data['contact_name'] == 'Dana'
    assert data['contact_phone'] == '050-1234567'
    assert data['contact_info']['name'] == 'Dana'
    assert data['listing_type'] == 'sale'
    assert data['ad_type'] == 'private'
    assert data['recent_deal'] is True
    # ensure scraped_at is isoformat
    datetime.fromisoformat(data['scraped_at'])

    text = str(listing)
    assert 'Cozy Apartment' in text
    assert '1200000' in text
    assert 'Main St, Tel Aviv' in text
    assert repr(listing) == text
