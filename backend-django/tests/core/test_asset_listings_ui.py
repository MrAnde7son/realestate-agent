from django.test import TestCase

from core.models import Asset, Listing


class AssetListingsUiTests(TestCase):
    def setUp(self):
        self.asset_rent = Asset.objects.create(
            scope_type="address",
            city="Tel Aviv",
            normalized_address="test street 1",
        )
        self.asset_sale = Asset.objects.create(
            scope_type="address",
            city="Tel Aviv",
            normalized_address="test street 2",
        )

        self.listing_rent = Listing.objects.create(
            source="yad2",
            external_id="rent-1",
            title="דירת 3 חדרים",
            listing_type="rent",
            ad_type="private",
            contact_name="Dana",
            contact_phone="050-1234567",
            recent_deal=True,
            photos=["http://example.com/photo.jpg"],
            video_url="http://example.com/video.mp4",
            address="test street 1",
        )
        self.listing_rent.assets.add(self.asset_rent)

        self.listing_sale = Listing.objects.create(
            source="yad2",
            external_id="sale-1",
            title="בית פרטי",
            listing_type="sale",
            ad_type="broker",
            contact_name="Ronen",
            contact_phone="050-7654321",
            recent_deal=False,
            address="test street 2",
        )
        self.listing_sale.assets.add(self.asset_sale)

    def test_assets_endpoint_includes_primary_listing_fields(self):
        response = self.client.get("/api/assets")
        self.assertEqual(response.status_code, 200)

        rows = response.json()["rows"]
        asset_row = next(row for row in rows if row["id"] == self.asset_rent.id)

        self.assertEqual(asset_row.get("listing_type"), "rent")
        self.assertEqual(asset_row.get("ad_type"), "private")
        self.assertEqual(asset_row.get("contact_name"), "Dana")
        self.assertEqual(asset_row.get("contact_phone"), "050-1234567")
        self.assertTrue(asset_row.get("recent_deal"))
        self.assertEqual(asset_row.get("video_url"), "http://example.com/video.mp4")
        self.assertIn("http://example.com/photo.jpg", asset_row.get("photos", []))

        primary = asset_row.get("primary_listing")
        self.assertIsNotNone(primary)
        self.assertEqual(primary.get("listing_type"), "rent")
        self.assertEqual(primary.get("ad_type"), "private")
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
        self.assertEqual(listing.get("ad_type"), "private")
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
        self.assertIn("private", listing_filters.get("ad_type", []))

    def test_assets_ad_type_filter_uses_listing_ad_type(self):
        response = self.client.get("/api/assets", {"adType": "private"})
        self.assertEqual(response.status_code, 200)

        private_ids = {row["id"] for row in response.json()["rows"]}
        self.assertIn(self.asset_rent.id, private_ids)
        self.assertNotIn(self.asset_sale.id, private_ids)
