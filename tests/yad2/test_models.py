from datetime import datetime

from yad2.core.models import Contact, RealEstateListing


def test_real_estate_listing_to_dict_and_str():
    listing = RealEstateListing()
    listing.title = "Cozy Apartment"
    listing.price = 1200000
    listing.address = "Main St, Tel Aviv"
    listing.rooms = 3
    listing.size = 75
    listing.total_size = 110
    listing.documents = [{"type": "tabu", "url": "http://example.com/tabu.pdf"}]
    listing.images = ["http://example.com/image.jpg"]
    listing.video = "http://example.com/video.mp4"
    listing.contact_info = Contact(name="Dana", phone="050-1234567")
    listing.listing_type = "sale"
    listing.ad_type = "private"
    listing.recent_deal = True

    data = listing.to_dict()
    assert data["title"] == "Cozy Apartment"
    assert data["price"] == 1200000
    assert data["address"] == "Main St, Tel Aviv"
    assert "scraped_at" in data
    assert data["documents"] == [{"type": "tabu", "url": "http://example.com/tabu.pdf"}]
    assert data["images"] == ["http://example.com/image.jpg"]
    assert data["photos"] == ["http://example.com/image.jpg"]
    assert data["video"] == "http://example.com/video.mp4"
    assert data["contact_name"] == "Dana"
    assert data["contact_phone"] == "050-1234567"
    assert data["contact_info"]["name"] == "Dana"
    assert data["listing_type"] == "sale"
    assert data["ad_type"] == "private"
    assert data["recent_deal"] is True
    assert data["size"] == 75
    assert data["total_size"] == 110
    # ensure scraped_at is isoformat
    datetime.fromisoformat(data["scraped_at"])

    text = str(listing)
    assert "Cozy Apartment" in text
    assert "1200000" in text
    assert "Main St, Tel Aviv" in text
    assert repr(listing) == text


def test_contact_preserves_broker_metadata():
    brokers = [{"name": "Agent Smith", "id": "10596", "licenseNumber": "31102707"}]
    contact = Contact(
        id=6365987,
        name="Shahar Rabinovich",
        phone="053-3739795",
        brokerPhone="053-3739795",
        isVirtualPhoneNumber=True,
        agencyName="Yesh Nadlan",
        agencyLogo="//images.yad2.co.il/logo.jpg",
        brokerAvatar="https://img.yad2.co.il/avatar.jpg",
        agencyAbout="About the agency",
        brokers=brokers,
        licenseNumber=31102707,
    )

    contact_dict = contact.to_dict()
    assert contact_dict["id"] == 6365987
    assert contact_dict["isVirtualPhoneNumber"] is True
    assert contact_dict["agencyName"] == "Yesh Nadlan"
    assert contact_dict["agencyLogo"] == "//images.yad2.co.il/logo.jpg"
    assert contact_dict["brokerAvatar"] == "https://img.yad2.co.il/avatar.jpg"
    assert contact_dict["agencyAbout"] == "About the agency"
    assert contact_dict["brokers"] == brokers
    assert contact_dict["licenseNumber"] == 31102707

    listing = RealEstateListing(contact_info=contact)
    listing_dict = listing.to_dict()
    assert listing_dict["contact_info"]["agencyName"] == "Yesh Nadlan"
    assert listing_dict["contact_info"]["brokers"] == brokers
