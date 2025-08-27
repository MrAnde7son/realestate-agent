#!/usr/bin/env python3
"""Debug PDF download issues."""

import requests

import tests.test_utils  # This sets up the Python path


def test_direct_pdf_access():
    """Test accessing PDF URLs directly to see what we get."""
    
    # Test URLs from the user's data
    test_urls = [
        "https://apps.land.gov.il/IturTabotData/takanonim/telmer/5050330.pdf",
        "https://apps.land.gov.il/IturTabotData/tabot/telmer/5050330/5050330_מצב מאושר-גיליון 1.pdf",
        "https://apps.land.gov.il/IturTabotData/download/telmer/5050330.zip"
    ]
    
    headers = {
        "Accept": "application/pdf,application/octet-stream,*/*",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Referer": "https://apps.land.gov.il/TabaSearch/",
        "Accept-Language": "he,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    for url in test_urls:
        print(f"\n🔗 Testing URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Content-Type: {response.headers.get('content-type', 'Unknown')}")
            print(f"Content-Length: {response.headers.get('content-length', 'Unknown')}")
            
            # Check if it's HTML (error page) or actual file
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                print("❌ Got HTML response (likely error page)")
                # Show first 500 chars of HTML to understand the error
                html_content = response.text[:500]
                print(f"HTML preview: {html_content}...")
            elif 'application/pdf' in content_type or 'application/octet-stream' in content_type:
                print("✅ Got binary file (PDF/ZIP)")
                print(f"File size: {len(response.content)} bytes")
            else:
                print(f"🤔 Unexpected content type: {content_type}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def test_with_session():
    """Test accessing PDFs with a session that might maintain cookies."""
    
    print("\n" + "="*50)
    print("🍪 Testing with session (maintaining cookies)")
    
    session = requests.Session()
    
    # First, visit the main page to get any necessary cookies
    main_page_url = "https://apps.land.gov.il/TabaSearch/"
    print(f"📄 Visiting main page: {main_page_url}")
    
    try:
        main_response = session.get(main_page_url, timeout=30)
        print(f"Main page status: {main_response.status_code}")
        print(f"Cookies received: {len(session.cookies)} cookies")
        
        # Now try to access a PDF
        test_pdf = "https://apps.land.gov.il/IturTabotData/takanonim/telmer/5050330.pdf"
        
        headers = {
            "Accept": "application/pdf,*/*",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://apps.land.gov.il/TabaSearch/"
        }
        
        pdf_response = session.get(test_pdf, headers=headers, timeout=30)
        print(f"\nPDF access status: {pdf_response.status_code}")
        print(f"Content-Type: {pdf_response.headers.get('content-type', 'Unknown')}")
        
        if 'text/html' in pdf_response.headers.get('content-type', ''):
            print("❌ Still getting HTML response")
            print(f"HTML preview: {pdf_response.text[:300]}...")
        else:
            print("✅ Success! Got binary content")
            
    except Exception as e:
        print(f"❌ Session error: {e}")


def test_url_variations():
    """Test different URL variations to see if there's a correct format."""
    
    print("\n" + "="*50)
    print("🔗 Testing URL variations")
    
    base_urls = [
        "https://apps.land.gov.il/IturTabotData/takanonim/telmer/5050330.pdf",
        "https://land.gov.il/IturTabotData/takanonim/telmer/5050330.pdf",
        "http://apps.land.gov.il/IturTabotData/takanonim/telmer/5050330.pdf",
        # Fix backslash issues
        "https://apps.land.gov.il/IturTabotData/tabot/telmer/5050330/5050330_מצב מאושר-גיליון 1.pdf"
    ]
    
    for url in base_urls:
        print(f"\n🧪 Testing: {url}")
        try:
            response = requests.head(url, timeout=10)  # HEAD request to check if accessible
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("✅ URL is accessible")
            elif response.status_code == 404:
                print("❌ File not found")
            elif response.status_code == 403:
                print("🚫 Access forbidden") 
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🐛 PDF Download Debug Tool")
    print("="*50)
    
    test_direct_pdf_access()
    test_with_session() 
    test_url_variations()
    
    print("\n" + "="*50)
    print("💡 Recommendations:")
    print("1. Check if files exist on the server")
    print("2. Verify correct URL format (forward vs backslashes)")
    print("3. Check if authentication/session is required")
    print("4. Consider using browser automation (Selenium) if needed")
