from django.test import TestCase

from core.models import Asset


class AssetLegacyRoutesTest(TestCase):
    def setUp(self):
        self.asset = Asset.objects.create(
            scope_type="address",
            city="Tel Aviv",
            street="Main St",
            number=10,
        )

    def test_asset_detail_available_without_api_prefix(self):
        api_response = self.client.get(f"/api/assets/{self.asset.id}/")
        legacy_response = self.client.get(f"/assets/{self.asset.id}/")

        self.assertEqual(api_response.status_code, 200)
        self.assertEqual(legacy_response.status_code, 200)
        self.assertEqual(api_response.json(), legacy_response.json())
        self.assertEqual(
            legacy_response.json().get("asset", {}).get("id"),
            self.asset.id,
        )

    def test_asset_rights_available_without_api_prefix(self):
        response = self.client.get(f"/assets/{self.asset.id}/rights/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("tabu_data", response.json())

    def test_asset_collection_available_without_api_prefix(self):
        response = self.client.get("/assets/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("rows", body)
        self.assertGreaterEqual(body.get("pagination", {}).get("total", 0), 1)
