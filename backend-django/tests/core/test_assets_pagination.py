from django.core.cache import cache
from django.test import TestCase

from core.models import Asset
from core.views import MAX_ASSET_PAGE_SIZE


class AssetsPaginationTests(TestCase):
    def setUp(self):
        """Clear cache before each test to ensure fresh metadata."""
        cache.clear()

    @classmethod
    def setUpTestData(cls):
        cls.asset_ids = []
        for i in range(30):
            asset = Asset.objects.create(
                scope_type="address",
                city="CityA" if i < 20 else "CityB",
                price=100000 + i,
                status="done" if i % 2 == 0 else "pending",
            )
            cls.asset_ids.append(asset.id)

        commercial_asset = Asset.objects.create(
            scope_type="address",
            city="CityC",
            price=500000,
            status="done",
            is_commercial=True,
        )
        cls.asset_ids.append(commercial_asset.id)

    def test_default_pagination_returns_first_page(self):
        response = self.client.get("/api/assets")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("rows", data)
        self.assertIn("pagination", data)
        self.assertEqual(len(data["rows"]), 25)

        pagination = data["pagination"]
        self.assertEqual(pagination["page"], 1)
        self.assertEqual(pagination["page_size"], 25)
        total_assets = Asset.objects.count()
        self.assertEqual(pagination["total"], total_assets)
        self.assertEqual(pagination["has_next"], total_assets > pagination["page_size"])
        self.assertFalse(pagination["has_previous"])

    def test_custom_page_and_size(self):
        first_response = self.client.get("/api/assets", {"pageSize": 10})
        self.assertEqual(first_response.status_code, 200)

        first_data = first_response.json()
        self.assertEqual(len(first_data["rows"]), 10)
        next_cursor = first_data["pagination"].get("next_cursor")
        self.assertTrue(next_cursor)

        response = self.client.get(
            "/api/assets",
            {"pageSize": 10, "cursor": next_cursor},
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data["rows"]), 10)

        expected_ids = list(
            Asset.objects.order_by("-created_at").values_list("id", flat=True)
        )
        self.assertEqual(
            [row["id"] for row in data["rows"]],
            expected_ids[10:20],
        )

        pagination = data["pagination"]
        self.assertEqual(pagination["page"], 1)
        self.assertEqual(pagination["page_size"], 10)
        total_assets = Asset.objects.count()
        expected_total_pages = -(-total_assets // pagination["page_size"])
        self.assertEqual(pagination["total_pages"], expected_total_pages)
        self.assertTrue(pagination["has_next"])
        self.assertTrue(pagination["has_previous"])

    def test_filters_and_metadata(self):
        response = self.client.get(
            "/api/assets",
            {"city": "CityA", "status": "done", "pageSize": 100},
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        rows = data["rows"]
        self.assertTrue(rows)
        self.assertTrue(all(row["city"] == "CityA" for row in rows))
        self.assertTrue(all(row.get("status") == "done" for row in rows))

        pagination = data["pagination"]
        self.assertEqual(pagination["total"], len(rows))

        # Filter metadata is now served from a dedicated endpoint to keep the list payload lean
        self.assertNotIn("filters", data)

        filter_response = self.client.get("/api/assets/filter-metadata")
        self.assertEqual(filter_response.status_code, 200)
        filters = filter_response.json()
        self.assertIn("CityA", filters.get("cities", []))
        self.assertIn("CityB", filters.get("cities", []))
        status_counts = filters.get("statusCounts", {})
        self.assertEqual(
            status_counts.get("done"), Asset.objects.filter(status="done").count()
        )
        self.assertEqual(
            status_counts.get("pending"), Asset.objects.filter(status="pending").count()
        )

    def test_commercial_filter(self):
        response = self.client.get(
            "/api/assets",
            {"commercial": "commercial", "pageSize": 100},
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        rows = data["rows"]
        self.assertEqual(len(rows), 1)
        commercial_row = rows[0]
        self.assertTrue(
            commercial_row.get("isCommercial") or commercial_row.get("is_commercial")
        )

        residential_response = self.client.get(
            "/api/assets",
            {"commercial": "residential", "pageSize": 100},
        )
        self.assertEqual(residential_response.status_code, 200)
        residential_rows = residential_response.json()["rows"]
        self.assertTrue(residential_rows)
        self.assertTrue(all(not row.get("isCommercial") for row in residential_rows))

    def test_page_size_capped_to_maximum(self):
        response = self.client.get("/api/assets", {"pageSize": MAX_ASSET_PAGE_SIZE * 5})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        pagination = data["pagination"]

        self.assertEqual(pagination["page"], 1)
        self.assertEqual(pagination["page_size"], MAX_ASSET_PAGE_SIZE)
        total_assets = Asset.objects.count()
        self.assertEqual(pagination["total"], total_assets)
        self.assertFalse(pagination["has_next"])
        self.assertFalse(pagination["has_previous"])
        self.assertEqual(len(data["rows"]), total_assets)


class AssetsMetadataTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_assets_list_excludes_meta_blob_but_keeps_overrides(self):
        asset = Asset.objects.create(
            scope_type="address",
            city="Meta City",
            status="done",
            meta={
                "zoning": {
                    "value": "residential",
                    "source": "gov",
                    "fetched_at": "2024-01-01T00:00:00Z",
                },
                "listing_prices": {"sale": 1234567},
            },
        )

        response = self.client.get("/api/assets", {"pageSize": 1})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        row = data["rows"][0]

        # Meta blob should be stripped to keep response small
        self.assertNotIn("meta", row)
        self.assertNotIn("_meta", row)

        # Meta-derived values should still populate fields
        self.assertEqual(row.get("zoning"), "residential")
        self.assertEqual(row.get("price"), 1234567)

        # Asset detail should still include meta and attribution for full views
        detail_response = self.client.get(f"/api/assets/{asset.id}")
        self.assertEqual(detail_response.status_code, 200)
        detail = detail_response.json().get("asset", {})
        self.assertIn("meta", detail)
        self.assertIn("_meta", detail)
