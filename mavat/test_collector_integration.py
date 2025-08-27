#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Simple test script to verify MavatCollector integration."""

import sys
import os

# Add the project root to the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_mavat_collector():
    """Test the MavatCollector integration."""
    try:
        print("🧪 Testing MavatCollector integration...")
        
        # Import the collector
        from mavat.collector.mavat_collector import MavatCollector
        
        print("✅ Successfully imported MavatCollector")
        
        # Create an instance
        collector = MavatCollector()
        print("✅ Successfully created MavatCollector instance")
        
        # Test lookup data retrieval
        print("\n🔍 Testing lookup data retrieval...")
        cities = collector.get_lookup_data("cities")
        print(f"   Found {len(cities)} cities")
        
        districts = collector.get_lookup_data("districts")
        print(f"   Found {len(districts)} districts")
        
        # Test search functionality
        print("\n🔍 Testing search functionality...")
        plans = collector.search_plans("תל אביב", limit=5)
        print(f"   Found {len(plans)} plans for 'תל אביב'")
        
        # Test location search
        print("\n🗺️ Testing location search...")
        location_plans = collector.search_by_location("תל אביב", limit=3)
        print(f"   Found {len(location_plans)} plans by location")
        
        # Test block/parcel search
        print("\n🏗️ Testing block/parcel search...")
        block_plans = collector.collect("666", "1")
        print(f"   Found {len(block_plans)} plans for block 666, parcel 1")
        
        print("\n✅ All tests passed! MavatCollector is working correctly.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Check the error details above")
        return False
    
    return True

def test_data_pipeline_integration():
    """Test the data pipeline integration."""
    try:
        print("\n🧪 Testing data pipeline integration...")
        
        # Import the data pipeline
        from orchestration.data_pipeline import DataPipeline, MavatCollector
        
        print("✅ Successfully imported DataPipeline and MavatCollector")
        
        # Create a data pipeline instance
        pipeline = DataPipeline()
        print("✅ Successfully created DataPipeline instance")
        
        # Verify MavatCollector is included
        assert hasattr(pipeline, 'mavat'), "MavatCollector not found in pipeline"
        assert isinstance(pipeline.mavat, MavatCollector), "Pipeline mavat is not MavatCollector"
        
        print("✅ MavatCollector is properly integrated in DataPipeline")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print("💡 Check the error details above")
        return False

if __name__ == "__main__":
    print("🚀 Starting MavatCollector integration tests...\n")
    
    # Test 1: Basic collector functionality
    test1_passed = test_mavat_collector()
    
    # Test 2: Data pipeline integration
    test2_passed = test_data_pipeline_integration()
    
    # Summary
    print("\n" + "="*50)
    if test1_passed and test2_passed:
        print("🎉 All integration tests passed!")
        print("✅ MavatCollector is working correctly")
        print("✅ Data pipeline integration is successful")
    else:
        print("❌ Some tests failed")
        if not test1_passed:
            print("   - MavatCollector basic functionality failed")
        if not test2_passed:
            print("   - Data pipeline integration failed")
    print("="*50)
