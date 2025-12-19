#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulate the Bat Yam GIS identify request.
This script replicates the exact request from the browser to the Bat Yam GIS service.
"""

import requests
import json
from typing import Dict, Any


def simulate_batyam_gis_request() -> Dict[str, Any]:
    """
    Simulate the Bat Yam GIS identify request with all headers and cookies.
    
    Returns:
        Response JSON data
    """
    # The full URL with all parameters
    url = (
        "https://v5.gis-net.co.il/proxy/proxy.ashx?"
        "http://arcgis006/arcgis/rest/services/Bat_yam/batyam_main_data_public/MapServer/identify?"
        "f=json&tolerance=9&returnGeometry=true&returnFieldName=false&returnUnformattedValues=false&imageDisplay=1688%2C873%2C96&geometry=%7B%22x%22%3A175782%2C%22y%22%3A659524%7D&geometryType=esriGeometryPoint&sr=2039&mapExtent=175515.43999999997%2C659159.21%2C176460.72%2C659648.0899999999&layers=all%3A17&guid=a0b0febb-c5d1-5a23-7db6-e58bf62bc202"
    )
    
    # Headers from the request
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
        "connection": "keep-alive",
        "host": "v5.gis-net.co.il",
        "referer": "https://v5.gis-net.co.il/v5/batyam",
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
        "_hertzeliya": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdXJsIjoiaHR0cDovL2FyY2dpczAwNS9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9IZXJ6bGl5YS9IUlpfUHJpbnQxL0dQU2VydmVyL0V4cG9ydCUyMFdlYiUyME1hcCIsImd1cmwiOiJodHRwOi8vYXJjZ2lzMDA1L2FyY2dpcy9yZXN0L3NlcnZpY2VzL1V0aWxpdGllcy9HZW9tZXRyeS9HZW9tZXRyeVNlcnZlciIsImV1cmwiOiJodHRwczovL3Y1Lmdpcy1uZXQuY28uaWwvYXJjZ2lzL3Jlc3Qvc2VydmljZXMvSGVyemxpeWEvaGVyemxpeWFfZWRpdC9GZWF0dXJlU2VydmVyIiwib3ZlcnZpZXciOiJodHRwOi8vYXJjZ2lzMDA1L2FyY2dpcy9yZXN0L3NlcnZpY2VzL0hlcnpsaXlhL2hlcnpsaXlhX2h5YnJpZC9NYXBTZXJ2ZXIiLCJtdXJsIjoiaHR0cDovL2FyY2dpczAwNS9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9IZXJ6bGl5YS9oZXJ6bGl5YV9tYWluX2RhdGUxL01hcFNlcnZlciIsIm1zaWRzIjoiOS0xNTciLCJuYmYiOjE3NjYwOTA0NTQsImV4cCI6MTc2NjA5NzY1NCwiaXNzIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsIiwiYXVkIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsL3Y1In0.-6esXLuTasiovpXjsrI2oZ9gUIVuj8eygDSfcFcsNkU",
        "_ga_8QML5PBNRE": "GS2.1.s1766089555$o3$g1$t1766090456$j55$l0$h0",
        "_ga": "GA1.3.797682413.1766052238",
        "_gat": "1",
        "_batyam": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdXJsIjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9CYXRfeWFtL2JhdHlhbV9QcmludDEvR1BTZXJ2ZXIvRXhwb3J0JTIwV2ViJTIwTWFwIiwiZ3VybCI6Imh0dHA6Ly9hcmNnaXMwMDYvYXJjZ2lzL3Jlc3Qvc2VydmljZXMvVXRpbGl0aWVzL0dlb21ldHJ5L0dlb21ldHJ5U2VydmVyIiwib3ZlcnZpZXciOiJodHRwOi8vYXJjZ2lzMDA2L2FyY2dpcy9yZXN0L3NlcnZpY2VzL0JhdF95YW0vYmF0eWFtX2h5YnJpZC9NYXBTZXJ2ZXIiLCJtdXJsIjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9CYXRfeWFtL2JhdHlhbV9tYWluX2RhdGFfcHVibGljL01hcFNlcnZlciIsIm1zaWRzIjoiMC0yNiwyOC0xMzQiLCJuYmYiOjE3NjYwOTA3MjAsImV4cCI6MTc2NjA5NzkyMCwiaXNzIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsIiwiYXVkIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsL3Y1In0.DNUu6uyvKcfcspIBsY5lFyOAEif-EPHYQgWFuFpNqVM",
        "TS01d52e22": "01fa9750ce2b51ed49bdada02d9a52f8b5a3429a117c8035afe77c3e81cb03c129c196b6fbaf355a14ed4833e74690a98b70b92d707dc5d8d9ee929c48c31e5222dd6c91b6bcb98d0a63f7948a109ccbd4717ef9a6283af9b334873532158058e98bd25001",
        "_ga_DRKJ9KDWZ0": "GS2.1.s1766090557$o1$g1$t1766090721$j56$l0$h0",
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
    result = simulate_batyam_gis_request()
    print("\n" + "="*80)
    print("Request completed!")
    print("="*80)



