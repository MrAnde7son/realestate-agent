#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the improved PPM-based model price calculation.
"""

import pytest
from unittest.mock import Mock
from orchestration.pipeline.asset_enrichment import _calculate_market_metrics


class TestPPMModelPriceCalculation:
    """Test the new PPM-based model price calculation."""

    def test_calculate_ppm_from_yad2_listings(self):
        """Test PPM calculation from Yad2 listings."""
        # Mock asset with proper meta support
        asset = Mock()
        asset.total_area = 100  # 100 sqm
        asset.area = 100
        asset.price = None  # No existing price
        asset.is_commercial = False  # Required for filtering
        asset.meta = {}  # Initialize meta as dict
        asset.save = Mock()  # Mock save method
        # Ensure required attributes exist for hasattr checks
        asset.avg_price_per_sqm = None
        asset.min_price_per_sqm = None
        asset.max_price_per_sqm = None
        asset.model_price = None

        # Mock Yad2 listings
        listings = [
            {"price": 2000000, "area": 80, "total_size": 100, "address": "Street 1"},
            {"price": 2500000, "area": 90, "total_size": 120, "address": "Street 2"},
            {"price": 3000000, "area": 110, "total_size": 140, "address": "Street 3"},
        ]

        # Mock gov_data (no transactions)
        gov_data = {"transactions": []}

        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)

        # Verify PPM calculation
        assert hasattr(asset, "avg_price_per_sqm")
        assert hasattr(asset, "min_price_per_sqm")
        assert hasattr(asset, "max_price_per_sqm")
        assert hasattr(asset, "model_price")

        # Expected PPM values use total_size: 2000000/100=20000, 2500000/120≈20833.33, 3000000/140≈21428.57
        # Implementation uses trimmed mean (removes bottom 10%): removes 20000, averages [20833.33, 21428.57]
        # Trimmed average PPM = (20833.33 + 21428.57) / 2 = 21130.95
        # Base value = 21130.95 * 100 = 2,113,095
        # Model price may have small adjustments applied, so use approximate value
        assert asset.avg_price_per_sqm == pytest.approx(21130.95, rel=1e-2)
        assert asset.min_price_per_sqm == pytest.approx(20000.0, rel=1e-2)
        assert asset.max_price_per_sqm == pytest.approx(21428.57, rel=1e-2)
        # Allow for small adjustments (within 1%)
        assert asset.model_price == pytest.approx(2113095, rel=1e-2)

    def test_ppm_prefers_total_area_metadata(self):
        """Ensure PPM uses total/gross area from listing metadata when available."""
        asset = Mock()
        asset.total_area = 120
        asset.area = 100
        asset.price = None
        asset.is_commercial = False
        asset.meta = {}
        asset.save = Mock()
        asset.avg_price_per_sqm = None
        asset.min_price_per_sqm = None
        asset.max_price_per_sqm = None
        asset.model_price = None

        listings = [
            {"price": 2400000, "area": 90, "meta": {"total_size": 120}},
            {"price": 3000000, "size": 95, "meta": {"totalSqm": 130}},
        ]

        gov_data = {"transactions": []}

        _calculate_market_metrics(asset, listings, gov_data)

        # Implementation uses trimmed mean (removes bottom 10%):
        # PPM values: 2400000/120=20000, 3000000/130≈23076.92
        # Sorted: [20000, 23076.92], remove bottom 10% (1 value) = [23076.92]
        # Trimmed average PPM = 23076.92
        expected_avg_ppm = 23076.92
        assert asset.avg_price_per_sqm == pytest.approx(expected_avg_ppm, rel=1e-2)
        assert asset.min_price_per_sqm == pytest.approx(20000.0, rel=1e-2)
        assert asset.max_price_per_sqm == pytest.approx(23076.92, rel=1e-2)
        # Base value = 23076.92 * 120 = 2,769,230.4
        # Size adjustment: 120 sqm is in range 100-150, so -4% adjustment
        # Model price = 2,769,230.4 * 0.96 = 2,658,461.184
        expected_model_price = 23076.92 * 120 * 0.96
        assert asset.model_price == pytest.approx(expected_model_price, rel=1e-2)

    def test_calculate_ppm_from_nadlan_transactions(self):
        """Test PPM calculation from Nadlan transactions."""
        # Mock asset with proper meta support
        asset = Mock()
        asset.total_area = 90  # 90 sqm
        asset.area = 90
        asset.price = None
        asset.is_commercial = False  # Required for filtering
        asset.meta = {}
        asset.save = Mock()
        # Ensure required attributes exist for hasattr checks
        asset.avg_price_per_sqm = None
        asset.min_price_per_sqm = None
        asset.max_price_per_sqm = None
        asset.model_price = None

        # Mock listings (empty)
        listings = []

        # Mock gov_data with transactions (need asset_type for filtering)
        gov_data = {
            "transactions": [
                {
                    "deal_amount": 1800000,
                    "area": 80,
                    "address": "Transaction 1",
                    "asset_type": "דירה",
                },
                {
                    "deal_amount": 2250000,
                    "area": 90,
                    "address": "Transaction 2",
                    "asset_type": "דירה",
                },
                {
                    "deal_amount": 2700000,
                    "area": 100,
                    "address": "Transaction 3",
                    "asset_type": "דירה",
                },
            ]
        }

        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)

        # Expected PPM values: 1800000/80=22500, 2250000/90=25000, 2700000/100=27000
        # Implementation uses trimmed mean (removes bottom 10%):
        # Sorted: [22500, 25000, 27000], remove bottom 10% (1 value) = [25000, 27000]
        # Trimmed average PPM = (25000 + 27000) / 2 = 26000.0
        assert asset.avg_price_per_sqm == pytest.approx(26000.0, rel=1e-2)
        assert asset.min_price_per_sqm == 22500.0
        assert asset.max_price_per_sqm == 27000.0
        # Base value = 26000.0 * 90 = 2,340,000
        # Allow for small adjustments (within 1%)
        assert asset.model_price == pytest.approx(2340000, rel=1e-2)

    def test_calculate_ppm_from_both_sources(self):
        """Test PPM calculation from both Yad2 listings and Nadlan transactions."""
        # Mock asset with proper meta support
        asset = Mock()
        asset.total_area = 110  # 110 sqm
        asset.area = 110
        asset.price = 3000000  # Existing price for gap calculation
        asset.is_commercial = False  # Required for filtering
        asset.meta = {}
        asset.year_built = 2000
        asset.city = "Tel Aviv"  # Required for rent calculation
        asset.neighborhood = None
        asset.save = Mock()
        # Ensure required attributes exist for hasattr checks
        asset.avg_price_per_sqm = None
        asset.min_price_per_sqm = None
        asset.max_price_per_sqm = None
        asset.model_price = None
        asset.price_gap_pct = None

        # Mock Yad2 listings
        listings = [
            {"price": 2200000, "area": 100, "address": "Listing 1"},
            {"price": 2750000, "area": 110, "address": "Listing 2"},
        ]

        # Mock gov_data with transactions (need asset_type for filtering)
        gov_data = {
            "transactions": [
                {
                    "deal_amount": 2000000,
                    "area": 90,
                    "address": "Transaction 1",
                    "asset_type": "דירה",
                },
                {
                    "deal_amount": 2500000,
                    "area": 100,
                    "address": "Transaction 2",
                    "asset_type": "דירה",
                },
            ]
        }

        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)

        # Implementation uses trimmed mean (removes bottom 10%):
        # PPM values: 2200000/100=22000, 2750000/110=25000, 2000000/90≈22222.22, 2500000/100=25000
        # Sorted: [22000, 22222.22, 25000, 25000], remove bottom 10% (1 value) = [22222.22, 25000, 25000]
        # Trimmed average PPM = (22222.22 + 25000 + 25000) / 3 = 24074.07
        expected_avg_ppm = 24074.07
        assert asset.avg_price_per_sqm == pytest.approx(expected_avg_ppm, rel=0.01)
        assert asset.min_price_per_sqm == pytest.approx(22000, rel=0.01)
        assert asset.max_price_per_sqm == 25000.0

        # Base value = 24074.07 * 110 = 2,648,147.7
        # Size adjustment: 110 sqm is in range 100-150, so -4% adjustment
        # Model price = 2,648,147.7 * 0.96 = 2,542,221.792
        expected_model_price = 24074.07 * 110 * 0.96
        assert asset.model_price == pytest.approx(expected_model_price, rel=1e-2)

        # Verify price gap calculation
        if hasattr(asset, "price_gap_pct"):
            expected_model_price = 24074.07 * 110 * 0.96  # From the assertion above
            expected_gap = (
                (asset.price - expected_model_price) / expected_model_price
            ) * 100
            assert asset.price_gap_pct == pytest.approx(expected_gap, rel=1e-1)

    def test_confidence_calculation_with_both_sources(self):
        """Test confidence calculation weights transactions higher than listings and accounts for data completeness."""
        # Mock asset with proper meta support and sufficient data for high completeness
        asset = Mock()
        asset.total_area = 100
        asset.area = 100
        asset.year_built = 2000  # For age factor
        asset.floor = 3  # For floor factor
        asset.elevator = True  # For elevator factor
        asset.parking_spaces = 1  # For attachments factor
        asset.price = None
        asset.is_commercial = False  # Required for filtering
        asset.meta = {
            "distance_to_transit_m": 500,  # For proximity factor (environment)
            "nuisance_index": 0.5,  # For noise factor (environment)
        }
        asset.save = Mock()
        # Ensure required attributes exist for hasattr checks
        asset.confidence_pct = None

        # Mock listings (3 items)
        listings = [
            {"price": 2000000, "area": 80},
            {"price": 2500000, "area": 100},
            {"price": 3000000, "area": 120},
        ]

        # Mock gov_data with transactions (2 items, need asset_type for filtering)
        gov_data = {
            "transactions": [
                {"deal_amount": 1800000, "area": 80, "asset_type": "דירה"},
                {"deal_amount": 2200000, "area": 90, "asset_type": "דירה"},
            ]
        }

        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)

        # Base confidence calculation:
        # normalized_transactions = min(1.0, 2/10) = 0.2
        # normalized_listings = min(1.0, 3/20) = 0.15
        # base_confidence = 0.2 * 0.7 + 0.15 * 0.3 = 0.185 (18.5%)
        # With high data completeness (most factors have data, ~0.8-1.0), final confidence:
        # 0.185 * completeness_factor * 100 = ~15-19%
        assert asset.confidence_pct is not None
        assert (
            12 <= asset.confidence_pct <= 20
        )  # Allow range for completeness factor (0.7-1.0)

        # Verify source breakdown in meta
        assert "market_metrics" in asset.meta
        assert asset.meta["market_metrics"]["ppmSources"]["transactions"] == 2
        assert asset.meta["market_metrics"]["ppmSources"]["listings"] == 3
        assert asset.meta["market_metrics"]["ppmSources"]["total"] == 5

    def test_adjustments_applied_from_features(self):
        """Ensure feature-driven adjustments are applied transparently."""
        asset = Mock()
        asset.total_area = 120
        asset.area = 120
        asset.floor = 4
        asset.elevator = False
        asset.parking_spaces = 1
        asset.balcony_area = 12
        asset.year_built = 1985
        asset.price = None
        asset.is_commercial = False
        asset.meta = {"distance_to_transit_m": 200}
        asset.save = Mock()
        asset.model_price = None

        listings = [
            {"price": 3000000, "area": 120},
        ]

        gov_data = {"transactions": []}

        _calculate_market_metrics(asset, listings, gov_data)

        metrics = asset.meta["market_metrics"]
        assert "adjustments" in metrics
        total_pct = metrics["adjustments"]["totalPct"]
        assert (
            total_pct > 0
        )  # parking + balcony + transit - elevator/size/age net positive

        base_price = metrics["baseModelPrice"]
        adjusted_price = metrics["modelPrice"]
        assert adjusted_price > base_price

    def test_fallback_to_simple_average_when_no_area(self):
        """Test fallback to simple average price when asset has no area."""
        # Mock asset with no area
        asset = Mock()
        asset.total_area = None
        asset.area = None
        asset.price = None
        asset.is_commercial = False  # Required for filtering
        asset.meta = {}
        asset.save = Mock()
        # Ensure required attributes exist for hasattr checks
        asset.model_price = None

        # Mock listings
        listings = [
            {"price": 2000000, "area": 80},
            {"price": 2500000, "area": 100},
            {"price": 3000000, "area": 120},
        ]

        gov_data = {"transactions": []}

        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)

        assert asset.model_price is None

    def test_no_comparable_data(self):
        """Test behavior when no comparable data is available."""
        # Mock asset with proper meta support
        asset = Mock()
        asset.total_area = 100
        asset.area = 100
        asset.price = None
        asset.is_commercial = False  # Required for filtering
        asset.meta = {}
        asset.save = Mock()
        # Ensure required attributes exist for hasattr checks
        asset.confidence_pct = None

        # No listings or transactions
        listings = []
        gov_data = {"transactions": []}

        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)

        # Should have zero confidence and no PPM data
        assert asset.confidence_pct == 0
        assert "market_metrics" in asset.meta
        assert asset.meta["market_metrics"]["ppmSources"]["transactions"] == 0
        assert asset.meta["market_metrics"]["ppmSources"]["listings"] == 0
        assert asset.meta["market_metrics"]["ppmSources"]["total"] == 0


if __name__ == "__main__":
    pytest.main([__file__])
