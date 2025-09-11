#!/usr/bin/env python3
"""Simple test to isolate PDF download issue."""

import requests

import tests.utils.test_utils  # This sets up the Python path
from gov.rami.rami_client import RamiClient


def test_direct_vs_client():
    """Compare direct requests vs RamiClient session."""
    
    test_url = "https://apps.land.gov.il/IturTabotData/takanonim/telmer/5050330.pdf"
    
    print("🧪 Testing Direct Request:")
    try:
        response = requests.get(test_url, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {response.headers.get('content-length')}")
        if 'text/html' in response.headers.get('content-type', ''):
            print("❌ Got HTML (error page)")
        else:
            print("✅ Got PDF file")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🧪 Testing RamiClient Session:")
    try:
        client = RamiClient()
        response = client.session.get(test_url, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Content-Length: {response.headers.get('content-length')}")
        if 'text/html' in response.headers.get('content-type', ''):
            print("❌ Got HTML (error page)")
            print(f"HTML preview: {response.text[:200]}...")
        else:
            print("✅ Got PDF file")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🧪 Testing RamiClient with Better Headers:")
    try:
        client = RamiClient()
        headers = {
            "Accept": "application/pdf,*/*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Referer": "https://apps.land.gov.il/TabaSearch/"
        }
        response = client.session.get(test_url, headers=headers, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        if 'text/html' in response.headers.get('content-type', ''):
            print("❌ Still getting HTML")
        else:
            print("✅ Success with better headers!")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_working_download():
    """Test a working download using the approach that works."""
    
    print("\n🏗️  Testing Working Download:")
    
    # Create a simple requests session like the debug script
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    })
    
    test_url = "https://apps.land.gov.il/IturTabotData/takanonim/telmer/5050330.pdf"
    
    try:
        print(f"📥 Downloading: {test_url}")
        response = session.get(test_url, stream=True, timeout=60)
        
        if response.status_code == 200 and 'application/pdf' in response.headers.get('content-type', ''):
            # Save to a test file
            with open('test_download.pdf', 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            import os
            file_size = os.path.getsize('test_download.pdf')
            print(f"✅ Successfully downloaded {file_size} bytes to test_download.pdf")
            
            # Clean up
            os.remove('test_download.pdf')
            print("🧹 Cleaned up test file")
            
        else:
            print(f"❌ Failed: Status {response.status_code}, Type: {response.headers.get('content-type')}")
            
    except Exception as e:
        print(f"❌ Download error: {e}")


if __name__ == "__main__":
    test_direct_vs_client()
    test_working_download()
