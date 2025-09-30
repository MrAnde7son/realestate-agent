# -*- coding: utf-8 -*-
"""
Simple example for Nadlan API Client - Parse neighborhood data.

This file shows how to get and analyze neighborhood data from the Nadlan API.
"""

from .api_client import NadlanAPIClient
from .models import parse_neighborhood_data, format_price_report


def example_neighborhood_analysis():
    """Simple neighborhood analysis example."""
    print("🏘️ Analyzing neighborhood data")
    
    client = NadlanAPIClient()
    
    try:
        # Get real data from the API
        raw_data = client.get_neighborhood_data("65210036")
        print(f"✅ Retrieved data for: {raw_data.get('neighborhoodName')}")
        
        # Parse the data
        parsed_data = parse_neighborhood_data(raw_data)
        
        # Generate report
        report = format_price_report(parsed_data)
        print(report)
        
        # Show some key insights
        print(f"\n🔍 Key Insights:")
        print(f"Neighborhood: {parsed_data.neighborhood_name}")
        print(f"Settlement: {parsed_data.settlement_name}")
        print(f"Price Change: {parsed_data.market_indexes.price_increases:+.2f}%")
        
        # Handle None values gracefully
        yield_rate = parsed_data.market_indexes.yield_rate
        if yield_rate is not None:
            print(f"Yield Rate: {yield_rate:.2f}%")
        else:
            print("Yield Rate: לא ידוע")
            
        print(f"Luxury Index: {parsed_data.market_indexes.luxury_index}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    example_neighborhood_analysis()