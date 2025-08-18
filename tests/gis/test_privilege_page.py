#!/usr/bin/env python3
"""
Test script for get_building_privilege_page function
"""

import sys
import os
import pytest
from gis.gis_client import TelAvivGS

@pytest.mark.skip("Requires live GIS service")
def test_privilege_page():
    """Test the get_building_privilege_page function"""
    print("Testing get_building_privilege_page function...")
    
    # Initialize the GIS client
    gs = TelAvivGS()
    
    # Coordinates for רחוב הגולן 1, תל אביב
    x, y = 184320.94, 668548.65
    
    print(f"Testing with coordinates: x={x}, y={y}")
    
    # Test individual functions first
    print("\n1. Testing get_blocks...")
    blocks = gs.get_blocks(x, y)
    print(f"   Blocks found: {len(blocks)}")
    if blocks:
        print(f"   First block: {blocks[0]}")
        gush = blocks[0].get("ms_gush")
        print(f"   Gush: {gush}")
    
    print("\n2. Testing get_parcels...")
    parcels = gs.get_parcels(x, y)
    print(f"   Parcels found: {len(parcels)}")
    if parcels:
        print(f"   First parcel: {parcels[0]}")
        helka = parcels[0].get("ms_chelka")
        print(f"   Helka: {helka}")
    
    # Test the main function
    print("\n3. Testing get_building_privilege_page...")
    try:
        result = gs.get_building_privilege_page(x, y, save_dir="test_privilege_pages")
        if result:
            print(f"   SUCCESS! Result: {result}")
            print(f"   File path: {result.get('file_path')}")
            print(f"   Content type: {result.get('content_type')}")
            print(f"   Message: {result.get('message')}")
        else:
            print("   FAILED: Function returned None")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

@pytest.mark.skip("Requires live GIS service")
def test_gush_helka_extraction():
    """Test the gush and helka extraction specifically"""
    print("\n=== Testing Gush and Helka Extraction ===")
    
    gs = TelAvivGS()
    x, y = 184320.94, 668548.65
    
    # Test the debug function
    try:
        result = gs.get_gush_helka_info(x, y)
        print(f"Gush/Helka info: {result}")
        
        if result.get('success'):
            print(f"✅ SUCCESS: Gush {result['gush']}, Helka {result['helka']}")
            print(f"URL: {result['url']}")
        else:
            print(f"❌ FAILED: {result.get('error')}")
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_privilege_page()
    test_gush_helka_extraction()
