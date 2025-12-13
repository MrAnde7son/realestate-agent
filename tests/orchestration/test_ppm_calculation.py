#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the improved PPM-based model price calculation.
"""

import pytest
from statistics import median
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
            {'price': 2000000, 'area': 80, 'total_size': 100, 'address': 'Street 1'},
            {'price': 2500000, 'area': 90, 'total_size': 120, 'address': 'Street 2'},
            {'price': 3000000, 'area': 110, 'total_size': 140, 'address': 'Street 3'},
        ]
        
        # Mock gov_data (no transactions)
        gov_data = {'transactions': []}
        
        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)
        
        # Verify PPM calculation
        assert hasattr(asset, 'avg_price_per_sqm')
        assert hasattr(asset, 'min_price_per_sqm')
        assert hasattr(asset, 'max_price_per_sqm')
        assert hasattr(asset, 'model_price')

        # Expected PPM values use total_size: 2000000/100=20000, 2500000/120≈20833.33, 3000000/140≈21428.57
        # Weighted average PPM ≈ 20753.97
        # Model price ≈ median([20000, 20833.33, 21428.57] * 100) = 2,083,333
        assert asset.avg_price_per_sqm == pytest.approx(20753.97, rel=1e-2)
        assert asset.min_price_per_sqm == pytest.approx(20000.0, rel=1e-2)
        assert asset.max_price_per_sqm == pytest.approx(21428.57, rel=1e-2)
        assert asset.model_price == 2083333

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
            {'price': 2400000, 'area': 90, 'meta': {'total_size': 120}},
            {'price': 3000000, 'size': 95, 'meta': {'totalSqm': 130}},
        ]

        gov_data = {'transactions': []}

        _calculate_market_metrics(asset, listings, gov_data)

        expected_avg_ppm = (2400000 / 120 + 3000000 / 130) / 2
        assert asset.avg_price_per_sqm == pytest.approx(expected_avg_ppm, rel=1e-2)
        assert asset.min_price_per_sqm == pytest.approx(20000.0, rel=1e-2)
        assert asset.max_price_per_sqm == pytest.approx(23076.92, rel=1e-2)
        expected_base_value = median([(2400000 / 120) * 120, (3000000 / 130) * 120])
        assert asset.model_price == int(expected_base_value * 0.96)

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
            'transactions': [
                {'deal_amount': 1800000, 'area': 80, 'address': 'Transaction 1', 'asset_type': 'דירה'},
                {'deal_amount': 2250000, 'area': 90, 'address': 'Transaction 2', 'asset_type': 'דירה'},
                {'deal_amount': 2700000, 'area': 100, 'address': 'Transaction 3', 'asset_type': 'דירה'},
            ]
        }
        
        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)
        
        # Expected PPM values: 1800000/80=22500, 2250000/90=25000, 2700000/100=27000
        # Weighted PPM should be close to the simple average in this neutral case
        assert asset.avg_price_per_sqm == pytest.approx(24833.33, rel=1e-2)
        assert asset.min_price_per_sqm == 22500.0
        assert asset.max_price_per_sqm == 27000.0
        assert asset.model_price == 2250000

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
        asset.city = 'Tel Aviv'  # Required for rent calculation
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
            {'price': 2200000, 'area': 100, 'address': 'Listing 1'},
            {'price': 2750000, 'area': 110, 'address': 'Listing 2'},
        ]
        
        # Mock gov_data with transactions (need asset_type for filtering)
        gov_data = {
            'transactions': [
                {'deal_amount': 2000000, 'area': 90, 'address': 'Transaction 1', 'asset_type': 'דירה'},
                {'deal_amount': 2500000, 'area': 100, 'address': 'Transaction 2', 'asset_type': 'דירה'},
            ]
        }
        
        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)
        
        # Base PPM is derived from a weighted average of all comps
        expected_avg_ppm = 23555.56
        assert asset.avg_price_per_sqm == pytest.approx(expected_avg_ppm, rel=0.01)
        assert asset.min_price_per_sqm == pytest.approx(22000, rel=0.01)
        assert asset.max_price_per_sqm == 25000.0

        # Size adjustment for 110 sqm is -4%, so model price should reflect a 4% reduction
        comparable_prices = []
        for listing in listings:
            comparable_prices.append((listing['price'] / listing['area']) * asset.total_area)
        for transaction in gov_data['transactions']:
            comparable_prices.append((transaction['deal_amount'] / transaction['area']) * asset.total_area)

        expected_base_value = int(median(comparable_prices))
        expected_model_price = int(expected_base_value * 0.96)
        assert asset.model_price == expected_model_price

        # Verify price gap calculation
        if hasattr(asset, 'price_gap_pct'):
            expected_gap = ((asset.price - expected_model_price) / expected_model_price) * 100
            assert asset.price_gap_pct == pytest.approx(expected_gap, rel=1e-1)

    def test_confidence_calculation_with_both_sources(self):
        """Test confidence calculation weights transactions higher than listings."""
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
        
        # Mock listings (3 items)
        listings = [
            {'price': 2000000, 'area': 80},
            {'price': 2500000, 'area': 100},
            {'price': 3000000, 'area': 120},
        ]
        
        # Mock gov_data with transactions (2 items, need asset_type for filtering)
        gov_data = {
            'transactions': [
                {'deal_amount': 1800000, 'area': 80, 'asset_type': 'דירה'},
                {'deal_amount': 2200000, 'area': 90, 'asset_type': 'דירה'},
            ]
        }
        
        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)
        
        # Confidence: 2 transactions * 15% + 3 listings * 10% = 30% + 30% = 60%
        assert asset.confidence_pct == 60
        
        # Verify source breakdown in meta
        assert 'market_metrics' in asset.meta
        assert asset.meta['market_metrics']['ppmSources']['transactions'] == 2
        assert asset.meta['market_metrics']['ppmSources']['listings'] == 3
        assert asset.meta['market_metrics']['ppmSources']['total'] == 5

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
        asset.meta = {'distance_to_transit_m': 200}
        asset.save = Mock()
        asset.model_price = None

        listings = [
            {'price': 3000000, 'area': 120},
        ]

        gov_data = {'transactions': []}

        _calculate_market_metrics(asset, listings, gov_data)

        metrics = asset.meta['market_metrics']
        assert 'adjustments' in metrics
        total_pct = metrics['adjustments']['totalPct']
        assert total_pct > 0  # parking + balcony + transit - elevator/size/age net positive

        base_price = metrics['baseModelPrice']
        adjusted_price = metrics['modelPrice']
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
            {'price': 2000000, 'area': 80},
            {'price': 2500000, 'area': 100},
            {'price': 3000000, 'area': 120},
        ]
        
        gov_data = {'transactions': []}
        
        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)
        
        # Should fallback to simple average price: (2000000 + 2500000 + 3000000) / 3 = 2500000
        assert asset.model_price == 2500000

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
        gov_data = {'transactions': []}
        
        # Calculate metrics
        _calculate_market_metrics(asset, listings, gov_data)
        
        # Should have zero confidence and no PPM data
        assert asset.confidence_pct == 0
        assert 'market_metrics' in asset.meta
        assert asset.meta['market_metrics']['ppmSources']['transactions'] == 0
        assert asset.meta['market_metrics']['ppmSources']['listings'] == 0
        assert asset.meta['market_metrics']['ppmSources']['total'] == 0


if __name__ == '__main__':
    pytest.main([__file__])
