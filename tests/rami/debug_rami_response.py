#!/usr/bin/env python3
"""Debug the RAMI API response to see what we're actually getting."""

import json

import requests


def debug_rami_api():
    endpoint = "https://apps.land.gov.il/TabaSearch/api//SerachPlans/GetPlans"
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }

    # Test with Tel Aviv search - using the exact payload from the user
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

    print(f'Making request to: {endpoint}')
    print(f'Payload: {json.dumps(search_params, indent=2)}')
    print(f'Headers: {json.dumps(headers, indent=2)}')
    print()

    try:
        response = requests.post(
            endpoint,
            json=search_params,
            headers=headers,
            timeout=60
        )
        
        print(f'Status Code: {response.status_code}')
        print(f'Response Headers: {dict(response.headers)}')
        print(f'Content Type: {response.headers.get("content-type", "Not specified")}')
        print()
        
        # Show raw response (first 1000 chars)
        raw_text = response.text
        print(f'Response Text (first 1000 chars):')
        print('=' * 50)
        print(raw_text[:1000])
        print('=' * 50)
        
        if len(raw_text) > 1000:
            print(f'... (response continues, total length: {len(raw_text)} chars)')
        
        # Try to parse as JSON
        try:
            json_data = response.json()
            print('\nSuccessfully parsed as JSON!')
            print(f'Keys: {list(json_data.keys()) if isinstance(json_data, dict) else "Not a dict"}')
        except:
            print('\nFailed to parse as JSON - likely HTML response')
            
    except Exception as e:
        print(f'Request failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_rami_api()
