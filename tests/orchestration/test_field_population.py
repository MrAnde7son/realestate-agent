#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the enhanced asset field population from collected data.
"""

import pytest
from unittest.mock import Mock
from orchestration.data_pipeline import _populate_asset_fields_from_listings, _populate_asset_fields_from_tabu


class MockAsset:
    """Simple mock asset class for testing."""
    def __init__(self):
        self.id = 1
        self.price = None
        self.total_area = None
        self.area = None
        self.price_per_sqm = None
        self.rooms = None
        self.bedrooms = None
        self.floor = None
        self.building_type = None
        self.normalized_address = None
        self.street = None
        self.meta = {}
        self.save_called = False
    
    def save(self, update_fields=None):
        self.save_called = True


class TestAssetFieldPopulation:
    """Test asset field population from Yad2 listings and Tabu documents."""

    def test_populate_from_yad2_listings_exact_match(self):
        """Test populating asset fields from Yad2 listing with exact address match."""
        # Create mock asset
        asset = MockAsset()
        asset.normalized_address = "רחוב הרצל 15, תל אביב"
        asset.street = "הרצל"
        
        # Mock listings with exact address match
        listings = [
            {
                'price': 2500000,
                'area': 100,
                'address': 'רחוב הרצל 15, תל אביב',
                'rooms': 4,
                'bedrooms': 3,
                'floor': 2,
                'listing_id': '12345',
                'url': 'https://yad2.co.il/item/12345'
            },
            {
                'price': 3000000,
                'area': 120,
                'address': 'רחוב הרצל 20, תל אביב',
                'rooms': 5,
                'bedrooms': 4,
                'floor': 3
            }
        ]
        
        # Test population
        _populate_asset_fields_from_listings(asset, listings)
        
        # Verify exact match was used (first listing)
        assert asset.price == 2500000
        assert asset.area == 100  # Changed from total_area to area
        assert asset.price_per_sqm == 25000  # 2500000 / 100
        assert asset.rooms == 4
        assert asset.bedrooms == 3
        assert asset.floor == 2
        
        # Verify source tracking
        assert 'primary_listing_source' in asset.meta
        assert asset.meta['primary_listing_source']['source'] == 'yad2'
        assert asset.meta['primary_listing_source']['listing_id'] == '12345'
        assert asset.meta['primary_listing_source']['address'] == 'רחוב הרצל 15, תל אביב'
        
        # Verify save was called
        assert asset.save_called

    def test_populate_from_yad2_listings_street_match(self):
        """Test that street matching is not supported - only exact matches work."""
        # Create mock asset
        asset = MockAsset()
        asset.normalized_address = None  # No exact address
        asset.street = "הרצל"
        
        # Mock listings with street match but no exact match
        listings = [
            {
                'price': 2800000,
                'area': 110,
                'address': 'רחוב הרצל 25, תל אביב',  # Different address
                'rooms': 4,
                'bedrooms': 3
            },
            {
                'price': 3000000,
                'area': 120,
                'address': 'רחוב דיזנגוף 10, תל אביב',
                'rooms': 5,
                'bedrooms': 4
            }
        ]
        
        # Test population
        _populate_asset_fields_from_listings(asset, listings)
        
        # Verify no fields were populated since there's no exact match
        assert asset.price is None
        assert asset.total_area is None
        assert asset.price_per_sqm is None
        assert asset.rooms is None
        assert asset.bedrooms is None
        
        # Verify save was not called
        assert not asset.save_called

    def test_populate_from_yad2_listings_fallback(self):
        """Test that fallback behavior is not supported - only exact matches work."""
        # Create mock asset
        asset = MockAsset()
        asset.normalized_address = None
        asset.street = None  # No address info
        
        # Mock listings
        listings = [
            {
                'price': 2000000,
                'area': 80,
                'address': 'רחוב אחר 10, תל אביב',
                'rooms': 3,
                'bedrooms': 2
            },
            {
                'price': 3000000,
                'area': 120,
                'address': 'רחוב אחר 20, תל אביב',
                'rooms': 5,
                'bedrooms': 4
            }
        ]
        
        # Test population
        _populate_asset_fields_from_listings(asset, listings)
        
        # Verify no fields were populated since there's no exact match
        assert asset.price is None
        assert asset.total_area is None
        assert asset.price_per_sqm is None
        assert asset.rooms is None
        assert asset.bedrooms is None
        
        # Verify save was not called
        assert not asset.save_called

    def test_populate_from_yad2_listings_no_overwrite_existing(self):
        """Test that existing asset fields are not overwritten."""
        # Create mock asset with existing data
        asset = MockAsset()
        asset.price = 2000000  # Already has price
        asset.total_area = 90   # Already has area
        asset.rooms = 3        # Already has rooms
        asset.normalized_address = "רחוב הרצל 15, תל אביב"  # Add exact address for matching
        
        # Mock listings
        listings = [
            {
                'price': 3000000,  # Different price
                'area': 120,      # Different area
                'address': 'רחוב הרצל 15, תל אביב',  # Exact match
                'rooms': 5,       # Different rooms
                'bedrooms': 4,
                'floor': 2
            }
        ]
        
        # Test population
        _populate_asset_fields_from_listings(asset, listings)
        
        # Verify existing fields were not overwritten
        assert asset.price == 2000000  # Original value preserved
        assert asset.total_area == 90   # Original value preserved
        assert asset.rooms == 3        # Original value preserved
        
        # Verify new fields were populated
        assert asset.bedrooms == 4
        assert asset.floor == 2
        
        # Verify price_per_sqm was calculated from existing data
        assert asset.price_per_sqm == 22222  # 2000000 / 90

    def test_populate_from_tabu_documents(self):
        """Test populating asset fields from Tabu document data."""
        # Create mock asset
        asset = MockAsset()
        
        # Mock Tabu data
        tabu_data = [
            {'field': 'שטח', 'value': '85.5 מ״ר'},
            {'field': 'סוג בניין', 'value': 'דירה'},
            {'field': 'גוש', 'value': '1234'},
            {'field': 'חלקה', 'value': '5678'},
            {'field': 'בעלים', 'value': 'יוסי כהן'},
        ]
        
        # Test population
        _populate_asset_fields_from_tabu(asset, tabu_data)
        
        # Verify area was extracted
        assert asset.total_area == 85.5
        assert asset.building_type == 'דירה'
        
        # Verify source tracking
        assert 'tabu_source' in asset.meta
        assert asset.meta['tabu_source']['source'] == 'tabu'
        assert asset.meta['tabu_source']['rows_count'] == 5
        
        # Verify save was called
        assert asset.save_called

    def test_populate_from_tabu_documents_no_overwrite_existing(self):
        """Test that existing asset fields are not overwritten by Tabu data."""
        # Create mock asset with existing data
        asset = MockAsset()
        asset.total_area = 100  # Already has area
        asset.building_type = 'בית פרטי'  # Already has building type
        
        # Mock Tabu data
        tabu_data = [
            {'field': 'שטח', 'value': '120 מ״ר'},  # Different area
            {'field': 'סוג בניין', 'value': 'דירה'},  # Different type
        ]
        
        # Test population
        _populate_asset_fields_from_tabu(asset, tabu_data)
        
        # Verify existing fields were not overwritten
        assert asset.total_area == 100  # Original value preserved
        assert asset.building_type == 'בית פרטי'  # Original value preserved
        
        # Verify save was not called since no fields were updated
        assert not asset.save_called

    def test_populate_from_empty_data(self):
        """Test behavior with empty data sources."""
        # Create mock asset
        asset = MockAsset()
        
        # Test with empty listings
        _populate_asset_fields_from_listings(asset, [])
        
        # Verify no fields were updated
        assert asset.price is None
        assert asset.total_area is None
        assert not asset.save_called
        
        # Reset save flag
        asset.save_called = False
        
        # Test with empty Tabu data
        _populate_asset_fields_from_tabu(asset, [])
        
        # Verify no fields were updated
        assert asset.price is None
        assert asset.total_area is None
        assert not asset.save_called


if __name__ == '__main__':
    pytest.main([__file__])
