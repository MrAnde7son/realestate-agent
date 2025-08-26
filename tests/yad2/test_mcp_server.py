#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Yad2 MCP Server

Test suite for the enhanced Yad2 MCP server functionality.
"""

import pytest
import asyncio
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import MCP server functions (only the ones that actually exist)
from yad2.mcp.server import (
    get_all_property_types,
    search_locations,
    get_search_parameters_reference,
    build_search_url,
    search_real_estate
)

# Extract the underlying functions from the FastMCP tools
get_all_property_types_func = get_all_property_types.fn
search_locations_func = search_locations.fn
get_search_parameters_reference_func = get_search_parameters_reference.fn
build_search_url_func = build_search_url.fn
search_real_estate_func = search_real_estate.fn

# Mock context for testing
class MockContext:
    """Mock MCP context for testing."""
    
    async def info(self, message):
        print(f"INFO: {message}")
    
    async def error(self, message):
        print(f"ERROR: {message}")


@pytest.fixture
def mock_ctx():
    """Provide mock context for tests."""
    return MockContext()


class TestPropertyTypeFunctionality:
    """Test property type related functions."""
    
    @pytest.mark.asyncio
    async def test_get_all_property_types(self, mock_ctx):
        """Test getting all property types."""
        result = await get_all_property_types_func(mock_ctx)
        
        assert result["success"] is True
        assert "property_types" in result
        assert "total_types" in result
        assert isinstance(result["property_types"], dict)
        assert result["total_types"] > 0
        
        # Check that each property type has required fields
        for code, prop_type in result["property_types"].items():
            assert isinstance(code, int)
            assert "hebrew" in prop_type
            assert "english" in prop_type
            assert "code" in prop_type
            assert prop_type["code"] == code


class TestLocationServices:
    """Test location service functions."""

    @pytest.mark.asyncio
    async def test_search_locations(self, mock_ctx):
        """Test location search."""
        result = await search_locations_func(mock_ctx, search_text="רמת")

        assert result["success"] is True
        assert "locations" in result
        assert "search_text" in result
        assert result["search_text"] == "רמת"

        # Should have some location data
        locations = result["locations"]
        assert isinstance(locations, dict)


class TestSearchFunctionality:
    """Test search functionality."""
    
    @pytest.mark.asyncio
    async def test_get_search_parameters_reference(self, mock_ctx):
        """Test getting search parameters reference."""
        result = await get_search_parameters_reference_func(mock_ctx)
        
        # This function doesn't return a 'success' key
        assert "categories" in result
        assert "all_parameters" in result
        
        categories = result["categories"]
        assert isinstance(categories, dict)
        assert "Price Parameters" in categories
        assert "Location Parameters" in categories
        assert "Property Types" in categories
    
    @pytest.mark.asyncio
    async def test_build_search_url(self, mock_ctx):
        """Test building search URLs."""
        # Test with basic parameters
        result = await build_search_url_func(
            mock_ctx,
            property="5",
            city="5000",
            neighborhood="203"
        )
        
        assert result["success"] is True
        assert "url" in result
        assert "parameters" in result
        assert "descriptions" in result
        
        # Check that parameters were set correctly
        params = result["parameters"]
        assert params.get("property") == "5"
        # Note: city and neighborhood get converted to integers
        assert params.get("city") == 5000
        assert params.get("neighborhood") == 203
        
        # Test with Hebrew property name
        result = await build_search_url_func(
            mock_ctx,
            property="בית פרטי",
            city="5000"
        )
        
        assert result["success"] is True
        # Should convert Hebrew to code
        params = result["parameters"]
        assert "property" in params
    
    @pytest.mark.asyncio
    async def test_search_real_estate(self, mock_ctx):
        """Test real estate search."""
        # Test with basic search
        result = await search_real_estate_func(
            mock_ctx,
            property="5",
            city="5000",
            neighborhood="203",
            max_pages=1
        )

        assert result["success"] is True
        assert "total_assets" in result
        assert "assets_preview" in result
        assert "search_url" in result

        # Should have some results
        assert result["total_assets"] >= 0
        assert isinstance(result["assets_preview"], list)


class TestIntegration:
    """Integration tests for complex workflows."""
    
    @pytest.mark.asyncio
    async def test_property_search_workflow(self, mock_ctx):
        """Test a complete property search workflow."""
        # Step 1: Get all property types
        all_types = await get_all_property_types_func(mock_ctx)
        assert all_types["success"] is True
        
        # Step 2: Get search parameters reference
        params_ref = await get_search_parameters_reference_func(mock_ctx)
        # This function doesn't return a 'success' key
        assert "categories" in params_ref
        
        # Step 3: Build a search URL
        search_url = await build_search_url_func(
            mock_ctx,
            property="5",
            city="5000"
        )
        assert search_url["success"] is True
        
        # Step 4: Perform a search
        search_results = await search_real_estate_func(
            mock_ctx,
            property="5",
            city="5000",
            max_pages=1
        )
        assert search_results["success"] is True
    
    @pytest.mark.asyncio
    async def test_location_workflow(self, mock_ctx):
        """Test a complete location workflow."""
        # Step 1: Search for locations
        locations = await search_locations_func(mock_ctx, search_text="רמת")
        assert locations["success"] is True
        
        # Step 2: Use location in search
        if locations["locations"].get("hoods"):
            # Get first neighborhood
            first_hood = locations["locations"]["hoods"][0]
            city_id = first_hood["cityId"]
            hood_id = first_hood["hoodId"]
            
            # Build search URL with found location
            search_url = await build_search_url_func(
                mock_ctx,
                property="5",
                city=city_id,
                neighborhood=hood_id
            )
            assert search_url["success"] is True


def test_mock_context():
    """Test that our mock context works correctly."""
    ctx = MockContext()
    
    # Test that we can call the async methods
    async def test_async():
        await ctx.info("Test message")
        await ctx.error("Test error")
    
    asyncio.run(test_async())


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
