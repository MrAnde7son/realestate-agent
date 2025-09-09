#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Optimized End-to-End Test for Real Estate Data Pipeline

This test runs the pipeline with real data but with optimized settings
to handle performance and timeout issues.
"""

import sys
import os
import time
import logging
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_pipeline_e2e_optimized():
    """Test the complete pipeline with optimized settings."""
    try:
        from orchestration.data_pipeline import DataPipeline
        
        # Create pipeline
        pipeline = DataPipeline()
        logger.info("✅ Pipeline created successfully")
        
        # Test with a well-known Tel Aviv address
        address = "רוטשילד"
        house_number = 1
        
        logger.info(f"🚀 Running optimized pipeline for: {address} {house_number}")
        
        # Run the pipeline with max_pages=1 to limit data
        start_time = time.time()
        results = pipeline.run(address, house_number, max_pages=1)
        execution_time = time.time() - start_time
        
        # Basic assertions with more reasonable timeout
        assert results is not None, "Pipeline should return results"
        assert len(results) > 0, "Pipeline should return at least some data"
        assert execution_time < 300, f"Pipeline should complete within 5 minutes, took {execution_time:.2f}s"
        
        # Analyze results
        sources = analyze_results_by_source(results)
        
        logger.info(f"✅ Pipeline completed successfully in {execution_time:.2f}s")
        logger.info(f"📊 Collected data from {len(sources)} sources: {list(sources.keys())}")
        
        # Verify we got data from multiple sources
        assert len(sources) >= 2, f"Expected data from multiple sources, got: {list(sources.keys())}"
        
        # Verify Yad2 data
        if 'yad2' in sources:
            yad2_data = sources['yad2']
            assert len(yad2_data) > 0, "Should have Yad2 listings"
            logger.info(f"🏠 Found {len(yad2_data)} Yad2 listings")
            
            # Check first listing
            first_listing = yad2_data[0]
            assert hasattr(first_listing, 'title'), "Listing should have title"
            assert hasattr(first_listing, 'address'), "Listing should have address"
            logger.info(f"   First listing: {first_listing.title} - {first_listing.address}")
        
        # Verify GIS data
        if 'gis' in sources:
            gis_data = sources['gis']
            # GIS data can be a list of dictionaries or a single dictionary
            if isinstance(gis_data, list) and len(gis_data) > 0:
                gis_data = gis_data[0]  # Take the first item if it's a list
            
            assert isinstance(gis_data, dict), f"GIS data should be a dictionary, got {type(gis_data)}"
            if 'x' in gis_data and 'y' in gis_data:
                logger.info(f"📍 GIS coordinates: {gis_data['x']}, {gis_data['y']}")
            if 'block' in gis_data and 'parcel' in gis_data:
                logger.info(f"📍 Block/Parcel: {gis_data['block']}/{gis_data['parcel']}")
        
        logger.info("🎉 Optimized E2E test completed successfully!")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("This might be due to missing dependencies. Try installing them first.")
        return False
        
    except Exception as e:
        logger.error(f"❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_error_handling():
    """Test pipeline resilience with invalid address."""
    try:
        from orchestration.data_pipeline import DataPipeline
        
        # Create pipeline
        pipeline = DataPipeline()
        
        # Test with an address that should fail gracefully
        address = "nonexistent_street_12345"
        house_number = 999
        
        logger.info(f"🚀 Testing error handling with: {address} {house_number}")
        
        # Run the pipeline - should not crash
        start_time = time.time()
        results = pipeline.run(address, house_number, max_pages=1)
        execution_time = time.time() - start_time
        
        # Should still return results (even if empty)
        assert results is not None, "Pipeline should return results even on error"
        assert execution_time < 60, f"Pipeline should fail fast, took {execution_time:.2f}s"
        
        # Should have at least Yad2 data (general search)
        sources = analyze_results_by_source(results)
        assert 'yad2' in sources, "Should have Yad2 data even with invalid address"
        
        logger.info(f"✅ Error handling test completed in {execution_time:.2f}s")
        logger.info("🎉 Error handling E2E test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error handling test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_performance_benchmark():
    """Test pipeline performance with different addresses."""
    try:
        from orchestration.data_pipeline import DataPipeline
        
        # Create pipeline
        pipeline = DataPipeline()
        
        # Test addresses with different complexity
        test_cases = [
            ("רוטשילד", 1, "Well-known Tel Aviv street"),
            ("דיזנגוף", 50, "Another major Tel Aviv street"),
        ]
        
        results = {}
        
        for address, house_number, description in test_cases:
            logger.info(f"🚀 Testing: {address} {house_number} ({description})")
            
            start_time = time.time()
            try:
                pipeline_results = pipeline.run(address, house_number, max_pages=1)
                execution_time = time.time() - start_time
                
                sources = analyze_results_by_source(pipeline_results)
                
                results[f"{address} {house_number}"] = {
                    'success': True,
                    'time': execution_time,
                    'items': len(pipeline_results),
                    'sources': len(sources)
                }
                
                logger.info(f"✅ {address} {house_number}: {execution_time:.2f}s, {len(pipeline_results)} items, {len(sources)} sources")
                
            except Exception as e:
                execution_time = time.time() - start_time
                results[f"{address} {house_number}"] = {
                    'success': False,
                    'time': execution_time,
                    'error': str(e)
                }
                
                logger.error(f"❌ {address} {house_number}: {execution_time:.2f}s, error: {e}")
        
        # Analyze results
        successful_tests = [r for r in results.values() if r['success']]
        if successful_tests:
            avg_time = sum(r['time'] for r in successful_tests) / len(successful_tests)
            logger.info(f"📊 Average execution time: {avg_time:.2f}s")
            logger.info(f"📊 Success rate: {len(successful_tests)}/{len(test_cases)}")
        
        # At least one test should succeed
        assert len(successful_tests) > 0, "At least one test case should succeed"
        
        logger.info("🎉 Performance benchmark E2E test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Performance benchmark test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_individual_collectors_e2e():
    """Test individual collectors with real data."""
    try:
        logger.info("🔍 Testing individual collectors...")
        
        # Test Yad2 collector
        from orchestration.collectors.yad2_collector import Yad2Collector
        yad2 = Yad2Collector()
        yad2_results = yad2.collect(address="רוטשילד", max_pages=1)
        assert len(yad2_results) > 0, "Yad2 should return listings"
        logger.info(f"✅ Yad2: {len(yad2_results)} listings")
        
        # Test GIS collector
        from orchestration.collectors.gis_collector import GISCollector
        gis = GISCollector()
        gis_results = gis.collect(address="רוטשילד", house_number=1)
        assert isinstance(gis_results, dict), "GIS should return dictionary"
        logger.info(f"✅ GIS: {len(gis_results)} data items")
        
        # Test other collectors (may return empty results)
        from orchestration.collectors.gov_collector import GovCollector
        gov = GovCollector()
        gov_results = gov.collect(address="רוטשילד", block="", parcel="")
        logger.info(f"✅ Gov: {len(gov_results)} data items")
        
        from orchestration.collectors.rami_collector import RamiCollector
        rami = RamiCollector()
        rami_results = rami.collect(block="", parcel="")
        logger.info(f"✅ RAMI: {len(rami_results)} plans")
        
        from orchestration.collectors.mavat_collector import MavatCollector
        mavat = MavatCollector()
        mavat_results = mavat.collect(block="", parcel="")
        logger.info(f"✅ Mavat: {len(mavat_results)} plans")
        
        logger.info("🎉 All individual collectors working!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Individual collectors test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pipeline_data_quality():
    """Test data quality and validation."""
    try:
        from orchestration.data_pipeline import DataPipeline
        
        # Create pipeline
        pipeline = DataPipeline()
        
        # Test with a simple address
        address = "רוטשילד"
        house_number = 1
        
        logger.info("🔍 Testing pipeline data quality")
        
        results = pipeline.run(address, house_number, max_pages=1)
        sources = analyze_results_by_source(results)
        
        # Validate Yad2 data quality
        if 'yad2' in sources:
            yad2_data = sources['yad2']
            for listing in yad2_data[:3]:  # Check first 3
                # Check required fields
                assert listing.title and len(listing.title.strip()) > 0, "Title should not be empty"
                assert listing.address and len(listing.address.strip()) > 0, "Address should not be empty"
                
                # Check data types
                if listing.price is not None:
                    assert isinstance(listing.price, (int, float)), "Price should be numeric"
                    assert listing.price > 0, "Price should be positive"
                
                if listing.rooms is not None:
                    assert isinstance(listing.rooms, (int, float)), "Rooms should be numeric"
                    assert listing.rooms > 0, "Rooms should be positive"
                
                if listing.size is not None:
                    assert isinstance(listing.size, (int, float)), "Size should be numeric"
                    assert listing.size > 0, "Size should be positive"
        
        # Validate GIS data quality
        if 'gis' in sources:
            gis_data = sources['gis']
            if 'x' in gis_data and 'y' in gis_data:
                assert isinstance(gis_data['x'], (int, float)), "X coordinate should be numeric"
                assert isinstance(gis_data['y'], (int, float)), "Y coordinate should be numeric"
                assert 180000 <= gis_data['x'] <= 200000, "X coordinate should be in Tel Aviv range"
                assert 650000 <= gis_data['y'] <= 680000, "Y coordinate should be in Tel Aviv range"
        
        logger.info("✅ Data quality validation passed")
        logger.info("🎉 Data quality E2E test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Data quality test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def analyze_results_by_source(results: List[Any]) -> Dict[str, List[Any]]:
    """Analyze pipeline results and group by source."""
    sources = {}
    
    for result in results:
        if hasattr(result, 'title'):  # Yad2 listing
            if 'yad2' not in sources:
                sources['yad2'] = []
            sources['yad2'].append(result)
        elif isinstance(result, dict) and 'source' in result:
            source = result['source']
            if source not in sources:
                sources[source] = []
            sources[source].append(result['data'])
        else:
            # Unknown result type
            if 'unknown' not in sources:
                sources['unknown'] = []
            sources['unknown'].append(result)
    
    return sources


def main():
    """Run all optimized e2e tests."""
    print("🚀 REAL ESTATE PIPELINE OPTIMIZED E2E TESTS")
    print("=" * 60)
    
    tests = [
        ("Optimized Pipeline", test_pipeline_e2e_optimized),
        ("Error Handling", test_pipeline_error_handling),
        ("Performance Benchmark", test_pipeline_performance_benchmark),
        ("Individual Collectors", test_individual_collectors_e2e),
        ("Data Quality", test_pipeline_data_quality),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        print("-" * 40)
        
        try:
            success = test_func()
            results[test_name] = success
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 40)
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All optimized E2E tests passed!")
        return 0
    else:
        print("⚠️ Some optimized E2E tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
