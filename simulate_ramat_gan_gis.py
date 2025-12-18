#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulate the Ramat Gan GIS identify request.
This script replicates the exact request from the browser to the Ramat Gan GIS service.
"""

import requests
import json
from typing import Dict, Any


def simulate_ramat_gan_gis_request() -> Dict[str, Any]:
    """
    Simulate the Ramat Gan GIS identify request with all headers and cookies.
    
    Returns:
        Response JSON data
    """
    # The full URL with all parameters
    url = (
        "https://v5.gis-net.co.il/proxy/proxy.ashx?"
        "http://arcgis006/arcgis/rest/services/RamatGan/RamatGan_maindata/MapServer/identify?"
        "f=json&tolerance=9&returnGeometry=true&returnFieldName=false&returnUnformattedValues=false&imageDisplay=1688%2C873%2C96&geometry=%7B%22x%22%3A183748%2C%22y%22%3A663828%7D&geometryType=esriGeometryPoint&sr=2039&mapExtent=183607.08%2C663727.34%2C184079.72%2C663971.7799999999&layers=all%3A212&guid=41d66a4d-18df-77c3-cfc7-1c63a685a787"
    )
    
    # Headers from the request
    headers = {
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-US,en;q=0.9,he-IL;q=0.8,he;q=0.7",
        "connection": "keep-alive",
        "host": "v5.gis-net.co.il",
        "referer": "https://v5.gis-net.co.il/v5/ramat_gan",
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
        "_batyam": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdXJsIjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9CYXRfeWFtL2JhdHlhbV9QcmludDEvR1BTZXJ2ZXIvRXhwb3J0JTIwV2ViJTIwTWFwIiwiZ3VybCI6Imh0dHA6Ly9hcmNnaXMwMDYvYXJjZ2lzL3Jlc3Qvc2VydmljZXMvVXRpbGl0aWVzL0dlb21ldHJ5L0dlb21ldHJ5U2VydmVyIiwib3ZlcnZpZXciOiJodHRwOi8vYXJjZ2lzMDA2L2FyY2dpcy9yZXN0L3NlcnZpY2VzL0JhdF95YW0vYmF0eWFtX2h5YnJpZC9NYXBTZXJ2ZXIiLCJtdXJsIjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9CYXRfeWFtL2JhdHlhbV9tYWluX2RhdGFfcHVibGljL01hcFNlcnZlciIsIm1zaWRzIjoiMC0yNiwyOC0xMzQiLCJuYmYiOjE3NjYwOTA3MjAsImV4cCI6MTc2NjA5NzkyMCwiaXNzIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsIiwiYXVkIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsL3Y1In0.DNUu6uyvKcfcspIBsY5lFyOAEif-EPHYQgWFuFpNqVM",
        "_ga_DRKJ9KDWZ0": "GS2.1.s1766090557$o1$g1$t1766090721$j56$l0$h0",
        "_ga": "GA1.1.797682413.1766052238",
        "_ramat_gan": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwdXJsIjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9SYW1hdEdhbi9SYW1hdEdhblByaW50L0dQU2VydmVyL0V4cG9ydCUyMFdlYiUyME1hcCIsImd1cmwiOiJodHRwOi8vYXJjZ2lzMDA2L2FyY2dpcy9yZXN0L3NlcnZpY2VzL1V0aWxpdGllcy9HZW9tZXRyeS9HZW9tZXRyeVNlcnZlciIsIm92ZXJ2aWV3IjoiaHR0cDovL2FyY2dpczAwNi9hcmNnaXMvcmVzdC9zZXJ2aWNlcy9SYW1hdEdhbi9SYW1hdEdhbl9IeWJyaWQvTWFwU2VydmVyIiwibXVybCI6Imh0dHA6Ly9hcmNnaXMwMDYvYXJjZ2lzL3Jlc3Qvc2VydmljZXMvUmFtYXRHYW4vUmFtYXRHYW5fbWFpbmRhdGEvTWFwU2VydmVyIiwibXNpZHMiOiIwLTEwNSwxMDctMjUzLDI2OC0yNzUiLCJuYmYiOjE3NjYwOTEwODMsImV4cCI6MTc2NjA5ODI4MywiaXNzIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsIiwiYXVkIjoiaHR0cHM6Ly92NS5naXMtbmV0LmNvLmlsL3Y1In0.C9s9ji07oBJgniJSrCN8sPFlPH5kH-TcHU_ur9YewQ0",
        "TS01d52e22": "01fa9750ce999128e519d35c386b254f9f79c66dcb6dda6121e247c8d471b09b35405bf7a55715a3d4f492f00b8a92a175ccf126eb7402d8f43864825c345ef68a32e396d147b22288e5f021e6457c29407d29b30b5661caba681df49cc8f5744ebd9cc60b7578e18c0bebca88ef622a4276f82f05",
        "_gat": "1",
        "_ga_3HDGMVD29Z": "GS2.1.s1766091145$o1$g1$t1766091213$j52$l0$h0",
    }
    
    # Make the request
    print(f"Making request to: {url[:100]}...")
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=60)
    except requests.exceptions.Timeout:
        print("Request timed out. The server may be slow or unavailable.")
        return {"error": "Request timed out"}
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return {"error": str(e)}
    
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
    result = simulate_ramat_gan_gis_request()
    print("\n" + "="*80)
    print("Request completed!")
    print("="*80)

