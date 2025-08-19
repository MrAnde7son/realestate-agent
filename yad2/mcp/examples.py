#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Yad2 MCP Server - Usage Examples

This file contains practical examples of how to use the Yad2 MCP server
for various real estate search and analysis tasks.
"""

import asyncio
import json
from typing import Dict, Any

# Note: This assumes the MCP server is running and accessible
# In practice, you would connect to the MCP server using a proper MCP client


class Yad2MCPExamples:
    """Examples of how to use the Yad2 MCP server."""
    
    def __init__(self):
        # In practice, this would be an MCP client connection
        self.client = None
    
    async def example_1_basic_property_search(self):
        """Example 1: Basic property search."""
        print("=== Example 1: Basic Property Search ===")
        
        # Search for apartments in Tel Aviv under 5M NIS
        search_params = {
            "property": "1",        # Apartment
            "maxPrice": 5000000,    # 5M NIS
            "city": "5000",         # Tel Aviv
            "max_pages": 2
        }
        
        print("Search parameters:", json.dumps(search_params, indent=2))
        
        # result = await self.client.call("search_real_estate", search_params)
        # print("Search results:", json.dumps(result, indent=2))
        
        print("This would search for apartments in Tel Aviv under 5M NIS")
        print()
    
    async def example_2_property_type_discovery(self):
        """Example 2: Discover and explore property types."""
        print("=== Example 2: Property Type Discovery ===")
        
        # Get all property types
        print("1. Getting all property types...")
        # all_types = await self.client.call("get_all_property_types")
        
        # Search for specific property types
        print("2. Searching for apartment types...")
        search_params = {"search_term": "דירה"}
        # apartments = await self.client.call("search_property_types", search_params)
        
        # Get details about a specific property type
        print("3. Getting details for apartment (code 1)...")
        details_params = {"property_code": 1}
        # details = await self.client.call("get_property_type_details", details_params)
        
        # Convert to English
        print("4. Converting to English...")
        convert_params = {
            "value": "1",
            "from_format": "yad2",
            "to_format": "english"
        }
        # english_name = await self.client.call("convert_property_type", convert_params)
        
        print("This example demonstrates property type discovery")
        print()
    
    async def example_3_location_services(self):
        """Example 3: Location services and search."""
        print("=== Example 3: Location Services ===")
        
        # Search for locations starting with "רמת"
        print("1. Searching for locations starting with 'רמת'...")
        location_params = {"search_text": "רמת"}
        # locations = await self.client.call("search_locations", location_params)
        
        # Get all location codes
        print("2. Getting all location codes...")
        # location_codes = await self.client.call("get_location_codes")
        
        # Get specific city information
        print("3. Getting info for Ramat Gan (city ID 8600)...")
        city_params = {"city_id": "8600"}
        # city_info = await self.client.call("get_city_info", city_params)
        
        print("This example demonstrates location services")
        print()
    
    async def example_4_intelligent_recommendations(self):
        """Example 4: Get intelligent property recommendations."""
        print("=== Example 4: Intelligent Recommendations ===")
        
        # Get recommendations based on criteria
        criteria = {
            "budget": 3000000,      # 3M NIS budget
            "family_size": 4,       # Family of 4
            "location": "תל אביב",   # Tel Aviv
            "investment": False     # Not for investment
        }
        
        print("Criteria:", json.dumps(criteria, indent=2))
        
        # recommendations = await self.client.call("get_property_type_recommendations", criteria)
        
        print("This would return intelligent property type recommendations")
        print()
    
    async def example_5_market_analysis(self):
        """Example 5: Market analysis and trends."""
        print("=== Example 5: Market Analysis ===")
        
        # Get overall market trends
        print("1. Getting market trends...")
        # trends = await self.client.call("get_property_type_trends")
        
        # Get detailed market analysis for apartments
        print("2. Getting market analysis for apartments...")
        analysis_params = {"property_type_code": 1}
        # analysis = await self.client.call("get_market_analysis", analysis_params)
        
        # Get property type statistics
        print("3. Getting property type statistics...")
        # stats = await self.client.call("get_property_type_statistics")
        
        # Generate comparison table
        print("4. Generating comparison table...")
        # comparison_table = await self.client.call("get_comparison_table")
        
        print("This example demonstrates market analysis capabilities")
        print()
    
    async def example_6_advanced_search(self):
        """Example 6: Advanced search with property type names."""
        print("=== Example 6: Advanced Search ===")
        
        # Search using property type name instead of code
        search_params = {
            "property_type_name": "דירה",
            "maxPrice": 4000000,
            "location": "רמת גן",
            "max_pages": 2
        }
        
        print("Search parameters:", json.dumps(search_params, indent=2))
        
        # results = await self.client.call("search_with_property_type", search_params)
        
        # Get search recommendations
        print("Getting search recommendations...")
        recommendation_params = {
            "budget": 2500000,
            "family_size": 3,
            "location": "תל אביב"
        }
        
        # suggestions = await self.client.call("get_search_recommendations", recommendation_params)
        
        print("This example demonstrates advanced search capabilities")
        print()
    
    async def example_7_comparison_and_validation(self):
        """Example 7: Compare property types and validate codes."""
        print("=== Example 7: Comparison and Validation ===")
        
        # Compare two property types
        comparison_params = {"type1": "1", "type2": "5"}  # Apartment vs Villa
        # comparison = await self.client.call("compare_property_types", comparison_params)
        
        print("Comparing apartment (1) vs villa (5)...")
        
        # Validate property type codes
        valid_codes = ["1", "5", "33", "999"]  # Last one is invalid
        for code in valid_codes:
            validation_params = {"code": code}
            # validation = await self.client.call("validate_property_type_code", validation_params)
            print(f"Validating code {code}...")
        
        print("This example demonstrates comparison and validation")
        print()
    
    async def example_8_export_and_bulk_operations(self):
        """Example 8: Export data and bulk operations."""
        print("=== Example 8: Export and Bulk Operations ===")
        
        # Export property types to different formats
        formats = ["json", "csv", "excel"]
        for fmt in formats:
            export_params = {"format": fmt}
            # result = await self.client.call("export_property_types", export_params)
            print(f"Exporting to {fmt} format...")
        
        # Perform bulk operations
        operations = ["summary", "export_all", "validate_all"]
        for operation in operations:
            bulk_params = {"operation": operation}
            # result = await self.client.call("bulk_property_type_operations", bulk_params)
            print(f"Performing bulk operation: {operation}...")
        
        print("This example demonstrates export and bulk operations")
        print()
    
    async def example_9_testing_and_diagnostics(self):
        """Example 9: Testing and diagnostics."""
        print("=== Example 9: Testing and Diagnostics ===")
        
        # Check API status
        print("1. Checking API status...")
        # status = await self.client.call("get_api_status")
        
        # Run comprehensive tests
        print("2. Running comprehensive tests...")
        # test_results = await self.client.call("test_property_type_functionality")
        
        # Get help and documentation
        print("3. Getting help documentation...")
        # help_info = await self.client.call("get_property_types_help")
        
        print("This example demonstrates testing and diagnostics")
        print()
    
    async def example_10_complete_workflow(self):
        """Example 10: Complete real estate search workflow."""
        print("=== Example 10: Complete Workflow ===")
        
        # Step 1: Get recommendations based on user criteria
        print("Step 1: Getting recommendations...")
        criteria = {
            "budget": 3500000,
            "family_size": 3,
            "location": "רמת השרון",
            "investment": False
        }
        # recommendations = await self.client.call("get_search_recommendations", criteria)
        
        # Step 2: Search using recommended property type
        print("Step 2: Searching with recommended property type...")
        search_params = {
            "property_type_name": "דירה",  # From recommendations
            "maxPrice": 3500000,
            "location": "רמת השרון",
            "max_pages": 3
        }
        # search_results = await self.client.call("search_with_property_type", search_params)
        
        # Step 3: Analyze results
        print("Step 3: Analyzing search results...")
        # analysis = await self.client.call("analyze_search_results", {"analysis_type": "summary"})
        
        # Step 4: Save results
        print("Step 4: Saving results...")
        # saved_file = await self.client.call("save_search_results")
        
        print("Complete workflow executed successfully!")
        print()
    
    async def run_all_examples(self):
        """Run all examples."""
        print("🏠 Yad2 MCP Server - Usage Examples")
        print("=" * 50)
        print()
        
        examples = [
            self.example_1_basic_property_search,
            self.example_2_property_type_discovery,
            self.example_3_location_services,
            self.example_4_intelligent_recommendations,
            self.example_5_market_analysis,
            self.example_6_advanced_search,
            self.example_7_comparison_and_validation,
            self.example_8_export_and_bulk_operations,
            self.example_9_testing_and_diagnostics,
            self.example_10_complete_workflow
        ]
        
        for example in examples:
            await example()
        
        print("=" * 50)
        print("All examples completed!")
        print()
        print("Note: These are demonstration examples.")
        print("To run actual MCP calls, connect to a running Yad2 MCP server.")


def main():
    """Main function to run examples."""
    examples = Yad2MCPExamples()
    asyncio.run(examples.run_all_examples())


if __name__ == "__main__":
    main()
