#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo script for the Mavat MCP server.

This script demonstrates how to use the Mavat MCP server tools
for searching plans and retrieving plan details.

Usage:
    python demo.py
"""

import asyncio
import os
import sys

# Add the mavat package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from mcp.server import (
    get_plan_details,
    get_plan_documents,
    get_plan_gis_layers,
    search_plans,
)


class MockContext:
    """Mock context for demo purposes."""
    
    async def info(self, message):
        print(f"INFO: {message}")
    
    async def error(self, message):
        print(f"ERROR: {message}")
    
    async def warning(self, message):
        print(f"WARNING: {message}")


async def demo_search_plans():
    """Demonstrate plan search functionality."""
    print("\n=== Demo: Search Plans ===")
    
    context = MockContext()
    
    # Search for plans in a specific area
    result = await search_plans(context, "רמת החייל", limit=5)
    
    if result.get("success"):
        print(f"Found {result['total_results']} plans:")
        for plan in result['plans'][:3]:  # Show first 3
            print(f"  - {plan['title']} (ID: {plan['plan_id']})")
            print(f"    Status: {plan['status']}")
            print(f"    Authority: {plan['authority']}")
    else:
        print(f"Search failed: {result.get('error')}")


async def demo_get_plan_details():
    """Demonstrate plan details retrieval."""
    print("\n=== Demo: Get Plan Details ===")
    
    context = MockContext()
    
    # Get details for a specific plan (using a sample ID)
    plan_id = "12345"  # This would be a real plan ID in practice
    result = await get_plan_details(context, plan_id)
    
    if result.get("success"):
        plan = result['plan']
        print(f"Plan: {plan['plan_name']}")
        print(f"Status: {plan['status']}")
        print(f"Authority: {plan['authority']}")
        print(f"Last Update: {plan['last_update']}")
    else:
        print(f"Failed to get plan details: {result.get('error')}")


async def demo_get_plan_documents():
    """Demonstrate document retrieval."""
    print("\n=== Demo: Get Plan Documents ===")
    
    context = MockContext()
    
    # Get documents for a specific plan
    plan_id = "12345"
    result = await get_plan_documents(context, plan_id)
    
    if result.get("success"):
        print(f"Found {result['documents_count']} documents:")
        for doc in result['documents'][:3]:  # Show first 3
            print(f"  - {doc.get('name', 'Unknown document')}")
    else:
        print(f"Failed to get documents: {result.get('error')}")


async def demo_get_plan_gis_layers():
    """Demonstrate GIS layers retrieval."""
    print("\n=== Demo: Get Plan GIS Layers ===")
    
    context = MockContext()
    
    # Get GIS layers for a specific plan
    plan_id = "12345"
    result = await get_plan_gis_layers(context, plan_id)
    
    if result.get("success"):
        print(f"Found {result['layers_count']} GIS layers:")
        for layer in result['layers'][:3]:  # Show first 3
            print(f"  - {layer.get('name', 'Unknown layer')}")
    else:
        print(f"Failed to get GIS layers: {result.get('error')}")


async def main():
    """Run all demos."""
    print("Mavat MCP Server Demo")
    print("=" * 50)
    
    try:
        await demo_search_plans()
        await demo_get_plan_details()
        await demo_get_plan_documents()
        await demo_get_plan_gis_layers()
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        print("Note: This demo requires Playwright to be installed.")
        print("Install with: pip install playwright && playwright install")


if __name__ == "__main__":
    asyncio.run(main())

