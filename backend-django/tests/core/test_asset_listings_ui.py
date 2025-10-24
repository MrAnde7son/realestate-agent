from django.test import TestCase

from core.models import Asset, Listing


class AssetListingsUiTests(TestCase):
    def setUp(self):
        self.asset_rent = Asset.objects.create(scope_type="address", city="Tel Aviv")
        self.asset_sale = Asset.objects.create(scope_type="address", city="Tel Aviv")

        self.listing_rent = Listing.objects.create(
            source="yad2",
            external_id="rent-1",
            title="דירת 3 חדרים",
            listing_type="rent",
            contact_name="Dana",
            contact_phone="050-1234567",
            recent_deal=True,
            photos=["http://example.com/photo.jpg"],
            video_url="http://example.com/video.mp4",
        )
        self.listing_rent.assets.add(self.asset_rent)

        self.listing_sale = Listing.objects.create(
            source="yad2",
            external_id="sale-1",
            title="בית פרטי",
            listing_type="sale",
            contact_name="Ronen",
            contact_phone="050-7654321",
            recent_deal=False,
        )
        self.listing_sale.assets.add(self.asset_sale)

    def test_assets_endpoint_includes_primary_listing_fields(self):
        response = self.client.get("/api/assets")
        self.assertEqual(response.status_code, 200)

        rows = response.json()["rows"]
        asset_row = next(row for row in rows if row["id"] == self.asset_rent.id)

        self.assertEqual(asset_row.get("listingType"), "rent")
        self.assertEqual(asset_row.get("contactName"), "Dana")
        self.assertEqual(asset_row.get("contactPhone"), "050-1234567")
        self.assertTrue(asset_row.get("recentDeal"))
        self.assertEqual(asset_row.get("videoUrl"), "http://example.com/video.mp4")
        self.assertIn("http://example.com/photo.jpg", asset_row.get("photos", []))

        primary = asset_row.get("primaryListing")
        self.assertIsNotNone(primary)
        self.assertEqual(primary.get("listing_type"), "rent")
        self.assertTrue(primary.get("recent_deal"))
        self.assertEqual(primary.get("contact_name"), "Dana")
        self.assertEqual(primary.get("contact_phone"), "050-1234567")
        self.assertEqual(primary.get("video_url"), "http://example.com/video.mp4")
        self.assertIn("http://example.com/photo.jpg", primary.get("photos", []))

    def test_assets_rental_sale_filter_uses_listing_type(self):
        response = self.client.get("/api/assets", {"rentalSale": "rent"})
        self.assertEqual(response.status_code, 200)

        rent_ids = {row["id"] for row in response.json()["rows"]}
        self.assertIn(self.asset_rent.id, rent_ids)
        self.assertNotIn(self.asset_sale.id, rent_ids)

    def test_asset_listings_endpoint_includes_contact_and_media(self):
        response = self.client.get(f"/api/assets/{self.asset_rent.id}/listings")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data.get("count"), 1)

        listing = data["results"][0]
        self.assertEqual(listing.get("listing_type"), "rent")
        self.assertTrue(listing.get("recent_deal"))
        self.assertEqual(listing.get("contact_name"), "Dana")
        self.assertEqual(listing.get("contact_phone"), "050-1234567")
        self.assertIn("http://example.com/photo.jpg", listing.get("photos", []))
        self.assertEqual(listing.get("video_url"), "http://example.com/video.mp4")

        contact_info = listing.get("contact_info") or {}
        self.assertEqual(contact_info.get("name"), "Dana")
        self.assertEqual(contact_info.get("phone"), "050-1234567")

        listing_filters = data.get("filters", {})
        self.assertIn("rent", listing_filters.get("listing_type", []))
