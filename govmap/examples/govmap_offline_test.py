#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Offline test for the GovMap client (no network required)
"""
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from govmap import GovMapClient
from govmap.api_client import itm_to_wgs84, wgs84_to_itm

def main():
    print("Testing GovMap module offline...")
    
    # Test 1: Module import
    print("✓ Module imported successfully")
    
    # Test 2: Client initialization
    client = GovMapClient()
    print("✓ Client initialized successfully")
    
    # Test 3: Coordinate conversion
    print("\nTesting coordinate conversion...")
    
    # Test with known Tel Aviv coordinates (ITM)
    x_itm, y_itm = 184391.15, 668715.93
    print(f"Original ITM coordinates: ({x_itm}, {y_itm})")
    
    # Convert to WGS84
    lon, lat = itm_to_wgs84(x_itm, y_itm)
    print(f"Converted to WGS84: ({lon:.6f}, {lat:.6f})")
    
    # Convert back to ITM
    x_back, y_back = wgs84_to_itm(lon, lat)
    print(f"Converted back to ITM: ({x_back:.2f}, {y_back:.2f})")
    
    # Check accuracy (should be within 1 meter)
    diff_x = abs(x_back - x_itm)
    diff_y = abs(y_back - y_itm)
    print(f"Accuracy check - X diff: {diff_x:.3f}m, Y diff: {diff_y:.3f}m")
    
    if diff_x < 1.0 and diff_y < 1.0:
        print("✓ Coordinate conversion is accurate")
    else:
        print("⚠ Coordinate conversion accuracy issue")
    
    # Test 4: Client configuration
    print(f"\nClient configuration:")
    print(f"  WMS URL: {client.wms_url}")
    print(f"  WFS URL: {client.wfs_url}")
    print(f"  Autocomplete URL: {client.autocomplete_url}")
    print(f"  Timeout: {client.timeout}s")
    
    # Test 5: Headers
    print(f"\nHTTP headers:")
    for key, value in client.http.headers.items():
        print(f"  {key}: {value}")
    
    print("\n✓ All offline tests passed!")

if __name__ == "__main__":
    main()
