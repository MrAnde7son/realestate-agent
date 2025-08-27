#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command-line interface for the Mavat MCP server.

This module provides a simple CLI for testing and using the Mavat tools
without requiring the full MCP server infrastructure.

Usage:
    python cli.py search "רמת החייל"
    python cli.py plan 12345
    python cli.py documents 12345
    python cli.py location "תל אביב" "הירקון"
    python cli.py block-parcel 666 1
    python cli.py cities
    python cli.py districts
    python cli.py streets
    python cli.py lookup "תל אביב"
"""

import asyncio
import sys
import argparse
from typing import Optional

# Add the mavat package to the path
sys.path.insert(0, '.')

from mcp.server import (
    search_plans, 
    get_plan_details, 
    get_plan_documents, 
    search_by_location,
    search_by_block_parcel,
    get_lookup_tables,
    get_districts,
    get_cities,
    get_streets,
    search_lookup
)


class CLIContext:
    """Simple context implementation for CLI usage."""
    
    async def info(self, message: str):
        print(f"ℹ️  {message}")
    
    async def error(self, message: str):
        print(f"❌ {message}")
    
    async def warning(self, message: str):
        print(f"⚠️  {message}")


async def cli_search(query: str, limit: int = 10):
    """CLI command for searching plans."""
    print(f"🔍 Searching for plans matching: '{query}'")
    print(f"📊 Limit: {limit}")
    print("-" * 50)
    
    context = CLIContext()
    result = await search_plans(context, query=query, limit=limit)
    
    if result.get("success"):
        print(f"✅ Found {result['pagination']['total_results']} plans")
        print()
        
        for i, plan in enumerate(result['plans'], 1):
            print(f"{i}. {plan['title'] or 'No title'}")
            print(f"   ID: {plan['plan_id']}")
            print(f"   Status: {plan['status'] or 'Unknown'}")
            print(f"   Authority: {plan['authority'] or 'Unknown'}")
            print(f"   Entity Number: {plan['entity_number'] or 'Unknown'}")
            print()
    else:
        print(f"❌ Search failed: {result.get('error')}")
        if 'message' in result:
            print(f"   Details: {result['message']}")


async def cli_plan_details(plan_id: str):
    """CLI command for getting plan details."""
    print(f"📋 Getting details for plan: {plan_id}")
    print("-" * 50)
    
    context = CLIContext()
    result = await get_plan_details(context, plan_id)
    
    if result.get("success"):
        plan = result['plan']
        print(f"✅ Plan details retrieved successfully")
        print()
        print(f"Name: {plan['plan_name'] or 'No name'}")
        print(f"Status: {plan['status'] or 'Unknown'}")
        print(f"Authority: {plan['authority'] or 'Unknown'}")
        print(f"Entity Number: {plan['entity_number'] or 'Unknown'}")
        print(f"Approval Date: {plan['approval_date'] or 'Unknown'}")
        
        if plan.get('raw'):
            print(f"\nRaw data keys: {list(plan['raw'].keys())}")
    else:
        print(f"❌ Failed to get plan details: {result.get('error')}")
        if 'message' in result:
            print(f"   Details: {result['message']}")


async def cli_documents(plan_id: str):
    """CLI command for getting plan documents."""
    print(f"📄 Getting documents for plan: {plan_id}")
    print("-" * 50)
    
    context = CLIContext()
    result = await get_plan_documents(context, plan_id)
    
    if result.get("success"):
        print(f"✅ Found {result['documents_count']} documents")
        print()
        
        for i, doc in enumerate(result['documents'], 1):
            print(f"{i}. {doc.get('filename', 'Unknown document')}")
            if doc.get('url'):
                print(f"   URL: {doc['url']}")
            print()
    else:
        print(f"❌ Failed to get documents: {result.get('error')}")
        if 'message' in result:
            print(f"   Details: {result['message']}")


async def cli_location_search(city: str, street: Optional[str] = None):
    """CLI command for location-based search."""
    print(f"🗺️  Searching for plans in location: city='{city}'")
    if street:
        print(f"   Street: '{street}'")
    print("-" * 50)
    
    context = CLIContext()
    result = await search_by_location(context, city=city, street=street)
    
    if result.get("success"):
        print(f"✅ Found {result['pagination']['total_results']} plans")
        print()
        
        for i, plan in enumerate(result['plans'][:5], 1):  # Show first 5
            print(f"{i}. {plan['title'] or 'No title'}")
            print(f"   ID: {plan['plan_id']}")
            print(f"   Status: {plan['status'] or 'Unknown'}")
            print()
    else:
        print(f"❌ Location search failed: {result.get('error')}")
        if 'message' in result:
            print(f"   Details: {result['message']}")


async def cli_block_parcel_search(block_number: str, parcel_number: str):
    """CLI command for block/parcel search."""
    print(f"🏗️  Searching for plans by block/parcel: block={block_number}, parcel={parcel_number}")
    print("-" * 50)
    
    context = CLIContext()
    result = await search_by_block_parcel(context, block_number, parcel_number)
    
    if result.get("success"):
        print(f"✅ Found {result['pagination']['total_results']} plans")
        print()
        
        for i, plan in enumerate(result['plans'][:5], 1):  # Show first 5
            print(f"{i}. {plan['title'] or 'No title'}")
            print(f"   ID: {plan['plan_id']}")
            print(f"   Status: {plan['status'] or 'Unknown'}")
            print()
    else:
        print(f"❌ Block/parcel search failed: {result.get('error')}")
        if 'message' in result:
            print(f"   Details: {result['message']}")


async def cli_get_cities():
    """CLI command for getting available cities."""
    print("🏙️  Getting available cities...")
    print("-" * 50)
    
    context = CLIContext()
    result = await get_cities(context)
    
    if result.get("success"):
        print(f"✅ Found {result['count']} cities")
        print()
        
        for i, city in enumerate(result['cities'][:10], 1):  # Show first 10
            print(f"{i}. {city['description']} (Code: {city['code']})")
        if result['count'] > 10:
            print(f"   ... and {result['count'] - 10} more cities")
    else:
        print(f"❌ Failed to get cities: {result.get('error')}")
        if 'message' in result:
            print(f"   Details: {result['message']}")


async def cli_get_districts():
    """CLI command for getting available districts."""
    print("🗺️  Getting available districts...")
    print("-" * 50)
    
    context = CLIContext()
    result = await get_districts(context)
    
    if result.get("success"):
        print(f"✅ Found {result['count']} districts")
        print()
        
        for i, district in enumerate(result['districts'][:10], 1):  # Show first 10
            print(f"{i}. {district['description']} (Code: {district['code']})")
        if result['count'] > 10:
            print(f"   ... and {result['count'] - 10} more districts")
    else:
        print(f"❌ Failed to get districts: {result.get('error')}")
        if 'message' in result:
            print(f"   Details: {result['message']}")


async def cli_get_streets():
    """CLI command for getting available streets."""
    print("🛣️  Getting available streets...")
    print("-" * 50)
    
    context = CLIContext()
    result = await get_streets(context)
    
    if result.get("success"):
        print(f"✅ Found {result['count']} streets")
        print()
        
        for i, street in enumerate(result['streets'][:10], 1):  # Show first 10
            print(f"{i}. {street['description']} (Code: {street['code']})")
        if result['count'] > 10:
            print(f"   ... and {result['count'] - 10} more streets")
    else:
        print(f"❌ Failed to get streets: {result.get('error')}")
        if 'message' in result:
            print(f"   Details: {result['message']}")


async def cli_lookup_search(search_text: str, table_type: Optional[str] = None):
    """CLI command for searching lookup tables."""
    table_desc = f"table {table_type}" if table_type else "all tables"
    print(f"🔍 Searching lookup tables for '{search_text}' in {table_desc}")
    print("-" * 50)
    
    context = CLIContext()
    result = await search_lookup(context, search_text, table_type)
    
    if result.get("success"):
        print(f"✅ Found {result['count']} matching items")
        print()
        
        for i, item in enumerate(result['results'][:10], 1):  # Show first 10
            print(f"{i}. {item['description']} (Code: {item['code']})")
        if result['count'] > 10:
            print(f"   ... and {result['count'] - 10} more items")
    else:
        print(f"❌ Lookup search failed: {result.get('error')}")
        if 'message' in result:
            print(f"   Details: {result['message']}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Mavat MCP Server CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py search "רמת החייל" --limit 5
  python cli.py plan 12345
  python cli.py documents 12345
  python cli.py location "תל אביב" "הירקון"
  python cli.py block-parcel 666 1
  python cli.py cities
  python cli.py districts
  python cli.py streets
  python cli.py lookup "תל אביב"
  python cli.py lookup "הירקון" --table-type 7
        """
    )
    
    parser.add_argument(
        'command',
        choices=[
            'search', 'plan', 'documents', 'location', 'block-parcel',
            'cities', 'districts', 'streets', 'lookup'
        ],
        help='Command to execute'
    )
    
    parser.add_argument(
        'identifier',
        nargs='?',
        help='Search query, plan ID, city name, or other identifier'
    )
    
    parser.add_argument(
        'secondary',
        nargs='?',
        help='Secondary parameter (e.g., street name for location search)'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=10,
        help='Maximum number of search results (default: 10)'
    )
    
    parser.add_argument(
        '--table-type', '-t',
        help='Table type for lookup search (4=districts, 5=cities, 6=plan_areas, 7=streets, etc.)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == 'search':
            if not args.identifier:
                print("❌ Search command requires a query string")
                sys.exit(1)
            asyncio.run(cli_search(args.identifier, args.limit))
            
        elif args.command == 'plan':
            if not args.identifier:
                print("❌ Plan command requires a plan ID")
                sys.exit(1)
            asyncio.run(cli_plan_details(args.identifier))
            
        elif args.command == 'documents':
            if not args.identifier:
                print("❌ Documents command requires a plan ID")
                sys.exit(1)
            asyncio.run(cli_documents(args.identifier))
            
        elif args.command == 'location':
            if not args.identifier:
                print("❌ Location command requires a city name")
                sys.exit(1)
            asyncio.run(cli_location_search(args.identifier, args.secondary))
            
        elif args.command == 'block-parcel':
            if not args.identifier or not args.secondary:
                print("❌ Block-parcel command requires both block and parcel numbers")
                sys.exit(1)
            asyncio.run(cli_block_parcel_search(args.identifier, args.secondary))
            
        elif args.command == 'cities':
            asyncio.run(cli_get_cities())
            
        elif args.command == 'districts':
            asyncio.run(cli_get_districts())
            
        elif args.command == 'streets':
            asyncio.run(cli_get_streets())
            
        elif args.command == 'lookup':
            if not args.identifier:
                print("❌ Lookup command requires search text")
                sys.exit(1)
            asyncio.run(cli_lookup_search(args.identifier, args.table_type))
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Make sure the Mavat API is accessible")
        sys.exit(1)


if __name__ == "__main__":
    main()

