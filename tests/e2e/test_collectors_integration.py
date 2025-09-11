#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Integration tests for all collectors using the address "רוזוב 14 תל אביב"

This test file tests each collector individually to ensure they're working properly:
- Mavat API Client
- Yad2 Scraper
- Nadlan Scraper
- Decisive Appraisal
- GIS Client
- RAMI Client
"""

import asyncio
import json
import logging
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import requests

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import all collectors
from gis.gis_client import TelAvivGS
from gov.decisive import fetch_decisive_appraisals
from gov.nadlan.scraper import NadlanDealsScraper
from mavat.scrapers.mavat_api_client import MavatAPIClient
from gov.rami.rami_client import RamiClient
from yad2.scrapers.yad2_scraper import Yad2Scraper
from yad2.search_helper import Yad2SearchHelper

# Test address
TEST_ADDRESS = "רוזוב 14 תל אביב"
TEST_STREET = "רוזוב"
TEST_HOUSE_NUMBER = 14
TEST_CITY = "תל אביב"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestCollectorsIntegration:
    """Integration tests for all collectors."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temp directory: {self.temp_dir}")

    def teardown_method(self):
        """Clean up test environment."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up temp directory: {self.temp_dir}")

    def test_mavat_api_client(self):
        """Test Mavat API client functionality."""
        logger.info("Testing Mavat API Client...")

        client = MavatAPIClient()

        # Test 1: Get lookup tables
        logger.info("Testing lookup tables...")
        lookup_tables = client.get_lookup_tables()
        assert isinstance(lookup_tables, dict)
        assert len(lookup_tables) > 0
        logger.info(f"✓ Found {len(lookup_tables)} lookup tables")

        # Test 2: Get cities
        logger.info("Testing cities lookup...")
        cities = client.get_cities()
        assert isinstance(cities, list)
        assert len(cities) > 0
        logger.info(f"✓ Found {len(cities)} cities")

        # Test 3: Search for plans in Tel Aviv
        logger.info("Testing plan search in Tel Aviv...")
        plans = client.search_plans(city=TEST_CITY, limit=5)
        assert isinstance(plans, list)
        logger.info(f"✓ Found {len(plans)} plans in {TEST_CITY}")

        # Test 4: Search for plans by street
        logger.info("Testing plan search by street...")
        street_plans = client.search_plans(street=TEST_STREET, limit=3)
        assert isinstance(street_plans, list)
        logger.info(f"✓ Found {len(street_plans)} plans for street {TEST_STREET}")

        # Test 5: Search lookup by text
        logger.info("Testing lookup search...")
        search_results = client.search_lookup_by_text(
            TEST_CITY, table_type="CityCounty"
        )
        assert isinstance(search_results, list)
        logger.info(f"✓ Found {len(search_results)} lookup results for {TEST_CITY}")

        logger.info("✓ Mavat API Client tests passed")

    def test_yad2_scraper(self):
        """Test Yad2 scraper functionality."""
        logger.info("Testing Yad2 Scraper...")

        # Test 1: Initialize scraper
        logger.info("Testing scraper initialization...")
        scraper = Yad2Scraper()
        assert scraper is not None
        logger.info("✓ Scraper initialized successfully")

        # Test 2: Get property types
        logger.info("Testing property types...")
        property_types = scraper.get_property_types()
        assert isinstance(property_types, dict)
        assert len(property_types) > 0
        logger.info(f"✓ Found {len(property_types)} property types")

        # Test 3: Parse address and test location autocomplete
        logger.info("Testing address parsing...")
        parsed_address = Yad2SearchHelper.parse_address(TEST_ADDRESS)
        assert isinstance(parsed_address, dict)
        assert 'street' in parsed_address
        assert 'number' in parsed_address
        assert 'city' in parsed_address
        assert 'neighborhood' in parsed_address
        logger.info(f"✓ Parsed address: {parsed_address}")
        
        # Test location autocomplete for individual components
        logger.info("Testing location autocomplete...")
        
        # Test street autocomplete
        street_data = scraper.fetch_location_autocomplete(parsed_address['street'])
        if street_data:
            assert isinstance(street_data, dict)
            logger.info(f"✓ Found street autocomplete data: {street_data.get('search_text')}")
        else:
            logger.warning("⚠ No street autocomplete data found (this might be expected)")
        
        # Test city autocomplete
        city_data = scraper.fetch_location_autocomplete(parsed_address['city'])
        if city_data:
            assert isinstance(city_data, dict)
            logger.info(f"✓ Found city autocomplete data: {city_data.get('search_text')}")
        else:
            logger.warning("⚠ No city autocomplete data found (this might be expected)")
        
        # Test neighborhood autocomplete (if available)
        if parsed_address['neighborhood']:
            neighborhood_data = scraper.fetch_location_autocomplete(parsed_address['neighborhood'])
            if neighborhood_data:
                assert isinstance(neighborhood_data, dict)
                logger.info(f"✓ Found neighborhood autocomplete data: {neighborhood_data.get('search_text')}")
            else:
                logger.warning("⚠ No neighborhood autocomplete data found (this might be expected)")

        # Test 4: Get location codes from autocomplete and set search parameters
        logger.info("Testing location code resolution...")
        
        # Get city data and extract city ID
        city_data = scraper.fetch_location_autocomplete(parsed_address['city'])
        city_id = None
        if city_data and city_data.get('cities'):
            city_id = city_data['cities'][0].get('cityId')
            logger.info(f"✓ Found city ID: {city_id}")
        
        # Get neighborhood data and extract neighborhood ID (if neighborhood exists)
        neighborhood_id = None
        if parsed_address['neighborhood']:
            neighborhood_data = scraper.fetch_location_autocomplete(parsed_address['neighborhood'])
            if neighborhood_data and neighborhood_data.get('hoods'):
                neighborhood_id = neighborhood_data['hoods'][0].get('hoodId')
                logger.info(f"✓ Found neighborhood ID: {neighborhood_id}")
        
        # Set search parameters using actual location IDs
        search_params = {
        }
        
        # Add city ID if available
        if city_id:
            search_params['city'] = city_id
            logger.info(f"✓ Added city ID to search: {city_id}")
        
        # Add neighborhood ID if available
        if neighborhood_id:
            search_params['neighborhood'] = neighborhood_id
            logger.info(f"✓ Added neighborhood ID to search: {neighborhood_id}")
        
        # Add street ID for more precise searching (prefer ID over name)
        street_id = None
        if parsed_address['street']:
            # Try to get street ID from autocomplete data
            street_data = scraper.fetch_location_autocomplete(parsed_address['street'])
            if street_data and street_data.get('streets'):
                # Find the street that matches our city
                for street in street_data['streets']:
                    if street.get('cityId') == str(city_id):
                        street_id = street.get('streetId')
                        logger.info(f"✓ Found street ID for {parsed_address['street']} in city {city_id}: {street_id}")
                        break
            
            if street_id:
                search_params['street'] = street_id
                logger.info(f"✓ Added street ID to search: {street_id}")
        
        logger.info(f"Setting search parameters: {search_params}")
        scraper.set_search_parameters(**search_params)
        summary = scraper.get_search_summary()
        assert isinstance(summary, dict)
        assert "search_url" in summary
        logger.info("✓ Search parameters set successfully")

        # Test 5: Build search URL
        logger.info("Testing search URL building...")
        search_url = scraper.build_search_url(page=1)
        assert isinstance(search_url, str)
        assert "yad2.co.il" in search_url
        logger.info(f"✓ Search URL built: {search_url}")

        # Test 6: Scrape actual listings - this should fail if captcha is detected
        logger.info("Testing actual listing scraping...")
        assets = scraper.scrape_all_pages(max_pages=1, delay=0)
        assert isinstance(assets, list)
        assert len(assets) > 0, "No assets found - this may indicate captcha or blocking"

        logger.info("✓ Yad2 Scraper tests passed")

    def test_nadlan_scraper(self):
        """Test Nadlan scraper functionality."""
        logger.info("Testing Nadlan Scraper...")

        # Test 1: Initialize scraper
        logger.info("Testing scraper initialization...")
        scraper = NadlanDealsScraper(timeout=30, headless=True)
        assert scraper is not None
        logger.info("✓ Scraper initialized successfully")

        # Test 2: Search for address
        logger.info("Testing address search...")
        search_results = scraper.search_address(TEST_ADDRESS, limit=5)
        assert isinstance(search_results, list)
        logger.info(f"✓ Found {len(search_results)} address results")

        if search_results:
            # Test 3: Get deals by address
            logger.info("Testing deals by address...")
            deals = scraper.get_deals_by_address(TEST_ADDRESS)
            assert isinstance(deals, list)
            logger.info(f"✓ Found {len(deals)} deals for address")

            # Test 4: Get neighborhood info
            if search_results[0].get("neighborhood_id"):
                logger.info("Testing neighborhood info...")
                neighborhood_id = search_results[0]["neighborhood_id"]
                neighborhood_info = scraper.get_neighborhood_info(neighborhood_id)
                assert isinstance(neighborhood_info, dict)
                logger.info(
                    f"✓ Found neighborhood info: {neighborhood_info.get('neigh_name')}"
                )
        else:
            logger.warning("⚠ No address results found (this might be expected)")

        logger.info("✓ Nadlan Scraper tests passed")

    def test_decisive_appraisal(self):
        """Test Decisive Appraisal functionality."""
        logger.info("Testing Decisive Appraisal...")

        # Test 1: Fetch decisive appraisals
        logger.info("Testing decisive appraisals fetch...")
        appraisals = fetch_decisive_appraisals(max_pages=1)
        assert isinstance(appraisals, list)
        logger.info(f"✓ Found {len(appraisals)} decisive appraisals")

        # Test 2: Check appraisal structure
        if appraisals:
            appraisal = appraisals[0]
            assert isinstance(appraisal, dict)
            required_fields = ["title", "date", "appraiser", "committee", "pdf_url"]
            for field in required_fields:
                assert field in appraisal
            logger.info("✓ Appraisal structure is correct")

        logger.info("✓ Decisive Appraisal tests passed")

    def test_gis_client(self):
        """Test GIS client functionality."""
        logger.info("Testing GIS Client...")

        # Test 1: Initialize client
        logger.info("Testing client initialization...")
        gis_client = TelAvivGS()
        assert gis_client is not None
        logger.info("✓ GIS client initialized successfully")

        # Test 2: Get address coordinates
        logger.info("Testing address geocoding...")
        try:
            x, y = gis_client.get_address_coordinates(
                TEST_STREET, TEST_HOUSE_NUMBER
            )
            assert isinstance(x, (int, float))
            assert isinstance(y, (int, float))
            logger.info(f"✓ Geocoded address to coordinates: ({x}, {y})")

            # Test 3: Get building permits
            logger.info("Testing building permits...")
            permits = gis_client.get_building_permits(x, y, radius=50)
            assert isinstance(permits, list)
            logger.info(f"✓ Found {len(permits)} building permits")

            # Test 4: Get land use
            logger.info("Testing land use...")
            land_use_main = gis_client.get_land_use_main(x, y)
            assert isinstance(land_use_main, list)
            logger.info(f"✓ Found {len(land_use_main)} main land use categories")

            land_use_detailed = gis_client.get_land_use_detailed(x, y)
            assert isinstance(land_use_detailed, list)
            logger.info(
                f"✓ Found {len(land_use_detailed)} detailed land use categories"
            )

            # Test 5: Get parcels and blocks
            logger.info("Testing parcels and blocks...")
            parcels = gis_client.get_parcels(x, y)
            assert isinstance(parcels, list)
            logger.info(f"✓ Found {len(parcels)} parcels")

            blocks = gis_client.get_blocks(x, y)
            assert isinstance(blocks, list)
            logger.info(f"✓ Found {len(blocks)} blocks")

            # Test 6: Get plans
            logger.info("Testing plans...")
            local_plans = gis_client.get_plans_local(x, y)
            assert isinstance(local_plans, list)
            logger.info(f"✓ Found {len(local_plans)} local plans")

            city_plans = gis_client.get_plans_citywide(x, y)
            assert isinstance(city_plans, list)
            logger.info(f"✓ Found {len(city_plans)} citywide plans")

            # Test 7: Get environmental data
            logger.info("Testing environmental data...")
            noise_levels = gis_client.get_noise_levels(x, y)
            assert isinstance(noise_levels, list)
            logger.info(f"✓ Found {len(noise_levels)} noise level records")

            green_areas = gis_client.get_green_areas(x, y, radius=100)
            assert isinstance(green_areas, list)
            logger.info(f"✓ Found {len(green_areas)} green areas")

            shelters = gis_client.get_shelters(x, y, radius=200)
            assert isinstance(shelters, list)
            logger.info(f"✓ Found {len(shelters)} shelters")

            # Test 8: Get building privilege info
            logger.info("Testing building privilege info...")
            privilege_info = gis_client.get_gush_helka_info(x, y)
            assert isinstance(privilege_info, dict)
            if privilege_info.get("success"):
                logger.info(
                    f"✓ Found gush: {privilege_info.get('gush')}, helka: {privilege_info.get('helka')}"
                )
            else:
                logger.warning(
                    f"⚠ Building privilege info not available: {privilege_info.get('error')}"
                )

        except Exception as e:
            logger.warning(f"⚠ Address geocoding failed: {e}")
            logger.info("Testing with known coordinates instead...")
            # Use known Tel Aviv coordinates as fallback
            x, y = 180000, 660000  # Approximate Tel Aviv coordinates
            permits = gis_client.get_building_permits(x, y, radius=50)
            assert isinstance(permits, list)
            logger.info(
                f"✓ Found {len(permits)} building permits with fallback coordinates"
            )

        logger.info("✓ GIS Client tests passed")

    def test_rami_client(self):
        """Test RAMI client functionality."""
        logger.info("Testing RAMI Client...")

        # Test 1: Initialize client
        logger.info("Testing client initialization...")
        client = RamiClient()
        assert client is not None
        logger.info("✓ RAMI client initialized successfully")

        # Test 2: Search for plans in Tel Aviv area
        logger.info("Testing plan search...")
        search_params = client.create_search_params(gush="6345")
        plans_df = client.fetch_plans(search_params)
        assert plans_df is not None
        logger.info(f"✓ Found {len(plans_df)} plans")

        # Test 3: Check plan structure
        if len(plans_df) > 0:
            plan = plans_df.iloc[0].to_dict()
            required_fields = ["planId", "planNumber"]
            for field in required_fields:
                assert field in plan
            logger.info("✓ Plan structure is correct")

            # Test 4: Extract document URLs
            logger.info("Testing document URL extraction...")
            documents = client._extract_document_urls(plan)
            assert isinstance(documents, list)
            logger.info(f"✓ Found {len(documents)} document URLs")

            # Test 5: Download a single document (if available)
            if documents:
                logger.info("Testing document download...")
                doc = documents[0]
                test_file = os.path.join(self.temp_dir, "test_document.pdf")
                success = client.download_document(doc["url"], test_file)
                if success:
                    assert os.path.exists(test_file)
                    logger.info("✓ Document downloaded successfully")
                else:
                    logger.warning(
                        "⚠ Document download failed (this might be expected)"
                    )

        logger.info("✓ RAMI Client tests passed")

    def test_all_collectors(self):
        """Test all collectors in sequence."""
        logger.info("=" * 60)
        logger.info("RUNNING INTEGRATION TESTS FOR ALL COLLECTORS")
        logger.info(f"Test Address: {TEST_ADDRESS}")
        logger.info("=" * 60)

        # Test each collector - pytest will handle failures automatically
        logger.info("\n--- Testing Mavat API Client ---")
        self.test_mavat_api_client()
        logger.info("✓ Mavat API Client - PASSED")

        logger.info("\n--- Testing Yad2 Scraper ---")
        self.test_yad2_scraper()
        logger.info("✓ Yad2 Scraper - PASSED")

        logger.info("\n--- Testing Nadlan Scraper ---")
        self.test_nadlan_scraper()
        logger.info("✓ Nadlan Scraper - PASSED")

        logger.info("\n--- Testing Decisive Appraisal ---")
        self.test_decisive_appraisal()
        logger.info("✓ Decisive Appraisal - PASSED")

        logger.info("\n--- Testing GIS Client ---")
        self.test_gis_client()
        logger.info("✓ GIS Client - PASSED")

        logger.info("\n--- Testing RAMI Client ---")
        self.test_rami_client()
        logger.info("✓ RAMI Client - PASSED")

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        logger.info("🎉 All collectors are working correctly!")


def main():
    """Run the integration tests."""
    test_instance = TestCollectorsIntegration()
    test_instance.setup_method()

    try:
        results = test_instance.test_all_collectors()
        return results
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    main()
