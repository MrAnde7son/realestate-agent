#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulate the Herzliya GIS identify request.
This script replicates the exact request from the browser to the Herzliya GIS service.
"""

import requests
import json
from typing import Dict, Any


def simulate_herzliya_gis_request() -> Dict[str, Any]:
    """
    Simulate the Herzliya GIS identify request with all headers and cookies.
    
    Returns:
        Response JSON data
    """
    # The full URL with all parameters
    url = (
        "https://v5.gis-net.co.il/proxy/proxy.ashx?"
        "http://arcgis005/arcgis/rest/services/Herzliya/herzliya_main_date1/MapServer/identify"
        "?f=json"
        "&tolerance=9"
        "&returnGeometry=true"
        "&returnFieldName=false"
        "&returnUnformattedValues=false"
        "&imageDisplay=1688%2C873%2C96"
        "&geometry=%7B%22x%22%3A186557%2C%22y%22%3A673926%7D"
        "&geometryType=esriGeometryPoint"
        "&sr=2039"
        "&mapExtent=185951.32000000004%2C673706.5400000002%2C186896.60000000006%2C674195.42"
        "&layers=all%3A24"
        "&guid=34fbdd4c-f157-907f-66a4-a7f571e84106"
    )
    
    # Headers from the request
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
        "connection": "keep-alive",
        "host": "v5.gis-net.co.il",
        "referer": "https://v5.gis-net.co.il/v5/Hertzeliya?minisite=public",
        "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": '"Android"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36",
    }
    
    # Cookies from the request
    cookies = {
        "ASP.NET_SessionId": "svvfa4jlmzfkkmxj5ll5dlry",
        "_gid": "GA1.3.305540927.1766052238",
        "_ga": "GA1.3.797682413.1766052238",
        "_hertzeliya": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdXJsIjoiaHR0cDovL2FyY2dpczAwNS9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9IZXJ6bGl5YS9IUlpfUHJpbnQxL0dQU2VydmVyL0V4cG9ydCUyMFdlYiUyME1hcCIsImd1cmwiOiJodHRwOi8vYXJjZ2lzMDA1L2FyY2dpcy9yZXN0L3NlcnZpY2VzL1V0aWxpdGllcy9HZW9tZXRyeS9HZW9tZXRyeVNlcnZlciIsImV1cmwiOiJodHRwczovL3Y1Lmdpcy1uZXQuY28uaWwvYXJjZ2lzL3Jlc3Qvc2VydmljZXMvSGVyemxpeWEvaGVyemxpeWFfZWRpdC9GZWF0dXJlU2VydmVyIiwib3ZlcnZpZXciOiJodHRwOi8vYXJjZ2lzMDA1L2FyY2dpcy9yZXN0L3NlcnZpY2VzL0hlcnpsaXlhL2hlcnpsaXlhX2h5YnJpZC9NYXBTZXJ2ZXIiLCJtdXJsIjoiaHR0cDovL2FyY2dpczAwNS9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9IZXJ6bGl5YS9oZXJ6bGl5YV9tYWluX2RhdGUxL01hcFNlcnZlciIsIm1zaWRzIjoiOS0xNTciLCJuYmYiOjE3NjYwODk1NjYsImV4cCI6MTc2NjA5Njc2NiwiaXNzIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsIiwiYXVkIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsL3Y1In0.3b_sz-TmV0av1EL70p6CBx9UoE1JoQVKGBfECN3UsHY",
        "TS01d52e22": "01fa9750ce963bad70090623c111e7ddbebaf6069b709dbf89c3ecc179de71e533b630850cb992a7f5780432440aa9e391077e141bc2881a8f20ded82ee858c84aa753c5c1ab4d4861ca44ed9119bb28ee25ea81a4",
        "_gat": "1",
        "_ga_8QML5PBNRE": "GS2.1.s1766089555$o3$g1$t1766090236$j48$l0$h0",
    }
    
    # Make the request
    print(f"Making request to: {url[:100]}...")
    response = requests.get(url, headers=headers, cookies=cookies, timeout=30)
    
    # Check response
    print(f"Status Code: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content-Length: {response.headers.get('Content-Length')}")
    
    # Parse JSON response
    try:
        data = response.json()
        print(f"\nResponse keys: {list(data.keys())}")
        
        # Pretty print the response
        print("\n" + "="*80)
        print("RESPONSE DATA:")
        print("="*80)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        return data
    except json.JSONDecodeError as e:
        print(f"\nFailed to parse JSON: {e}")
        print(f"Response text (first 500 chars): {response.text[:500]}")
        return {"error": "Failed to parse JSON", "text": response.text[:500]}


if __name__ == "__main__":
    result = simulate_herzliya_gis_request()
    print("\n" + "="*80)
    print("Request completed!")
    print("="*80)

