#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Core Functionality

Tests for the core Yad2 scraper functionality.
"""

import json
from yad2.core import Yad2SearchParameters, Yad2ParameterReference, URLUtils


def test_parameter_system():
    """Test the parameter system."""
    print("🧪 Testing Parameter System")
    print("=" * 30)
    
    # Test 1: Create parameters
    params = Yad2SearchParameters(
        maxPrice=8000000,
        city=5000,
        property="1,33",
        rooms="3-4",
        elevator=1
    )
    
    print("✅ Parameters created successfully")
    print("Active parameters:", len(params.get_active_parameters()))
    
    # Test 2: Build URL
    url = params.build_url()
    print("✅ URL built successfully:", url[:60] + "..." if len(url) > 60 else url)
    
    # Test 3: JSON export
    json_str = params.to_json()
    print("✅ JSON export successful:", len(json_str), "characters")
    
    return True


def test_reference_system():
    """Test the parameter reference system."""
    print("\n🧪 Testing Reference System")
    print("=" * 30)
    
    ref = Yad2ParameterReference()
    
    # Test 1: Get parameter info
    info = ref.get_parameter_info('maxPrice')
    print("✅ Parameter info retrieved:", info['description'])
    
    # Test 2: Get property types
    prop_types = ref.get_property_types()
    print("✅ Property types retrieved:", len(prop_types), "types")
    
    # Test 3: List all parameters
    all_params = ref.list_all_parameters()
    print("✅ All parameters listed:", len(all_params), "parameters")
    
    return True


def test_url_extraction():
    """Test URL parameter extraction."""
    print("\n🧪 Testing URL Extraction")
    print("=" * 30)
    
    # Test URL from your original request
    test_url = "https://www.yad2.co.il/realestate/forsale?maxPrice=10500000&property=5%2C33%2C39&topArea=2&area=1&city=5000&neighborhood=203"
    
    # Parse URL
    extracted_params = URLUtils.extract_url_parameters(test_url)
    
    print("✅ URL parsed successfully")
    print("Extracted parameters:", list(extracted_params.keys()))
    
    # Create parameters from extracted data
    params = Yad2SearchParameters(**extracted_params)
    
    print("✅ Parameters created from URL")
    print("Final parameter count:", len(params.get_active_parameters()))
    
    return True


def run_all_tests():
    """Run all core tests."""
    print("🏠 Yad2 Core Test Suite")
    print("=" * 50)
    
    tests = [
        test_parameter_system,
        test_reference_system, 
        test_url_extraction
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print("❌ Test failed with error:", e)
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 25)
    
    passed = sum(results)
    total = len(results)
    
    print("Passed: {}/{}".format(passed, total))
    
    if passed == total:
        print("🎉 All core tests passed!")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    run_all_tests() 