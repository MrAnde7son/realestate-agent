#!/usr/bin/env python3
"""
Test script to verify OpenAPI spec generation is working.
"""

import requests
import sys
import os
from pathlib import Path

API_BASE_URL = "http://localhost:8000"
OPENAPI_SPEC_URL = f"{API_BASE_URL}/api/docs/openapi.yaml"
SWAGGER_UI_URL = f"{API_BASE_URL}/api/docs/"
REDOC_URL = f"{API_BASE_URL}/api/docs/redoc/"


def get_auth_headers():
    """Get authentication headers if token is available."""
    token = os.getenv("REALESTATE_API_TOKEN")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def test_openapi_endpoints():
    """Test that all OpenAPI endpoints are working."""
    print("🧪 Testing OpenAPI endpoints...")

    # Test OpenAPI YAML spec
    print(f"📄 Testing OpenAPI YAML: {OPENAPI_SPEC_URL}")
    try:
        response = requests.get(OPENAPI_SPEC_URL, timeout=10)
        response.raise_for_status()

        if response.headers.get("content-type", "").startswith("text/yaml"):
            print("✅ OpenAPI YAML spec is accessible")
        else:
            print(f"⚠️  Unexpected content type: {response.headers.get('content-type')}")

        # Save the spec for inspection
        spec_path = Path("client/openapi.yaml")
        spec_path.parent.mkdir(exist_ok=True)
        with open(spec_path, "w") as f:
            f.write(response.text)
        print(f"💾 Saved spec to {spec_path}")

    except requests.RequestException as e:
        print(f"❌ Failed to fetch OpenAPI YAML: {e}")
        return False

    # Test Swagger UI
    print(f"🌐 Testing Swagger UI: {SWAGGER_UI_URL}")
    try:
        response = requests.get(SWAGGER_UI_URL, timeout=10)
        response.raise_for_status()
        print("✅ Swagger UI is accessible")
    except requests.RequestException as e:
        print(f"❌ Failed to access Swagger UI: {e}")
        return False

    # Test ReDoc
    print(f"📚 Testing ReDoc: {REDOC_URL}")
    try:
        response = requests.get(REDOC_URL, timeout=10)
        response.raise_for_status()
        print("✅ ReDoc is accessible")
    except requests.RequestException as e:
        print(f"❌ Failed to access ReDoc: {e}")
        return False

    return True


def test_api_endpoints():
    """Test some basic API endpoints."""
    print("\n🔍 Testing basic API endpoints...")

    # Test schema endpoint
    schema_url = f"{API_BASE_URL}/api/schema/"
    try:
        response = requests.get(schema_url, timeout=10)
        response.raise_for_status()
        print("✅ Schema endpoint is working")
    except requests.RequestException as e:
        print(f"❌ Schema endpoint failed: {e}")
        return False

    # Test assets endpoint
    assets_url = f"{API_BASE_URL}/api/assets"
    try:
        headers = get_auth_headers()
        response = requests.get(assets_url, headers=headers, timeout=10)
        if response.status_code == 200:
            print("✅ Assets endpoint is working")
            data = response.json()
            asset_count = len(data.get("rows", []))
            print(f"   Found {asset_count} asset(s)")
        elif response.status_code == 401:
            if headers:
                print(
                    f"❌ Assets endpoint returned 401 Unauthorized - token may be invalid"
                )
                print(f"   Response: {response.text[:200]}")
            else:
                print("⚠️  Assets endpoint returned 401 (no token provided)")
        else:
            print(f"⚠️  Assets endpoint returned {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Assets endpoint failed: {e}")
        return False

    return True


def main():
    """Main test function."""
    print("🚀 Testing OpenAPI and API endpoints...")
    print(f"🌐 API Base URL: {API_BASE_URL}")

    # Check for API token
    token = os.getenv("REALESTATE_API_TOKEN")
    if token:
        print(f"🔑 Using API token: {token[:20]}...")
    else:
        print("⚠️  No REALESTATE_API_TOKEN environment variable found")
        print("   Some endpoints may require authentication")

    # Test OpenAPI endpoints
    if not test_openapi_endpoints():
        print("\n❌ OpenAPI endpoints test failed")
        sys.exit(1)

    # Test basic API endpoints
    if not test_api_endpoints():
        print("\n❌ API endpoints test failed")
        sys.exit(1)

    print("\n✅ All tests passed!")
    print("\n🎉 OpenAPI spec is ready for SDK generation!")
    print(f"📖 View documentation at: {SWAGGER_UI_URL}")
    print(f"📚 View ReDoc at: {REDOC_URL}")
    print(f"📄 Download spec at: {OPENAPI_SPEC_URL}")


if __name__ == "__main__":
    main()
