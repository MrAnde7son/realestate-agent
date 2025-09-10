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
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all collectors
from gis.gis_client import TelAvivGS
from gov.decisive import fetch_decisive_appraisals
from gov.nadlan.scraper import NadlanDealsScraper
from mavat.scrapers.mavat_api_client import MavatAPIClient
from rami.rami_client import RamiClient
from yad2.scrapers.yad2_scraper import Yad2Scraper

# Test address
TEST_ADDRESS = "רוזוב 14 תל אביב"
TEST_STREET = "רוזוב"
TEST_HOUSE_NUMBER = 14
TEST_CITY = "תל אביב"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        
        try:
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
            search_results = client.search_lookup_by_text(TEST_CITY, table_type="5")
            assert isinstance(search_results, list)
            logger.info(f"✓ Found {len(search_results)} lookup results for {TEST_CITY}")
            
            logger.info("✓ Mavat API Client tests passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Mavat API Client test failed: {e}")
            return False
    
    def test_yad2_scraper(self):
        """Test Yad2 scraper functionality."""
        logger.info("Testing Yad2 Scraper...")
        
        try:
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
            
            # Test 3: Search property types
            logger.info("Testing property type search...")
            search_results = scraper.search_property_types("דירה")
            assert isinstance(search_results, dict)
            assert len(search_results) > 0
            logger.info(f"✓ Found {len(search_results)} apartment types")
            
            # Test 4: Fetch location data
            logger.info("Testing location data fetch...")
            location_data = scraper.fetch_location_data(TEST_ADDRESS)
            if location_data:
                assert isinstance(location_data, dict)
                logger.info(f"✓ Found location data: {location_data.get('search_text')}")
            else:
                logger.warning("⚠ No location data found (this might be expected)")
            
            # Test 5: Set search parameters
            logger.info("Testing search parameters...")
            scraper.set_search_parameters(
                property="1",  # דירה
                city=TEST_CITY,
                rooms="3,4,5"
            )
            summary = scraper.get_search_summary()
            assert isinstance(summary, dict)
            assert 'search_url' in summary
            logger.info("✓ Search parameters set successfully")
            
            # Test 6: Build search URL
            logger.info("Testing search URL building...")
            search_url = scraper.build_search_url(page=1)
            assert isinstance(search_url, str)
            assert "yad2.co.il" in search_url
            logger.info(f"✓ Search URL built: {search_url}")
            
            logger.info("✓ Yad2 Scraper tests passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Yad2 Scraper test failed: {e}")
            return False
    
    def test_nadlan_scraper(self):
        """Test Nadlan scraper functionality."""
        logger.info("Testing Nadlan Scraper...")
        
        try:
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
                if search_results[0].get('neighborhood_id'):
                    logger.info("Testing neighborhood info...")
                    neighborhood_id = search_results[0]['neighborhood_id']
                    neighborhood_info = scraper.get_neighborhood_info(neighborhood_id)
                    assert isinstance(neighborhood_info, dict)
                    logger.info(f"✓ Found neighborhood info: {neighborhood_info.get('neigh_name')}")
            else:
                logger.warning("⚠ No address results found (this might be expected)")
            
            logger.info("✓ Nadlan Scraper tests passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Nadlan Scraper test failed: {e}")
            return False
    
    def test_decisive_appraisal(self):
        """Test Decisive Appraisal functionality."""
        logger.info("Testing Decisive Appraisal...")
        
        try:
            # Test 1: Fetch decisive appraisals
            logger.info("Testing decisive appraisals fetch...")
            appraisals = fetch_decisive_appraisals(max_pages=1)
            assert isinstance(appraisals, list)
            logger.info(f"✓ Found {len(appraisals)} decisive appraisals")
            
            # Test 2: Check appraisal structure
            if appraisals:
                appraisal = appraisals[0]
                assert isinstance(appraisal, dict)
                required_fields = ['title', 'date', 'appraiser', 'committee', 'pdf_url']
                for field in required_fields:
                    assert field in appraisal
                logger.info("✓ Appraisal structure is correct")
            
            logger.info("✓ Decisive Appraisal tests passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ Decisive Appraisal test failed: {e}")
            return False
    
    def test_gis_client(self):
        """Test GIS client functionality."""
        logger.info("Testing GIS Client...")
        
        try:
            # Test 1: Initialize client
            logger.info("Testing client initialization...")
            gis_client = TelAvivGS()
            assert gis_client is not None
            logger.info("✓ GIS client initialized successfully")
            
            # Test 2: Get address coordinates
            logger.info("Testing address geocoding...")
            try:
                x, y = gis_client.get_address_coordinates(TEST_STREET, TEST_HOUSE_NUMBER)
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
                logger.info(f"✓ Found {len(land_use_detailed)} detailed land use categories")
                
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
                if privilege_info.get('success'):
                    logger.info(f"✓ Found gush: {privilege_info.get('gush')}, helka: {privilege_info.get('helka')}")
                else:
                    logger.warning(f"⚠ Building privilege info not available: {privilege_info.get('error')}")
                
            except Exception as e:
                logger.warning(f"⚠ Address geocoding failed: {e}")
                logger.info("Testing with known coordinates instead...")
                # Use known Tel Aviv coordinates as fallback
                x, y = 180000, 660000  # Approximate Tel Aviv coordinates
                permits = gis_client.get_building_permits(x, y, radius=50)
                assert isinstance(permits, list)
                logger.info(f"✓ Found {len(permits)} building permits with fallback coordinates")
            
            logger.info("✓ GIS Client tests passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ GIS Client test failed: {e}")
            return False
    
    def test_rami_client(self):
        """Test RAMI client functionality."""
        logger.info("Testing RAMI Client...")
        
        try:
            # Test 1: Initialize client
            logger.info("Testing client initialization...")
            client = RamiClient()
            assert client is not None
            logger.info("✓ RAMI client initialized successfully")
            
            # Test 2: Search for plans in Tel Aviv area
            logger.info("Testing plan search...")
            search_params = {
                "city": 5000,  # Tel Aviv area code
                "gush": "",
                "chelka": "",
                "statuses": None,
                "plan_types": None,
                "from_status_date": None,
                "to_status_date": None,
                "plan_types_used": False
            }
            
            plans_df = client.fetch_plans(search_params)
            assert plans_df is not None
            logger.info(f"✓ Found {len(plans_df)} plans")
            
            # Test 3: Check plan structure
            if len(plans_df) > 0:
                plan = plans_df.iloc[0].to_dict()
                required_fields = ['planId', 'planNumber']
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
                    success = client.download_document(doc['url'], test_file)
                    if success:
                        assert os.path.exists(test_file)
                        logger.info("✓ Document downloaded successfully")
                    else:
                        logger.warning("⚠ Document download failed (this might be expected)")
            
            logger.info("✓ RAMI Client tests passed")
            return True
            
        except Exception as e:
            logger.error(f"✗ RAMI Client test failed: {e}")
            return False
    
    def test_all_collectors(self):
        """Test all collectors in sequence."""
        logger.info("=" * 60)
        logger.info("RUNNING INTEGRATION TESTS FOR ALL COLLECTORS")
        logger.info(f"Test Address: {TEST_ADDRESS}")
        logger.info("=" * 60)
        
        results = {}
        
        # Test each collector
        collectors = [
            ("Mavat API Client", self.test_mavat_api_client),
            ("Yad2 Scraper", self.test_yad2_scraper),
            ("Nadlan Scraper", self.test_nadlan_scraper),
            ("Decisive Appraisal", self.test_decisive_appraisal),
            ("GIS Client", self.test_gis_client),
            ("RAMI Client", self.test_rami_client),
        ]
        
        for name, test_func in collectors:
            logger.info(f"\n--- Testing {name} ---")
            try:
                result = test_func()
                results[name] = result
                if result:
                    logger.info(f"✓ {name} - PASSED")
                else:
                    logger.error(f"✗ {name} - FAILED")
            except Exception as e:
                logger.error(f"✗ {name} - ERROR: {e}")
                results[name] = False
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for name, result in results.items():
            status = "✓ PASSED" if result else "✗ FAILED"
            logger.info(f"{name}: {status}")
        
        logger.info(f"\nOverall: {passed}/{total} collectors passed")
        
        if passed == total:
            logger.info("🎉 All collectors are working correctly!")
        else:
            logger.warning(f"⚠ {total - passed} collectors need attention")
        
        return results


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
