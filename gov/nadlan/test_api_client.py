# -*- coding: utf-8 -*-
"""
Test script for the Nadlan API client.

This script tests the basic functionality of the API client without requiring
external dependencies for the test framework.
"""

import asyncio
import sys
from typing import List

try:
    from .api_client import NadlanAPIClient
    from .models import Deal, NeighborhoodInfo
    from .exceptions import NadlanAPIError, NadlanConfigError
except ImportError:
    # If running as standalone script
    from api_client import NadlanAPIClient
    from models import Deal, NeighborhoodInfo
    from exceptions import NadlanAPIError, NadlanConfigError


def test_config_loading():
    """Test configuration loading."""
    print("Testing configuration loading...")
    
    client = NadlanAPIClient()
    
    try:
        config = client.get_config_sync()
        print(f"✓ Configuration loaded successfully")
        print(f"  API Base: {config.api_base}")
        print(f"  S3 Deals Base: {config.s3_deals_base}")
        print(f"  Search Base URL: {config.search_base_url}")
        return True
    except Exception as e:
        print(f"✗ Configuration loading failed: {e}")
        return False
    finally:
        client.close_sync()


def test_neighborhood_info():
    """Test neighborhood information retrieval."""
    print("\nTesting neighborhood information retrieval...")
    
    client = NadlanAPIClient()
    
    try:
        info = client.get_neighborhood_info_sync("65210036")  # רמת החייל
        print(f"✓ Neighborhood info retrieved successfully")
        print(f"  Neighborhood: {info.neigh_name}")
        print(f"  Settlement: {info.setl_name}")
        print(f"  Neighborhood ID: {info.neigh_id}")
        print(f"  Settlement ID: {info.setl_id}")
        return True
    except Exception as e:
        print(f"✗ Neighborhood info retrieval failed: {e}")
        return False
    finally:
        client.close_sync()


def test_deals_retrieval():
    """Test deals retrieval."""
    print("\nTesting deals retrieval...")
    
    client = NadlanAPIClient()
    
    try:
        deals = client.get_deals_by_neighborhood_id_sync("65210036")  # רמת החייל
        print(f"✓ Deals retrieved successfully")
        print(f"  Found {len(deals)} deals")
        
        if deals:
            deal = deals[0]
            print(f"  Sample deal:")
            print(f"    Address: {deal.address}")
            print(f"    Price: ₪{deal.deal_amount:,.0f}" if deal.deal_amount else "    Price: N/A")
            print(f"    Date: {deal.deal_date}")
            print(f"    Rooms: {deal.rooms}")
            print(f"    Area: {deal.area} sqm" if deal.area else "    Area: N/A")
        
        return True
    except Exception as e:
        print(f"✗ Deals retrieval failed: {e}")
        return False
    finally:
        client.close_sync()


def test_address_search():
    """Test address search."""
    print("\nTesting address search...")
    
    client = NadlanAPIClient()
    
    try:
        results = client.search_addresses_sync("רמת החייל", limit=3)
        print(f"✓ Address search successful")
        print(f"  Found {len(results)} results")
        
        for i, result in enumerate(results):
            print(f"  Result {i+1}:")
            print(f"    Address: {result['value']}")
            print(f"    Type: {result['type']}")
            print(f"    Neighborhood ID: {result['neighborhood_id']}")
        
        return True
    except Exception as e:
        print(f"✗ Address search failed: {e}")
        return False
    finally:
        client.close_sync()


async def test_async_functionality():
    """Test asynchronous functionality."""
    print("\nTesting asynchronous functionality...")
    
    async with NadlanAPIClient() as client:
        try:
            # Test async config loading
            config = await client.get_config()
            print(f"✓ Async configuration loaded successfully")
            
            # Test async deals retrieval
            deals = await client.get_deals_by_neighborhood_id("65210036")
            print(f"✓ Async deals retrieval successful")
            print(f"  Found {len(deals)} deals")
            
            # Test async address search
            results = await client.search_addresses("רמת החייל", limit=2)
            print(f"✓ Async address search successful")
            print(f"  Found {len(results)} results")
            
            return True
        except Exception as e:
            print(f"✗ Async functionality failed: {e}")
            return False


def test_error_handling():
    """Test error handling."""
    print("\nTesting error handling...")
    
    client = NadlanAPIClient(timeout=5.0)  # Short timeout for testing
    
    try:
        # Test with invalid neighborhood ID
        deals = client.get_deals_by_neighborhood_id_sync("99999999")
        print(f"✗ Expected error for invalid neighborhood ID, but got {len(deals)} deals")
        return False
    except NadlanAPIError as e:
        print(f"✓ Correctly caught API error for invalid neighborhood: {e}")
    except Exception as e:
        print(f"✗ Unexpected error type for invalid neighborhood: {e}")
        return False
    finally:
        client.close_sync()
    
    return True


def run_sync_tests():
    """Run all synchronous tests."""
    print("Running Nadlan API Client Tests")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_neighborhood_info,
        test_deals_retrieval,
        test_address_search,
        test_error_handling,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\nSynchronous Tests: {passed}/{total} passed")
    return passed == total


async def run_async_tests():
    """Run asynchronous tests."""
    print("\nRunning Asynchronous Tests")
    print("=" * 30)
    
    try:
        if await test_async_functionality():
            print("Asynchronous Tests: 1/1 passed")
            return True
        else:
            print("Asynchronous Tests: 0/1 passed")
            return False
    except Exception as e:
        print(f"Asynchronous Tests failed: {e}")
        return False


async def main():
    """Run all tests."""
    sync_success = run_sync_tests()
    async_success = await run_async_tests()
    
    print(f"\nOverall Results:")
    print(f"  Synchronous: {'✓ PASSED' if sync_success else '✗ FAILED'}")
    print(f"  Asynchronous: {'✓ PASSED' if async_success else '✗ FAILED'}")
    
    if sync_success and async_success:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
