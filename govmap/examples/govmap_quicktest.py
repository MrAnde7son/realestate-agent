#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick ad-hoc test for the GovMap client (run locally)
"""
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from govmap import GovMapClient

def main():
    cli = GovMapClient()
    
    # Test autocomplete
    print("Testing autocomplete...")
    result = cli.autocomplete("רוזוב 14 תל אביב")
    print(f"Autocomplete result: {result}")
    
    # Test coordinate conversion
    print("\nTesting coordinate conversion...")
    from govmap.api_client import itm_to_wgs84, wgs84_to_itm
    
    # Example Tel Aviv coordinates (ITM)
    x_itm, y_itm = 184391.15, 668715.93
    lon, lat = itm_to_wgs84(x_itm, y_itm)
    print(f"ITM ({x_itm}, {y_itm}) -> WGS84 ({lon:.6f}, {lat:.6f})")
    
    # Convert back
    x_back, y_back = wgs84_to_itm(lon, lat)
    print(f"WGS84 ({lon:.6f}, {lat:.6f}) -> ITM ({x_back:.2f}, {y_back:.2f})")
    
    # Test parcel lookup (if coordinates are valid)
    print(f"\nTesting parcel lookup at ({x_itm}, {y_itm})...")
    try:
        parcel = cli.get_parcel_at_point(x_itm, y_itm)
        if parcel:
            print(f"Found parcel: {parcel}")
        else:
            print("No parcel found at this location")
    except Exception as e:
        print(f"Parcel lookup failed: {e}")

if __name__ == "__main__":
    main()
