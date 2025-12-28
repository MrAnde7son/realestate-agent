#!/usr/bin/env python3
"""
Example usage of the Real Estate API Python client.
"""

import sys
import os

# Add the parent directory to the path so we can import the client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from realestate_api import RealEstateAPIClient
from realestate_api.exceptions import APIException, AuthenticationError


def main():
    """Example usage of the Real Estate API client."""
    print("🏠 Real Estate API Python Client Example")
    print("=" * 50)

    # Initialize the client
    client = RealEstateAPIClient(base_url="http://localhost:8000/api")
    print(f"✅ Client initialized with base URL: {client.base_url}")

    try:
        # Test basic connectivity
        print("\n📡 Testing API connectivity...")
        # Test with a simple endpoint that returns JSON
        try:
            # Try to get assets (might require auth but will return proper JSON)
            assets = client.get_assets()
            print("✅ API is accessible and returns JSON")
        except APIException as e:
            if "401" in str(e) or "Authentication" in str(e):
                print("✅ API is accessible (authentication required)")
            else:
                print(f"⚠️  API error: {e}")

        # Test authentication (this will fail without valid credentials)
        print("\n🔐 Testing authentication...")
        try:
            # This will likely fail since we don't have valid credentials
            login_response = client.login("test@example.com", "testpassword")
            print(f"✅ Login successful: {login_response}")
        except AuthenticationError as e:
            print(f"⚠️  Authentication failed (expected): {e}")
        except APIException as e:
            print(f"⚠️  API error (expected): {e}")

        # Test public endpoints
        print("\n📊 Testing public endpoints...")
        try:
            assets = client.get_assets()
            asset_count = (
                len(assets.get("data", []))
                if isinstance(assets, dict)
                else len(assets)
                if isinstance(assets, list)
                else 0
            )
            print(f"✅ Assets endpoint accessible: {asset_count} assets found")
        except APIException as e:
            print(f"⚠️  Assets endpoint error: {e}")

        try:
            permits = client.get_permits()
            permit_count = (
                len(permits.get("data", []))
                if isinstance(permits, dict)
                else len(permits)
                if isinstance(permits, list)
                else 0
            )
            print(f"✅ Permits endpoint accessible: {permit_count} permits found")
        except APIException as e:
            print(f"⚠️  Permits endpoint error: {e}")

        try:
            plans = client.get_plans()
            plan_count = (
                len(plans.get("data", []))
                if isinstance(plans, dict)
                else len(plans)
                if isinstance(plans, list)
                else 0
            )
            print(f"✅ Plans endpoint accessible: {plan_count} plans found")
        except APIException as e:
            print(f"⚠️  Plans endpoint error: {e}")

        print("\n🎉 Client test completed successfully!")
        print("\n📖 Next steps:")
        print("1. Register a user account using client.register()")
        print("2. Login with valid credentials using client.login()")
        print("3. Use authenticated endpoints to manage assets, permits, and plans")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
