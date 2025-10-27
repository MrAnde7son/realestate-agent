#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the enhanced asset field population from collected data.
"""

import pytest
import sys
import types

if 'pyproj' not in sys.modules:
    class _DummyTransformer:
        """Minimal stub for pyproj.Transformer used in unit tests."""

        @classmethod
        def from_crs(cls, *args, **kwargs):
            return cls()

        def transform(self, x, y, *args, **kwargs):
            return x, y

    sys.modules['pyproj'] = types.SimpleNamespace(Transformer=_DummyTransformer)

if 'selenium' not in sys.modules:
    selenium_module = types.ModuleType('selenium')
    selenium_module.__path__ = []

    class _DummyChromeOptions:
        def add_argument(self, *args, **kwargs):
            pass

    class _DummyChromeDriver:
        def __init__(self, *args, **kwargs):
            pass

        def set_page_load_timeout(self, *args, **kwargs):
            pass

        def execute_cdp_cmd(self, *args, **kwargs):
            pass

    selenium_module.webdriver = types.SimpleNamespace(
        Chrome=_DummyChromeDriver,
        ChromeOptions=_DummyChromeOptions,
    )
    sys.modules['selenium'] = selenium_module

    webdriver_module = types.ModuleType('selenium.webdriver')
    webdriver_module.__path__ = []
    webdriver_module.Chrome = _DummyChromeDriver
    webdriver_module.ChromeOptions = _DummyChromeOptions
    sys.modules['selenium.webdriver'] = webdriver_module

    common_module = types.ModuleType('selenium.webdriver.common')
    common_module.__path__ = []
    sys.modules['selenium.webdriver.common'] = common_module

    class _DummyBy:
        XPATH = "xpath"
        CSS_SELECTOR = "css"
        ID = "id"

    by_module = types.ModuleType('selenium.webdriver.common.by')
    by_module.By = _DummyBy
    sys.modules['selenium.webdriver.common.by'] = by_module

    class _DummyKeys:
        ENTER = "ENTER"

    keys_module = types.ModuleType('selenium.webdriver.common.keys')
    keys_module.Keys = _DummyKeys
    sys.modules['selenium.webdriver.common.keys'] = keys_module

    chrome_module = types.ModuleType('selenium.webdriver.chrome')
    chrome_module.__path__ = []
    sys.modules['selenium.webdriver.chrome'] = chrome_module

    class _DummyService:
        def __init__(self, *args, **kwargs):
            pass

    service_module = types.ModuleType('selenium.webdriver.chrome.service')
    service_module.Service = _DummyService
    sys.modules['selenium.webdriver.chrome.service'] = service_module

    support_module = types.ModuleType('selenium.webdriver.support')
    support_module.__path__ = []
    sys.modules['selenium.webdriver.support'] = support_module

    class _DummyWebDriverWait:
        def __init__(self, driver, timeout, *args, **kwargs):
            self.driver = driver
            self.timeout = timeout

        def until(self, method, *args, **kwargs):
            return True

    support_ui_module = types.ModuleType('selenium.webdriver.support.ui')
    support_ui_module.WebDriverWait = _DummyWebDriverWait
    sys.modules['selenium.webdriver.support.ui'] = support_ui_module

    class _DummyExpectedConditions:
        @staticmethod
        def presence_of_element_located(locator):
            return lambda driver: True

        @staticmethod
        def element_to_be_clickable(locator):
            return lambda driver: True

    support_module.expected_conditions = _DummyExpectedConditions
    support_ec_module = types.ModuleType('selenium.webdriver.support.expected_conditions')
    support_ec_module.presence_of_element_located = _DummyExpectedConditions.presence_of_element_located
    support_ec_module.element_to_be_clickable = _DummyExpectedConditions.element_to_be_clickable
    sys.modules['selenium.webdriver.support.expected_conditions'] = support_ec_module

if 'webdriver_manager' not in sys.modules:
    webdriver_manager_module = types.ModuleType('webdriver_manager')
    chrome_manager_module = types.ModuleType('webdriver_manager.chrome')

    class _DummyChromeDriverManager:
        def install(self):
            return "/tmp/chromedriver"

    chrome_manager_module.ChromeDriverManager = _DummyChromeDriverManager
    webdriver_manager_module.chrome = chrome_manager_module

    sys.modules['webdriver_manager'] = webdriver_manager_module
    sys.modules['webdriver_manager.chrome'] = chrome_manager_module

from orchestration.pipeline.asset_enrichment import _populate_asset_fields_from_listings


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
        self.neighborhood = None
        self.meta = {}
        self.save_called = False
        self.is_commercial = False
    
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
                'url': 'https://yad2.co.il/item/12345',
                'meta': {
                    'neighborhood': 'רמת החייל',
                    'raw': {
                        'address': {
                            'neighborhood': {'text': 'רמת החייל'}
                        }
                    }
                }
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
        assert asset.neighborhood == 'רמת החייל'
        
        # Verify source tracking
        assert 'primary_listing_source' in asset.meta
        assert asset.meta['primary_listing_source']['source'] == 'yad2'
        assert asset.meta['primary_listing_source']['listing_id'] == '12345'
        assert asset.meta['primary_listing_source']['address'] == 'רחוב הרצל 15, תל אביב'

        # Verify save was called
        assert asset.save_called

    def test_sets_commercial_flag_from_listings(self):
        asset = MockAsset()
        asset.normalized_address = "דרך השלום 10, תל אביב"

        listings = [
            {
                'price': 100000,
                'area': 40,
                'address': 'דרך השלום 10, תל אביב',
                'listing_type': 'commercial',
                'ad_type': 'private',
                'meta': {
                    'category_id': 2,
                },
            }
        ]

        _populate_asset_fields_from_listings(asset, listings)

        assert asset.is_commercial is True

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
        assert asset.neighborhood is None
        
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
        assert asset.neighborhood is None
        
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
        asset.neighborhood = 'קיים'
        
        # Mock listings
        listings = [
            {
                'price': 3000000,  # Different price
                'area': 120,      # Different area
                'address': 'רחוב הרצל 15, תל אביב',  # Exact match
                'rooms': 5,       # Different rooms
                'bedrooms': 4,
                'floor': 2,
                'meta': {
                    'neighborhood': 'רמת החייל',
                }
            }
        ]
        
        # Test population
        _populate_asset_fields_from_listings(asset, listings)
        
        # Verify existing fields were not overwritten
        assert asset.price == 2000000  # Original value preserved
        assert asset.total_area == 90   # Original value preserved
        assert asset.rooms == 3        # Original value preserved
        assert asset.neighborhood == 'קיים'
        
        # Verify new fields were populated
        assert asset.bedrooms == 4
        assert asset.floor == 2
        
        # Verify price_per_sqm was calculated from existing data
        assert asset.price_per_sqm == 22222  # 2000000 / 90

if __name__ == '__main__':
    pytest.main([__file__])
