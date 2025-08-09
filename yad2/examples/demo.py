#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 System Demonstration

This script demonstrates the complete functionality of your Yad2 scraper system
with dynamic parameters and MCP server capabilities.
"""

import json

# Support both package execution (python -m) and direct script execution
try:
    from yad2.core import Yad2SearchParameters, Yad2ParameterReference
    from yad2.scrapers import Yad2Scraper
except ModuleNotFoundError:
    import os, sys
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    from yad2.core import Yad2SearchParameters, Yad2ParameterReference
    from yad2.scrapers import Yad2Scraper

def demo_original_url_extraction():
    """Demo: Extract parameters from your original URL."""
    print("🔍 DEMO 1: Extract from Your Original URL")
    print("=" * 50)
    
    # Your original URL
    original_url = "https://www.yad2.co.il/realestate/forsale?maxPrice=10500000&property=5%2C33%2C39&topArea=2&area=1&city=5000&neighborhood=203"
    
    print("Original URL:")
    print(original_url)
    print()
    
    # Extract parameters
    try:
        from urllib.parse import urlparse, parse_qs, unquote
    except ImportError:
        from urlparse import urlparse, parse_qs
        from urllib import unquote
    
    parsed_url = urlparse(original_url)
    query_params = parse_qs(parsed_url.query)
    
    extracted_params = {}
    for key, values in query_params.items():
        if values:
            extracted_params[key] = unquote(values[0])
    
    # Create parameters object
    params = Yad2SearchParameters(**extracted_params)
    
    print("Extracted Parameters:")
    print(params.to_json())
    
    # Show human-readable interpretation
    ref = Yad2ParameterReference()
    print("\nHuman-readable interpretation:")
    for param, value in params.get_active_parameters().items():
        info = ref.get_parameter_info(param)
        print("• {}: {} ({})".format(param, value, info['description']))
        
        if param == 'property':
            prop_types = value.split(',')
            prop_names = [ref.get_property_types().get(int(p.strip()), 'Unknown') for p in prop_types]
            print("  Property types: {}".format(', '.join(prop_names)))
    
    return params

def demo_flexible_searches():
    """Demo: Create flexible searches for different areas."""
    print("\n🏠 DEMO 2: Flexible Search Examples")
    print("=" * 50)
    
    examples = [
        {
            "name": "Tel Aviv Luxury Apartments",
            "params": {
                "city": 5000,
                "property": "1,33",  # Apartments + Penthouses
                "minPrice": 5000000,
                "maxPrice": 15000000,
                "rooms": "4+",
                "elevator": 1,
                "parking": 2
            }
        },
        {
            "name": "Jerusalem Family Homes", 
            "params": {
                "topArea": 4,  # Jerusalem area
                "property": "1,2,5",  # Apartments + Houses + Duplexes
                "maxPrice": 8000000,
                "rooms": "4-5",
                "balcony": 1
            }
        },
        {
            "name": "Haifa Starter Homes",
            "params": {
                "city": 6300,  # Haifa
                "property": "1,39",  # Apartments + Studios
                "maxPrice": 3000000,
                "rooms": "2-3"
            }
        },
        {
            "name": "Center Region Investment Properties",
            "params": {
                "topArea": 2,  # Center
                "property": "1",  # Apartments only
                "minPrice": 2000000,
                "maxPrice": 6000000,
                "renovated": 1
            }
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print("{}. {}".format(i, example['name']))
        params = Yad2SearchParameters(**example['params'])
        url = params.build_url()
        print("   URL: {}".format(url))
        print("   Parameters: {}".format(len(params.get_active_parameters())))
        print()

def demo_scraper_integration():
    """Demo: Show scraper integration with parameters."""
    print("🤖 DEMO 3: Scraper Integration")
    print("=" * 50)
    
    # Create a search for Tel Aviv apartments
    params = Yad2SearchParameters(
        city=5000,  # Tel Aviv
        property="1",  # Apartments
        maxPrice=7000000,
        rooms="3-4",
        elevator=1,
        page=1
    )
    
    print("Creating scraper with parameters...")
    scraper = Yad2Scraper(params)
    
    print("Search Summary:")
    summary = scraper.get_search_summary()
    
    print("• Search URL: {}".format(summary['search_url']))
    print("• Active parameters: {}".format(len(summary['parameters'])))
    
    print("\nParameter Details:")
    for param, details in summary['parameter_descriptions'].items():
        print("  • {}: {} ({})".format(param, details['value'], details['description']))
    
    print("\nScraper is ready to search!")
    print("To actually scrape: listings = scraper.scrape_all_pages(max_pages=2)")

def demo_mcp_tools():
    """Demo: Show MCP server tool capabilities."""
    print("\n🔧 DEMO 4: MCP Server Tools")
    print("=" * 50)
    
    print("When you start the MCP server (python mcp_yad2_server.py),")
    print("your LLM will have access to these tools:")
    print()
    
    tools = [
        {
            "name": "search_real_estate",
            "description": "Search Yad2 listings with any parameters",
            "example": "Find 4-room apartments in Tel Aviv under 8M NIS with parking"
        },
        {
            "name": "get_search_parameters_reference", 
            "description": "Get complete parameter documentation",
            "example": "What search parameters are available?"
        },
        {
            "name": "analyze_search_results",
            "description": "Analyze price trends, locations, property types",
            "example": "Analyze the price distribution of my last search"
        },
        {
            "name": "save_search_results",
            "description": "Save results to JSON file with metadata",
            "example": "Save these results to a file"
        },
        {
            "name": "build_search_url",
            "description": "Generate Yad2 URLs without scraping", 
            "example": "Create a URL for penthouses in Jerusalem"
        }
    ]
    
    for i, tool in enumerate(tools, 1):
        print("{}. {}".format(i, tool['name']))
        print("   Description: {}".format(tool['description']))
        print("   Example use: \"{}\"".format(tool['example']))
        print()

def demo_advanced_features():
    """Demo: Show advanced features."""
    print("⚡ DEMO 5: Advanced Features")
    print("=" * 50)
    
    print("1. Parameter Validation:")
    params = Yad2SearchParameters()
    try:
        params.set_parameter('maxPrice', 'invalid')
    except ValueError as e:
        print("   ✅ Caught invalid price: {}".format(e))
    
    print("\n2. Property Type Translation:")
    ref = Yad2ParameterReference()
    prop_types = ref.get_property_types()
    print("   Available property types:")
    for prop_id, name in list(prop_types.items())[:5]:
        print("     {}: {}".format(prop_id, name))
    print("     ... and {} more".format(len(prop_types) - 5))
    
    print("\n3. URL Building:")
    params = Yad2SearchParameters(city=5000, property="1,33", maxPrice=8000000)
    url = params.build_url()
    print("   Generated URL: {}...".format(url[:60]))
    
    print("\n4. JSON Export with Metadata:")
    data = {
        'parameters': params.get_active_parameters(),
        'parameter_count': len(params.get_active_parameters()),
        'human_readable': True
    }
    print("   JSON export: {} characters".format(len(json.dumps(data))))

def main():
    """Run all demonstrations."""
    print("🏠 Yad2 Dynamic Real Estate Search System")
    print("=" * 60)
    print("Complete demonstration of your flexible Yad2 scraper!")
    print()
    
    # Run all demos
    original_params = demo_original_url_extraction()
    demo_flexible_searches()
    demo_scraper_integration()
    demo_mcp_tools()
    demo_advanced_features()
    
    print("\n" + "=" * 60)
    print("🎉 SYSTEM READY FOR USE!")
    print("=" * 30)
    print()
    print("What you can do now:")
    print("1. Interactive Search: python run_cli.py")
    print("2. Start MCP Server: python mcp_yad2_server.py")
    print("3. Use programmatically in your own scripts")
    print("4. Connect to your LLM for natural language queries")
    print()
    print("Key Benefits:")
    print("✅ Search ANY area (not just Tel Aviv)")
    print("✅ ALL Yad2 parameters supported")
    print("✅ LLM integration via MCP server")
    print("✅ Flexible and extensible architecture")
    print("✅ Built-in analytics and data export")
    
    return original_params

if __name__ == "__main__":
    main() # This script runs all the demos and showcases the full capabilities of your Yad2 scraper system.