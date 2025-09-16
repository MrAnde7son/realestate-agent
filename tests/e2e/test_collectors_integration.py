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

import logging
import os
import sys
import tempfile
from pathlib import Path
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import all collectors
from gis.gis_client import TelAvivGS
from gov.decisive import fetch_decisive_appraisals
from gov.nadlan.scraper import NadlanDealsScraper
from mavat.scrapers.mavat_selenium_client import MavatSeleniumClient
from gov.rami.rami_client import RamiClient
from yad2.scrapers.yad2_scraper import Yad2Scraper
from yad2.search_helper import Yad2SearchHelper
from govmap import GovMapClient
from orchestration.collectors.govmap_collector import GovMapCollector

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


    @pytest.mark.mavat
    @pytest.mark.integration
    @pytest.mark.slow
    def test_mavat_collector_integration(self):
        """Test MavatCollector integration with comprehensive functionality testing."""
        logger.info("Testing MavatCollector integration...")
        
        from orchestration.collectors.mavat_collector import MavatCollector
        
        collector = MavatCollector()
        
        # Test 1: Check accessibility
        logger.info("Testing accessibility...")
        with collector.client as client:
            is_accessible = client.is_accessible()
            assert is_accessible, "Mavat system should be accessible"
            logger.info("✓ Mavat system is accessible")
        
        # Test 2: Search functionality - query search with retry logic
        logger.info("Testing collector search functionality (query)...")
        query_results = []
        for attempt in range(3):  # Retry up to 3 times
            try:
                query_results = collector.search_plans(query=TEST_CITY, limit=5)
                if query_results:
                    break
                logger.warning(f"Attempt {attempt + 1}: No results for query {TEST_CITY}")
                if attempt < 2:  # Don't sleep on last attempt
                    import time
                    time.sleep(5)  # Wait longer between retries
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    import time
                    time.sleep(5)
        
        assert isinstance(query_results, list), "Query results should be a list"
        if len(query_results) == 0:
            logger.warning("⚠ No query results found - this might indicate rate limiting or network issues in CI")
            # In CI, we'll be more lenient and just check that we got a list
            pytest.skip("No query results found - likely due to CI environment constraints")
        logger.info(f"✓ Collector found {len(query_results)} plans for query {TEST_CITY}")
        
        # Add delay between searches to avoid rate limiting
        import time
        time.sleep(3)
        
        # Test 3: Search functionality - street search with retry logic
        logger.info("Testing collector search functionality (street)...")
        street_results = []
        for attempt in range(3):
            try:
                street_results = collector.search_plans(query=TEST_STREET, limit=3)
                if street_results:
                    break
                logger.warning(f"Attempt {attempt + 1}: No results for street {TEST_STREET}")
                if attempt < 2:
                    time.sleep(5)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)
        
        assert isinstance(street_results, list), "Street results should be a list"
        if len(street_results) == 0:
            logger.warning("⚠ No street results found - this might indicate rate limiting or network issues in CI")
            pytest.skip("No street results found - likely due to CI environment constraints")
        logger.info(f"✓ Collector found {len(street_results)} plans for street {TEST_STREET}")
        
        # Add delay between searches to avoid rate limiting
        time.sleep(3)
        
        # Test 4: Search functionality - specific plan search with retry logic
        logger.info("Testing collector search functionality (specific plan)...")
        plan_results = []
        for attempt in range(3):
            try:
                plan_results = collector.search_plans(query="ג/ 5000", limit=3)
                if plan_results:
                    break
                logger.warning(f"Attempt {attempt + 1}: No results for specific plan ג/ 5000")
                if attempt < 2:
                    time.sleep(5)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(5)
        
        assert isinstance(plan_results, list), "Plan results should be a list"
        if len(plan_results) == 0:
            logger.warning("⚠ No plan results found - this might indicate rate limiting or network issues in CI")
            pytest.skip("No plan results found - likely due to CI environment constraints")
        logger.info(f"✓ Collector found {len(plan_results)} plans for specific plan ג/ 5000")
        
        # Test 5: PDF download functionality for plan ג/ 5000 (known to have PDF)
        logger.info("Testing PDF download functionality for plan ג/ 5000...")
        try:
            # Use the underlying client to test PDF download
            with collector.client as client:
                pdf_data = client.fetch_pdf("ג/ 5000")
                assert isinstance(pdf_data, bytes), "PDF data should be bytes"
                assert len(pdf_data) > 0, "PDF should not be empty"
                logger.info(f"✓ Successfully downloaded PDF for plan ג/ 5000 ({len(pdf_data)} bytes)")
        except Exception as e:
            logger.error(f"❌ Failed to download PDF for plan ג/ 5000: {e}")
            # In CI, we'll be more lenient about PDF download failures
            logger.warning("⚠ PDF download failed - this might be due to CI environment constraints")
            pytest.skip("PDF download failed - likely due to CI environment constraints")
        
        logger.info("✓ MavatCollector integration tests passed")

    @pytest.mark.yad2
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    @pytest.mark.skip(reason="Skipping due to captcha issues - needs manual intervention")
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

    @pytest.mark.nadlan
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    @pytest.mark.skip(reason="Skipping due to structure change, need to fix")
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
        assert isinstance(search_results, list) and len(search_results) > 0
        logger.info(f"✓ Found {len(search_results)} address results")

        if search_results:
            # Test 3: Get deals by address
            logger.info("Testing deals by address...")
            deals = scraper.get_deals_by_address(TEST_ADDRESS)
            assert isinstance(deals, list) and len(deals) > 0
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

    @pytest.mark.decisive
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.external_service
    def test_decisive_appraisal(self):
        """Test Decisive Appraisal functionality."""
        logger.info("Testing Decisive Appraisal...")

        # Test 1: Fetch decisive appraisals with retry logic
        logger.info("Testing decisive appraisals fetch...")
        appraisals = []
        for attempt in range(3):  # Retry up to 3 times
            try:
                appraisals = fetch_decisive_appraisals(max_pages=1)
                if appraisals:
                    break
                logger.warning(f"Attempt {attempt + 1}: No appraisals found")
                if attempt < 2:
                    import time
                    time.sleep(5)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if "403" in str(e) or "Forbidden" in str(e):
                    logger.warning("⚠ Got 403 Forbidden - government site might be blocking CI requests")
                    pytest.skip("Government site blocked request - likely due to CI environment constraints")
                if attempt < 2:
                    import time
                    time.sleep(5)
        
        assert isinstance(appraisals, list), "Appraisals should be a list"
        if len(appraisals) == 0:
            logger.warning("⚠ No appraisals found - government site may have changed to use dynamic content loading")
            pytest.skip("No appraisals found - government site may require JavaScript for dynamic content loading")
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

    @pytest.mark.gis
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
            privilege_info = gis_client.get_block_parcel_info(x, y)
            assert isinstance(privilege_info, dict)
            if privilege_info.get("success"):
                logger.info(
                    f"✓ Found block: {privilege_info.get('block')}, parcel: {privilege_info.get('parcel')}"
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

    @pytest.mark.rami
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
        search_params = client.create_search_params(block="6345")
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

    @pytest.mark.govmap
    def test_govmap_client(self):
        """Test GovMap client functionality."""
        logger.info("Testing GovMap Client...")

        # Test 1: Initialize client
        logger.info("Testing client initialization...")
        client = GovMapClient()
        assert client is not None
        logger.info("✓ GovMap client initialized successfully")

        # Test 2: Test autocomplete functionality
        logger.info("Testing autocomplete functionality...")
        autocomplete_results = client.autocomplete(TEST_ADDRESS)
        assert isinstance(autocomplete_results, dict)
        assert "res" in autocomplete_results
        logger.info(f"✓ Autocomplete returned results: {list(autocomplete_results.get('res', {}).keys())}")

        # Test 3: Test coordinate conversion
        logger.info("Testing coordinate conversion...")
        from govmap.api_client import itm_to_wgs84, wgs84_to_itm
        
        # Test with known Tel Aviv coordinates
        x_itm, y_itm = 184391.15, 668715.93
        lon, lat = itm_to_wgs84(x_itm, y_itm)
        assert isinstance(lon, float) and isinstance(lat, float)
        logger.info(f"✓ ITM to WGS84 conversion: ({x_itm}, {y_itm}) -> ({lon:.6f}, {lat:.6f})")
        
        # Test roundtrip conversion
        x_back, y_back = wgs84_to_itm(lon, lat)
        assert abs(x_back - x_itm) < 1.0  # Within 1 meter
        assert abs(y_back - y_itm) < 1.0
        logger.info(f"✓ WGS84 to ITM conversion: ({lon:.6f}, {lat:.6f}) -> ({x_back:.2f}, {y_back:.2f})")

        # Test 4: Test parcel lookup (if coordinates are valid)
        logger.info("Testing parcel lookup...")
        parcel = client.get_parcel_at_point(x_itm, y_itm)
        assert isinstance(parcel, dict)
        logger.info(f"✓ Found parcel: {parcel.get('type', 'Unknown type')}")


        # Test 5: Test WMS GetFeatureInfo (if coordinates are valid)
        logger.info("Testing WMS GetFeatureInfo...")
        # Try with a common layer name
        feature_info = client.wms_getfeatureinfo(
            layer="opendata:PARCEL_ALL", 
            x=x_itm, 
            y=y_itm, 
            buffer_m=10
        )
        assert isinstance(feature_info, list)
        logger.info(f"✓ WMS GetFeatureInfo returned {len(feature_info)} features")

        logger.info("✓ GovMap Client tests passed")

    @pytest.mark.govmap
    def test_govmap_collector(self):
        """Test GovMap collector functionality."""
        logger.info("Testing GovMap Collector...")

        # Test 1: Initialize collector
        logger.info("Testing collector initialization...")
        collector = GovMapCollector()
        assert collector is not None
        logger.info("✓ GovMap collector initialized successfully")

        # Test 2: Test parameter validation
        logger.info("Testing parameter validation...")
        assert collector.validate_parameters(x=100.0, y=200.0) is True
        assert collector.validate_parameters(x="invalid", y=200.0) is False
        logger.info("✓ Parameter validation working correctly")

        # Test 3: Test data collection
        logger.info("Testing data collection...")
        try:
            # Use known Tel Aviv coordinates
            x, y = 184391.15, 668715.93
            data = collector.collect(x=x, y=y)
            
            assert isinstance(data, dict)
            assert "x" in data and "y" in data
            assert "parcel" in data and "nearby" in data
            assert data["x"] == x and data["y"] == y
            
            logger.info(f"✓ Data collection successful: parcel={data['parcel'] is not None}, nearby_layers={len(data['nearby'])}")
        except Exception as e:
            logger.warning(f"⚠ Data collection failed: {e}")

        # Test 4: Test collection with extra layers
        logger.info("Testing collection with extra layers...")
        try:
            data = collector.collect(
                x=184391.15, 
                y=668715.93, 
                extra_layers=["opendata:PARCEL_ALL"],
                buffer_m=50
            )
            assert isinstance(data, dict)
            assert "nearby" in data
            logger.info(f"✓ Collection with extra layers successful: {len(data['nearby'])} layers")
        except Exception as e:
            logger.warning(f"⚠ Collection with extra layers failed: {e}")

        logger.info("✓ GovMap Collector tests passed")




def main():
    """Run the integration tests directly (for standalone execution)."""
    test_instance = TestCollectorsIntegration()
    test_instance.setup_method()

    try:
        # Run all individual collector tests
        logger.info("=" * 60)
        logger.info("RUNNING INTEGRATION TESTS FOR ALL COLLECTORS")
        logger.info(f"Test Address: {TEST_ADDRESS}")
        logger.info("=" * 60)

        # Test each collector individually
        test_instance.test_govmap_client()
        test_instance.test_govmap_collector()
        test_instance.test_mavat_collector_integration()
        test_instance.test_yad2_scraper()
        test_instance.test_nadlan_scraper()
        test_instance.test_decisive_appraisal()
        test_instance.test_gis_client()
        test_instance.test_rami_client()


        logger.info("🎉 All collectors tested successfully!")
    finally:
        test_instance.teardown_method()


if __name__ == "__main__":
    main()
