#!/usr/bin/env python3
"""Test pagination parameters with the RAMI API."""

import requests


def test_pagination():
    endpoint = "https://apps.land.gov.il/TabaSearch/api//SerachPlans/GetPlans"
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    }

    # Base search params
    base_params = {
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

    # Test 1: Original request without pagination
    print("=== Test 1: No pagination params ===")
    try:
        response = requests.post(endpoint, json=base_params, headers=headers, timeout=60)
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            data = response.json()
            print(f'Total records: {data.get("totalRecords", "N/A")}')
            plans = data.get("plansSmall", [])
            print(f'Returned plans: {len(plans)}')
        else:
            print(f'Error response: {response.text[:500]}')
    except Exception as e:
        print(f'Failed: {e}')

    # Test 2: With page and size parameters
    print("\n=== Test 2: With page=0, size=10 ===")
    params_with_page = dict(base_params)
    params_with_page['page'] = 0
    params_with_page['size'] = 10
    
    try:
        response = requests.post(endpoint, json=params_with_page, headers=headers, timeout=60)
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            try:
                data = response.json()
                print(f'Total records: {data.get("totalRecords", "N/A")}')
                plans = data.get("plansSmall", [])
                print(f'Returned plans: {len(plans)}')
            except:
                print('Failed to parse JSON response')
                print(f'Raw response: {response.text[:500]}')
        else:
            print(f'Error response: {response.text[:500]}')
    except Exception as e:
        print(f'Failed: {e}')

    # Test 3: With different pagination field names
    print("\n=== Test 3: With pageIndex=0, pageSize=10 ===")
    params_alt_page = dict(base_params)
    params_alt_page['pageIndex'] = 0
    params_alt_page['pageSize'] = 10
    
    try:
        response = requests.post(endpoint, json=params_alt_page, headers=headers, timeout=60)
        print(f'Status: {response.status_code}')
        if response.status_code == 200:
            try:
                data = response.json()
                print(f'Total records: {data.get("totalRecords", "N/A")}')
                plans = data.get("plansSmall", [])
                print(f'Returned plans: {len(plans)}')
            except:
                print('Failed to parse JSON response')
                print(f'Raw response: {response.text[:500]}')
        else:
            print(f'Error response: {response.text[:500]}')
    except Exception as e:
        print(f'Failed: {e}')

if __name__ == "__main__":
    test_pagination()
