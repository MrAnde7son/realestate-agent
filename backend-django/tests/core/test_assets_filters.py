from django.test import TestCase

from core.models import Asset


class AssetFilterExtensionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.asset_basic = Asset.objects.create(
            scope_type="address",
            city="CityA",
            bedrooms=2,
            bathrooms=1,
            total_floors=3,
            total_area=80,
            balcony_area=8,
            parking_spaces=1,
            year_built=1995,
            rent_estimate=4200,
            price_gap_pct=1.5,
            cap_rate_pct=3.2,
            renovated=True,
            furnished=False,
            air_conditioning=True,
            storage_room=True,
            elevator=True,
            status="done",
        )

        cls.asset_premium = Asset.objects.create(
            scope_type="address",
            city="CityB",
            bedrooms=4,
            bathrooms=3,
            total_floors=10,
            total_area=160,
            balcony_area=25,
            parking_spaces=2,
            year_built=2012,
            rent_estimate=9800,
            price_gap_pct=-2.3,
            cap_rate_pct=4.9,
            renovated=False,
            furnished=True,
            air_conditioning=False,
            storage_room=False,
            elevator=False,
            status="done",
        )

        cls.asset_mid = Asset.objects.create(
            scope_type="address",
            city="CityC",
            bedrooms=3,
            bathrooms=2,
            total_floors=6,
            total_area=110,
            balcony_area=12,
            parking_spaces=0,
            year_built=2005,
            rent_estimate=6500,
            price_gap_pct=6.8,
            cap_rate_pct=2.5,
            renovated=True,
            furnished=True,
            air_conditioning=True,
            storage_room=False,
            elevator=True,
            status="done",
        )

    def _get_asset_ids(self, response):
        data = response.json()
        return [row["id"] for row in data.get("rows", [])]

    def test_bedrooms_range_filter(self):
        response = self.client.get("/api/assets", {"bedroomsMin": 3, "bedroomsMax": 4})
        self.assertEqual(response.status_code, 200)
        ids = self._get_asset_ids(response)
        self.assertIn(self.asset_mid.id, ids)
        self.assertIn(self.asset_premium.id, ids)
        self.assertNotIn(self.asset_basic.id, ids)

    def test_numeric_filters_cover_additional_fields(self):
        response = self.client.get(
            "/api/assets",
            {
                "bathroomsMin": 2,
                "totalFloorsMax": 6,
                "balconyAreaMin": 10,
                "parkingSpacesMax": 1,
                "yearBuiltMin": 2000,
                "rentEstimateMax": 7000,
                "priceGapPctMin": 5,
                "capRatePctMax": 3.5,
            },
        )
        self.assertEqual(response.status_code, 200)
        ids = self._get_asset_ids(response)
        # Only the mid asset satisfies all constraints
        self.assertEqual(ids, [self.asset_mid.id])

    def test_boolean_feature_filters(self):
        response = self.client.get(
            "/api/assets",
            {
                "renovated": "true",
                "furnished": "false",
                "airConditioning": "true",
                "storageRoom": "true",
                "hasElevator": "true",
            },
        )
        self.assertEqual(response.status_code, 200)
        ids = self._get_asset_ids(response)
        self.assertEqual(ids, [self.asset_basic.id])

        # Features filter should pick up new single-feature values as well
        response = self.client.get("/api/assets", {"features": "furnished"})
        self.assertEqual(response.status_code, 200)
        ids = self._get_asset_ids(response)
        self.assertIn(self.asset_mid.id, ids)
        self.assertIn(self.asset_premium.id, ids)
        self.assertNotIn(self.asset_basic.id, ids)

    def test_metadata_includes_extended_fields(self):
        response = self.client.get("/api/assets", {"pageSize": 5})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        filters = data.get("filters", {})

        self.assertIn("bedroomCounts", filters)
        self.assertIn(2, filters["bedroomCounts"])
        self.assertIn(4, filters["bedroomCounts"])

        self.assertIn("bathroomCounts", filters)
        self.assertIn(3, filters["bathroomCounts"])

        self.assertIn("totalFloorCounts", filters)
        self.assertIn(10, filters["totalFloorCounts"])

        self.assertIn("parkingSpaceCounts", filters)
        self.assertIn(2, filters["parkingSpaceCounts"])

        self.assertIn("balconyAreaRange", filters)
        balcony_range = filters["balconyAreaRange"]
        self.assertEqual(balcony_range["min"], 8)
        self.assertEqual(balcony_range["max"], 25)

        self.assertIn("yearBuiltRange", filters)
        self.assertEqual(filters["yearBuiltRange"], {"min": 1995, "max": 2012})

        self.assertIn("rentEstimateRange", filters)
        self.assertEqual(filters["rentEstimateRange"], {"min": 4200, "max": 9800})

        self.assertIn("priceGapPctRange", filters)
        self.assertEqual(filters["priceGapPctRange"], {"min": -2.3, "max": 6.8})

        self.assertIn("capRatePctRange", filters)
        self.assertEqual(filters["capRatePctRange"], {"min": 2.5, "max": 4.9})
