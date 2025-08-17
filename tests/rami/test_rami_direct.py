#!/usr/bin/env python3
"""Test RamiClient by comparing with direct requests."""

import requests
import json
from rami.rami_client import RamiClient

def test_direct_vs_client():
    search_params = {
        'planNumber': '',
        'city': 5000,  # Tel Aviv
        'gush': '',
        'chelka': '',
        'statuses': None,
        'planTypes': [72, 21, 1, 8, 9, 10, 12, 20, 62, 31, 41, 25, 22, 2, 11, 13, 61, 32, 74, 78, 77, 73, 76, 75, 80, 79, 40, 60, 71, 70, 67, 68, 69, 30, 50, 3],
        'fromStatusDate': None,
        'toStatusDate': None,
        'planTypesUsed': False
    }

    endpoint = "https://apps.land.gov.il/TabaSearch/api//SerachPlans/GetPlans"
    
    # Test 1: Direct request (we know this works)
    print("=== Direct Request Test ===")
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }
    
    try:
        response = requests.post(endpoint, json=search_params, headers=headers, timeout=60)
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'Success! Total records: {data.get("totalRecords", "N/A")}')
            plans = data.get("plansSmall", [])
            print(f'Returned plans: {len(plans)}')
        else:
            print(f'Failed: {response.text[:200]}')
    except Exception as e:
        print(f'Error: {e}')

    # Test 2: RamiClient approach - step by step
    print("\n=== RamiClient Step-by-Step Test ===")
    try:
        client = RamiClient()
        print(f'Client endpoint: {client.endpoint}')
        print(f'Client headers: {client.headers}')
        
        # Make the exact same request as RamiClient would
        print("\nMaking request with client session...")
        response = client.session.post(
            client.endpoint,
            json=search_params,
            headers=client.headers,
            cookies=client.cookies,
            timeout=60,
        )
        print(f'Status: {response.status_code}')
        print(f'Response headers: {dict(response.headers)}')
        print(f'Content type: {response.headers.get("content-type", "Unknown")}')
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f'Success! Total records: {data.get("totalRecords", "N/A")}')
                plans = data.get("plansSmall", [])
                print(f'Returned plans: {len(plans)}')
            except Exception as je:
                print(f'JSON parse error: {je}')
                print(f'Raw response length: {len(response.text)}')
                print(f'Raw response start: {response.text[:200]}')
        else:
            print(f'HTTP error: {response.text[:200]}')
            
    except Exception as e:
        print(f'Client error: {e}')
        import traceback
        traceback.print_exc()

    # Test 3: Full RamiClient fetch_plans method
    print("\n=== RamiClient fetch_plans Test ===")
    try:
        client = RamiClient()
        df = client.fetch_plans(search_params)
        print(f'Success! Got {len(df)} results')
        if len(df) > 0:
            print('Columns:', list(df.columns))
    except Exception as e:
        print(f'fetch_plans error: {e}')

if __name__ == "__main__":
    test_direct_vs_client()
