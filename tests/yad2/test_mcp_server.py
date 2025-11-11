#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for Yad2 MCP Server

Test suite for the enhanced Yad2 MCP server functionality.
"""

import asyncio
import os
import sys

import pytest
from unittest.mock import Mock, patch

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import MCP server functions
from yad2.mcp_server import (
    get_all_property_types,
    get_search_parameters_reference,
    fetch_listings,
    fetch_contact_info,
    fetch_project_autocomplete,
    fetch_location_autocomplete,
    fetch_latest_deals,
)

# Extract the underlying functions from the FastMCP tools
get_all_property_types_func = get_all_property_types.fn
get_search_parameters_reference_func = get_search_parameters_reference.fn
fetch_listings_func = fetch_listings.fn
fetch_contact_info_func = fetch_contact_info.fn
fetch_project_autocomplete_func = fetch_project_autocomplete.fn
fetch_location_autocomplete_func = fetch_location_autocomplete.fn
fetch_latest_deals_func = fetch_latest_deals.fn

# Mock context for testing
class MockContext:
    """Mock MCP context for testing."""
    
    async def info(self, message):
        print(f"INFO: {message}")
    
    async def error(self, message):
        print(f"ERROR: {message}")
    
    async def warning(self, message):
        print(f"WARNING: {message}")


@pytest.fixture
def mock_ctx():
    """Provide mock context for tests."""
    return MockContext()


@pytest.fixture
def mock_listing():
    """Create a mock RealEstateListing object."""
    listing = Mock()
    listing.title = "Test Apartment"
    listing.price = 2000000
    listing.address = "Test Street 1, Tel Aviv"
    listing.rooms = 3
    listing.size = 80
    listing.floor = 5
    listing.property_type = "דירה"
    listing.url = "https://yad2.co.il/item/test123"
    listing.listing_id = "test123"
    listing.contact_info = None
    return listing


@pytest.fixture
def mock_contact_info():
    """Create a mock ContactInfo object."""
    contact = Mock()
    contact.to_dict = Mock(return_value={
        "name": "Test Broker",
        "phone": "050-1234567",
        "agencyName": "Test Agency"
    })
    return contact


@pytest.fixture
def mock_deal():
    """Create a mock deal object."""
    deal = Mock()
    deal.title = "Test Deal"
    deal.price = 1800000
    deal.address = "Test Street 1, Tel Aviv"
    deal.rooms = 3
    deal.size = 80
    deal.floor = 5
    deal.property_type = "דירה"
    deal.date_posted = "2024-01-01"
    deal.recent_deal = True
    return deal


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
    
class TestFetchListings:
    """Test fetch_listings functionality."""
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_listings_success(self, mock_api_client, mock_ctx, mock_listing):
        """Test successful fetch_listings call."""
        # Setup mock
        mock_api_client.fetch_listings.return_value = [mock_listing]
        
        # Call function
        result = await fetch_listings_func(
            mock_ctx,
            city="5000",
            property="1",
            listing_type="sale"
        )
        
        # Verify results
        assert result["success"] is True
        assert result["total_listings"] == 1
        assert "listings_preview" in result
        assert "parameters" in result
        assert len(result["listings_preview"]) == 1
        assert result["listings_preview"][0]["title"] == "Test Apartment"
        assert result["listings_preview"][0]["price"] == 2000000
        
        # Verify API was called correctly
        mock_api_client.fetch_listings.assert_called_once()
        call_kwargs = mock_api_client.fetch_listings.call_args[1]
        assert call_kwargs["listing_type"] == "sale"
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_listings_no_results(self, mock_api_client, mock_ctx):
        """Test fetch_listings with no results."""
        # Setup mock
        mock_api_client.fetch_listings.return_value = []
        
        # Call function
        result = await fetch_listings_func(
            mock_ctx,
            city="5000"
        )
        
        # Verify results
        assert result["success"] is False
        assert "message" in result
        assert "No listings found" in result["message"]
        assert "parameters" in result
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_listings_with_hebrew_property(self, mock_api_client, mock_ctx, mock_listing):
        """Test fetch_listings with Hebrew property name."""
        # Setup mock
        mock_api_client.fetch_listings.return_value = [mock_listing]
        
        # Call function with Hebrew property name
        result = await fetch_listings_func(
            mock_ctx,
            property="דירה",
            city="5000"
        )
        
        # Verify results
        assert result["success"] is True
        assert result["total_listings"] == 1
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_listings_error(self, mock_api_client, mock_ctx):
        """Test fetch_listings error handling."""
        # Setup mock to raise exception
        mock_api_client.fetch_listings.side_effect = Exception("API Error")
        
        # Call function
        result = await fetch_listings_func(
            mock_ctx,
            city="5000"
        )
        
        # Verify error handling
        assert result["success"] is False
        assert "error" in result
        assert "API Error" in result["error"]


class TestFetchContactInfo:
    """Test fetch_contact_info functionality."""
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_contact_info_success(self, mock_api_client, mock_ctx, mock_contact_info):
        """Test successful fetch_contact_info call."""
        # Setup mock
        mock_api_client.fetch_contact_info.return_value = mock_contact_info
        
        # Call function
        result = await fetch_contact_info_func(mock_ctx, token="test123")
        
        # Verify results
        assert result["success"] is True
        assert "contact" in result
        assert result["contact"]["name"] == "Test Broker"
        assert result["contact"]["phone"] == "050-1234567"
        
        # Verify API was called correctly
        mock_api_client.fetch_contact_info.assert_called_once_with("test123")
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_contact_info_not_found(self, mock_api_client, mock_ctx):
        """Test fetch_contact_info when contact not found."""
        # Setup mock
        mock_api_client.fetch_contact_info.return_value = None
        
        # Call function
        result = await fetch_contact_info_func(mock_ctx, token="test123")
        
        # Verify results
        assert result["success"] is False
        assert "message" in result
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_contact_info_error(self, mock_api_client, mock_ctx):
        """Test fetch_contact_info error handling."""
        # Setup mock to raise exception
        mock_api_client.fetch_contact_info.side_effect = Exception("API Error")
        
        # Call function
        result = await fetch_contact_info_func(mock_ctx, token="test123")
        
        # Verify error handling
        assert result["success"] is False
        assert "error" in result


class TestFetchProjectAutocomplete:
    """Test fetch_project_autocomplete functionality."""
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_project_autocomplete_success(self, mock_api_client, mock_ctx):
        """Test successful fetch_project_autocomplete call."""
        # Setup mock
        mock_project = {"id": "123", "name": "Test Project"}
        mock_api_client.fetch_project_autocomplete.return_value = mock_project
        
        # Call function
        result = await fetch_project_autocomplete_func(mock_ctx, phrase="Test Project")
        
        # Verify results
        assert result["success"] is True
        assert "project" in result
        assert result["project"]["name"] == "Test Project"
        
        # Verify API was called correctly
        mock_api_client.fetch_project_autocomplete.assert_called_once_with("Test Project")
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_project_autocomplete_not_found(self, mock_api_client, mock_ctx):
        """Test fetch_project_autocomplete when project not found."""
        # Setup mock
        mock_api_client.fetch_project_autocomplete.return_value = None
        
        # Call function
        result = await fetch_project_autocomplete_func(mock_ctx, phrase="Nonexistent")
        
        # Verify results
        assert result["success"] is False
        assert "message" in result
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_project_autocomplete_error(self, mock_api_client, mock_ctx):
        """Test fetch_project_autocomplete error handling."""
        # Setup mock to raise exception
        mock_api_client.fetch_project_autocomplete.side_effect = Exception("API Error")
        
        # Call function
        result = await fetch_project_autocomplete_func(mock_ctx, phrase="Test")
        
        # Verify error handling
        assert result["success"] is False
        assert "error" in result


class TestFetchLocationAutocomplete:
    """Test fetch_location_autocomplete functionality."""
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_location_autocomplete_success(self, mock_api_client, mock_ctx):
        """Test successful fetch_location_autocomplete call."""
        # Setup mock
        from yad2.core import Yad2SearchParameters
        mock_params = Yad2SearchParameters()
        mock_params.set_parameter("city", 5000)
        mock_params.set_parameter("neighborhood", 203)
        mock_params.get_active_parameters = Mock(return_value={"city": 5000, "neighborhood": 203})
        mock_api_client.fetch_location_autocomplete.return_value = mock_params
        
        # Call function
        result = await fetch_location_autocomplete_func(mock_ctx, search_text="רמת החייל")
        
        # Verify results
        assert result["success"] is True
        assert "search_text" in result
        assert result["search_text"] == "רמת החייל"
        assert "search_parameters" in result
        assert result["search_parameters"]["city"] == 5000
        
        # Verify API was called correctly
        mock_api_client.fetch_location_autocomplete.assert_called_once_with("רמת החייל")
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_location_autocomplete_not_found(self, mock_api_client, mock_ctx):
        """Test fetch_location_autocomplete when location not found."""
        # Setup mock
        mock_api_client.fetch_location_autocomplete.return_value = None
        
        # Call function
        result = await fetch_location_autocomplete_func(mock_ctx, search_text="Nonexistent Location")
        
        # Verify results
        assert result["success"] is False
        assert "message" in result
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_location_autocomplete_error(self, mock_api_client, mock_ctx):
        """Test fetch_location_autocomplete error handling."""
        # Setup mock to raise exception
        mock_api_client.fetch_location_autocomplete.side_effect = Exception("API Error")
        
        # Call function
        result = await fetch_location_autocomplete_func(mock_ctx, search_text="Test")
        
        # Verify error handling
        assert result["success"] is False
        assert "error" in result


class TestFetchLatestDeals:
    """Test fetch_latest_deals functionality."""
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_latest_deals_success(self, mock_api_client, mock_ctx, mock_deal):
        """Test successful fetch_latest_deals call."""
        # Setup mock
        mock_api_client.fetch_latest_deals.return_value = [mock_deal]
        
        # Call function
        result = await fetch_latest_deals_func(
            mock_ctx,
            city=5000,
            limit=10
        )
        
        # Verify results
        assert result["success"] is True
        assert "total_deals" in result
        assert result["total_deals"] == 1
        assert "deals_preview" in result
        assert len(result["deals_preview"]) == 1
        assert result["deals_preview"][0]["title"] == "Test Deal"
        
        # Verify API was called correctly
        mock_api_client.fetch_latest_deals.assert_called_once()
        call_kwargs = mock_api_client.fetch_latest_deals.call_args[1]
        assert call_kwargs["city"] == 5000
        assert call_kwargs["limit"] == 10
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_latest_deals_no_results(self, mock_api_client, mock_ctx):
        """Test fetch_latest_deals with no results."""
        # Setup mock
        mock_api_client.fetch_latest_deals.return_value = []
        
        # Call function
        result = await fetch_latest_deals_func(mock_ctx, city=5000)
        
        # Verify results
        assert result["success"] is False
        assert "message" in result
        assert "No deals found" in result["message"]
    
    @pytest.mark.asyncio
    @patch('yad2.mcp_server._api_client')
    async def test_fetch_latest_deals_error(self, mock_api_client, mock_ctx):
        """Test fetch_latest_deals error handling."""
        # Setup mock to raise exception
        mock_api_client.fetch_latest_deals.side_effect = Exception("API Error")
        
        # Call function
        result = await fetch_latest_deals_func(mock_ctx, city=5000)
        
        # Verify error handling
        assert result["success"] is False
        assert "error" in result


def test_mock_context():
    """Test that our mock context works correctly."""
    ctx = MockContext()
    
    # Test that we can call the async methods
    async def test_async():
        await ctx.info("Test message")
        await ctx.error("Test error")
        await ctx.warning("Test warning")
    
    asyncio.run(test_async())


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
