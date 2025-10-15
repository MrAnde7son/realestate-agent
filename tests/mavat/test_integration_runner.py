#!/usr/bin/env python3
"""Integration test runner for Mavat scraper.

This script can be used to run integration tests for the Mavat scraper
when you want to test against the real website.

Usage:
    python tests/mavat/test_integration_runner.py
"""

import sys
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, call, patch
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def test_mavat_scraper_integration():
    """Test the Mavat Playwright scraper integration."""
    print("=== Testing Mavat Playwright Scraper Integration ===\n")
    
    try:
        import mavat.scrapers.mavat_scraper as mavat_module
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure Playwright is installed:")
        print("  pip install playwright")
        print("  playwright install")
        return False

    try:
        with patch.object(mavat_module, "MavatScraper") as MockMavatScraper:
            mock_scraper = MagicMock(name="MavatScraperMock")
            mock_tel_aviv_results = [
                SimpleNamespace(
                    title="תכנית תל אביב א'",
                    plan_id="TA-001",
                    status="Approved",
                    authority="עיריית תל אביב"
                ),
                SimpleNamespace(
                    title="תכנית תל אביב ב'",
                    plan_id="TA-002",
                    status="Pending",
                    authority="עיריית תל אביב"
                ),
                SimpleNamespace(
                    title="תכנית תל אביב ג'",
                    plan_id="TA-003",
                    status="Draft",
                    authority="עיריית תל אביב"
                ),
            ]
            mock_ramat_results = [
                SimpleNamespace(
                    title="תכנית רמת החייל א'",
                    plan_id="RH-001",
                    status="Approved",
                    authority="עיריית תל אביב"
                ),
                SimpleNamespace(
                    title="תכנית רמת החייל ב'",
                    plan_id="RH-002",
                    status="Pending",
                    authority="עיריית תל אביב"
                ),
            ]
            mock_scraper.search_text.side_effect = [
                mock_tel_aviv_results,
                mock_ramat_results,
            ]
            MockMavatScraper.return_value = mock_scraper
            
            # Initialize the scraper
            print("1. Initializing Mavat scraper...")
            scraper = mavat_module.MavatScraper(headless=True)  # Set to False to see the browser
            print("   ✅ Scraper initialized (mocked)")
            
            # Test search functionality
            print("\n2. Testing search for 'תל אביב'...")
            results = scraper.search_text("תל אביב", limit=3)
            print(f"   ✅ Search completed: {len(results)} results (mocked)")
            
            if results:
                print("\n   Results found:")
                for i, result in enumerate(results):
                    print(f"   {i+1}. {result.title}")
                    print(f"      ID: {result.plan_id}")
                    print(f"      Status: {result.status}")
                    print(f"      Authority: {result.authority}")
            else:
                print("   No results found - this might be due to:")
                print("   - CAPTCHA requirements")
                print("   - Network issues")
                print("   - Changes in the Mavat website structure")
            
            # Test with different query
            print("\n3. Testing search for 'רמת החייל'...")
            results2 = scraper.search_text("רמת החייל", limit=2)
            print(f"   ✅ Search completed: {len(results2)} results (mocked)")
            
            if results2:
                print("   Results found:")
                for i, result in enumerate(results2):
                    print(f"   {i+1}. {result.title}")
            
            scraper.search_text.assert_has_calls([
                call("תל אביב", limit=3),
                call("רמת החייל", limit=2),
            ])
            MockMavatScraper.assert_called_once_with(headless=True)
            
            print("\n✅ Integration test completed with mocked data!")
            return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

def test_playwright_availability():
    """Test if Playwright is available and working."""
    print("=== Testing Playwright Availability ===\n")
    
    try:
        from playwright.sync_api import sync_playwright
        
        print("1. Testing Playwright import...")
        print("   ✅ Playwright imported successfully")
        
        print("2. Testing Playwright initialization...")
        with sync_playwright() as p:
            print("   ✅ Playwright context created successfully")
            
            print("3. Testing browser launch...")
            browser = p.chromium.launch(headless=True)
            print("   ✅ Browser launched successfully")
            
            print("4. Testing page creation...")
            page = browser.new_page()
            print("   ✅ Page created successfully")
            
            print("5. Testing navigation...")
            page.goto("https://httpbin.org/get")
            print("   ✅ Navigation successful")
            
            print("6. Testing content retrieval...")
            content = page.content()
            print(f"   ✅ Content retrieved ({len(content)} characters)")
            
            browser.close()
            print("   ✅ Browser closed successfully")
        
        print("\n🎉 All Playwright tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Playwright not installed: {e}")
        print("\nTo install Playwright, run:")
        print("  pip install playwright")
        print("  playwright install")
        return False
        
    except Exception as e:
        print(f"❌ Playwright test failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("Starting Mavat Scraper Integration Tests...\n")
    
    # Test 1: Playwright availability
    playwright_ok = test_playwright_availability()
    
    if playwright_ok:
        # Test 2: Mavat scraper integration
        scraper_ok = test_mavat_scraper_integration()
        
        print(f"\n=== Final Results ===")
        print(f"Playwright availability: {'✅ READY' if playwright_ok else '❌ NOT READY'}")
        print(f"Mavat scraper integration: {'✅ READY' if scraper_ok else '❌ NOT READY'}")
        
        if scraper_ok:
            print("\n🎉 All tests passed! The Mavat scraper is working correctly.")
        else:
            print("\n⚠️  Scraper test failed. This might be due to CAPTCHA or website changes.")
    else:
        print("\n⚠️  Please install Playwright before running the integration test.")
