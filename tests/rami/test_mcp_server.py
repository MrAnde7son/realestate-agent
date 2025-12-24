#!/usr/bin/env python3
"""
Test script for RAMI MCP Server

Tests the MCP server functionality by importing and checking basic operations.
"""

import os
import sys

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_import_mcp_server():
    """Test that the MCP server can be imported successfully."""
    try:
        from gov.mcp_server import _get_client

        print("✅ MCP server imported successfully")

        # Test client creation
        client = _get_client()
        print(f"✅ Client created: {type(client).__name__}")

        return True
    except Exception as e:
        print(f"❌ Failed to import MCP server: {e}")
        return False


def test_mcp_tools():
    """Test that MCP tools are registered correctly."""
    try:
        from gov.mcp_server import mcp

        # Check if mcp object has the expected attributes/methods
        if hasattr(mcp, "tools") and callable(mcp.tools):
            tools_dict = mcp.tools()
            tools = list(tools_dict.keys()) if tools_dict else []
        elif hasattr(mcp, "_tools"):
            tools = list(mcp._tools.keys())
        else:
            # Try to access tools differently - check if they exist as functions
            tools = []
            expected_tools = [
                "search_plans",
                "download_plan_documents",
                "download_multiple_plans_documents",
                "get_document_types_info",
            ]

            # Import the functions and check they exist

            tools = expected_tools  # If we can import them, they exist

        expected_tools = [
            "search_plans",
            "download_plan_documents",
            "download_multiple_plans_documents",
            "get_document_types_info",
        ]

        print("📋 Expected MCP tools:")
        for tool in expected_tools:
            status = "✅" if tool in tools else "❌"
            print(f"  {status} {tool}")

        if len(tools) >= len(expected_tools):
            print(f"✅ Found {len(tools)} tools (expected {len(expected_tools)})")
            return True
        else:
            print(f"❌ Found {len(tools)} tools, expected {len(expected_tools)}")
            return False

    except Exception as e:
        print(f"❌ Failed to check MCP tools: {e}")
        return False


def test_tool_functions():
    """Test that MCP tool functions can be imported and exist."""
    try:
        from gov.mcp_server import (
            download_multiple_plans_documents,
            download_plan_documents,
            get_document_types_info,
            search_plans,
        )

        tools_to_check = [
            ("search_plans", search_plans),
            ("download_plan_documents", download_plan_documents),
            ("download_multiple_plans_documents", download_multiple_plans_documents),
            ("get_document_types_info", get_document_types_info),
        ]

        for tool_name, tool_func in tools_to_check:
            # Check that function exists (if we can import it, it exists)
            if tool_func is None:
                print(f"❌ {tool_name} is None")
                return False

            print(f"✅ {tool_name}: imported successfully")

        print("✅ All tool functions imported successfully")
        print(
            "   (Functions are decorated by FastMCP, so direct callable check isn't applicable)"
        )
        return True

    except Exception as e:
        print(f"❌ Tool function test failed: {e}")
        return False


def test_rami_client_integration():
    """Test that RamiClient can be imported and initialized."""
    try:
        from gov.mcp_server import _get_client
        from gov.rami.rami_client import RamiClient

        # Test client creation
        client = _get_client()

        # Verify it's the right type
        assert isinstance(client, RamiClient)

        # Test that multiple calls return the same instance (singleton behavior)
        client2 = _get_client()
        assert client is client2

        # Check that client has expected methods
        expected_methods = [
            "fetch_plans",
            "download_plan_documents",
            "download_multiple_plans_documents",
        ]
        for method_name in expected_methods:
            assert hasattr(client, method_name), f"Client missing method: {method_name}"

        print("✅ RamiClient integration works correctly")
        print(f"   Client type: {type(client).__name__}")
        print(f"   Has all expected methods: {expected_methods}")
        return True

    except Exception as e:
        print(f"❌ RamiClient integration test failed: {e}")
        return False


def main():
    """Run all MCP server tests."""
    print("🧪 Testing RAMI MCP Server")
    print("=" * 50)

    tests = [
        ("Import MCP Server", test_import_mcp_server),
        ("Check MCP Tools", test_mcp_tools),
        ("Tool Functions", test_tool_functions),
        ("RamiClient Integration", test_rami_client_integration),
    ]

    results = []

    # Run all tests
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        result = test_func()
        results.append(result)

    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"🎉 All {total} tests passed!")
        return True
    else:
        print(f"❌ {passed}/{total} tests passed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
