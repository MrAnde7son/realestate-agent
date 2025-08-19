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

# Import MCP server functions (for testing individual functions)
from yad2.mcp.server import (
    get_all_property_types,
    search_property_types,
    get_property_type_details,
    convert_property_type,
    validate_property_type_code,
    search_locations,
    get_location_codes,
    get_property_type_recommendations,
    compare_property_types,
    get_property_type_trends,
    export_property_types,
    get_api_status,
    test_property_type_functionality
)

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
        result = await get_all_property_types(mock_ctx)
        
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
    
    @pytest.mark.asyncio
    async def test_search_property_types(self, mock_ctx):
        """Test searching property types."""
        # Test Hebrew search
        result = await search_property_types(mock_ctx, search_term="דירה")
        
        assert result["success"] is True
        assert "exact_matches" in result
        assert "suggestions" in result
        assert "search_term" in result
        assert result["search_term"] == "דירה"
        
        # Should find apartment types
        assert len(result["exact_matches"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_property_type_details(self, mock_ctx):
        """Test getting property type details."""
        # Test with valid code (apartment)
        result = await get_property_type_details(mock_ctx, property_code=1)
        
        assert result["success"] is True
        assert "property_type" in result
        assert "market_analysis" in result
        
        property_type = result["property_type"]
        assert property_type["code"] == 1
        assert "name" in property_type
        assert "category" in property_type
        assert "description" in property_type
        
        # Test with invalid code
        result = await get_property_type_details(mock_ctx, property_code=999)
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_convert_property_type(self, mock_ctx):
        """Test property type conversion."""
        # Test Yad2 code to English
        result = await convert_property_type(
            mock_ctx, 
            value="1", 
            from_format="yad2", 
            to_format="english"
        )
        
        assert result["success"] is True
        assert "converted_value" in result
        assert result["converted_value"] == "Apartment"
        
        # Test invalid conversion
        result = await convert_property_type(
            mock_ctx, 
            value="999", 
            from_format="yad2", 
            to_format="english"
        )
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_validate_property_type_code(self, mock_ctx):
        """Test property type code validation."""
        # Test valid code
        result = await validate_property_type_code(mock_ctx, code="1")
        
        assert result["success"] is True
        assert "validation" in result
        assert result["validation"]["valid"] is True
        
        # Test invalid code
        result = await validate_property_type_code(mock_ctx, code="999")
        
        assert result["success"] is True
        assert "validation" in result
        assert result["validation"]["valid"] is False


class TestLocationServices:
    """Test location service functions."""
    
    @pytest.mark.asyncio
    async def test_search_locations(self, mock_ctx):
        """Test location search."""
        result = await search_locations(mock_ctx, search_text="רמת")
        
        assert result["success"] is True
        assert "locations" in result
        assert "search_text" in result
        assert result["search_text"] == "רמת"
        
        # Should have some location data
        locations = result["locations"]
        assert isinstance(locations, dict)
    
    @pytest.mark.asyncio
    async def test_get_location_codes(self, mock_ctx):
        """Test getting location codes."""
        result = await get_location_codes(mock_ctx)
        
        assert result["success"] is True
        assert "location_codes" in result
        
        location_codes = result["location_codes"]
        assert "top_areas" in location_codes
        assert "areas" in location_codes
        assert "cities" in location_codes
        assert "neighborhoods" in location_codes


class TestAnalysisAndRecommendations:
    """Test analysis and recommendation functions."""
    
    @pytest.mark.asyncio
    async def test_get_property_type_recommendations(self, mock_ctx):
        """Test getting property type recommendations."""
        result = await get_property_type_recommendations(
            mock_ctx,
            budget=3000000,
            family_size=4,
            location="תל אביב"
        )
        
        assert result["success"] is True
        assert "recommendations" in result
        assert "criteria" in result
        
        # Check criteria were recorded correctly
        criteria = result["criteria"]
        assert criteria["budget"] == 3000000
        assert criteria["family_size"] == 4
        assert criteria["location"] == "תל אביב"
        
        # Should have recommendations
        recommendations = result["recommendations"]
        assert isinstance(recommendations, list)
    
    @pytest.mark.asyncio
    async def test_compare_property_types(self, mock_ctx):
        """Test comparing property types."""
        result = await compare_property_types(mock_ctx, type1="1", type2="5")
        
        assert result["success"] is True
        assert "comparison" in result
        
        comparison = result["comparison"]
        assert "type1" in comparison
        assert "type2" in comparison
        assert "similarities" in comparison
        assert "differences" in comparison
    
    @pytest.mark.asyncio
    async def test_get_property_type_trends(self, mock_ctx):
        """Test getting property type trends."""
        result = await get_property_type_trends(mock_ctx)
        
        assert result["success"] is True
        assert "trends" in result
        
        trends = result["trends"]
        assert isinstance(trends, dict)


class TestUtilityFunctions:
    """Test utility and administrative functions."""
    
    @pytest.mark.asyncio
    async def test_export_property_types(self, mock_ctx):
        """Test exporting property types."""
        # Test JSON export
        result = await export_property_types(mock_ctx, format="json")
        
        assert result["success"] is True
        assert "filename" in result
        assert result["format"] == "json"
        
        # Test invalid format
        result = await export_property_types(mock_ctx, format="invalid")
        assert result["success"] is False
    
    @pytest.mark.asyncio
    async def test_get_api_status(self, mock_ctx):
        """Test getting API status."""
        result = await get_api_status(mock_ctx)
        
        assert result["success"] is True
        assert "status" in result
        
        status = result["status"]
        assert "property_types_available" in status
        assert "total_property_types" in status
        assert "api_endpoints" in status
    
    @pytest.mark.asyncio
    async def test_functionality_test(self, mock_ctx):
        """Test the comprehensive functionality test."""
        result = await test_property_type_functionality(mock_ctx)
        
        assert result["success"] is True
        assert "test_results" in result
        
        test_results = result["test_results"]
        assert "tests_run" in test_results
        assert "tests_passed" in test_results
        assert "tests_failed" in test_results
        assert "details" in test_results
        assert "success_rate" in test_results
        
        # Should run multiple tests
        assert test_results["tests_run"] > 0
        
        # Should have a reasonable success rate
        assert test_results["success_rate"] >= 0


class TestIntegration:
    """Integration tests for complex workflows."""
    
    @pytest.mark.asyncio
    async def test_property_search_workflow(self, mock_ctx):
        """Test a complete property search workflow."""
        # Step 1: Get all property types
        all_types = await get_all_property_types(mock_ctx)
        assert all_types["success"] is True
        
        # Step 2: Search for apartments
        apartments = await search_property_types(mock_ctx, search_term="דירה")
        assert apartments["success"] is True
        
        # Step 3: Get details for first apartment type
        if apartments["exact_matches"]:
            first_code = list(apartments["exact_matches"].keys())[0]
            details = await get_property_type_details(mock_ctx, property_code=first_code)
            assert details["success"] is True
        
        # Step 4: Get recommendations
        recommendations = await get_property_type_recommendations(
            mock_ctx,
            budget=2000000,
            family_size=2
        )
        assert recommendations["success"] is True
    
    @pytest.mark.asyncio
    async def test_location_workflow(self, mock_ctx):
        """Test a complete location workflow."""
        # Step 1: Get all location codes
        all_locations = await get_location_codes(mock_ctx)
        assert all_locations["success"] is True
        
        # Step 2: Search for specific locations
        ramot_locations = await search_locations(mock_ctx, search_text="רמת")
        assert ramot_locations["success"] is True
    
    @pytest.mark.asyncio
    async def test_analysis_workflow(self, mock_ctx):
        """Test a complete analysis workflow."""
        # Step 1: Get trends
        trends = await get_property_type_trends(mock_ctx)
        assert trends["success"] is True
        
        # Step 2: Compare property types
        comparison = await compare_property_types(mock_ctx, type1="1", type2="5")
        assert comparison["success"] is True
        
        # Step 3: Get recommendations
        recommendations = await get_property_type_recommendations(
            mock_ctx,
            budget=5000000,
            investment=True
        )
        assert recommendations["success"] is True


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