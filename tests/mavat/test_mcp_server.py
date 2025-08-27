#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mavat MCP server."""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from fastmcp import Context

# Import the MCP server
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'mavat', 'mcp'))
from server import mcp, search_plans, get_plan_details, get_plan_documents, search_by_location, search_by_block_parcel, get_plan_summary


@pytest.fixture
def mock_context():
    """Create a mock context for testing."""
    context = Mock(spec=Context)
    context.info = AsyncMock()
    context.error = AsyncMock()
    context.warning = AsyncMock()
    return context


@pytest.fixture
def mock_mavat_api_client():
    """Create a mock MavatAPIClient."""
    client = Mock()
    client.search_plans = Mock()
    client.get_plan_details = Mock()
    client.get_plan_attachments = Mock()
    return client


@pytest.fixture
def sample_search_hit():
    """Create a sample MavatSearchHit."""
    from mavat.scrapers.mavat_api_client import MavatSearchHit
    return MavatSearchHit(
        plan_id="12345",
        title="Sample Plan",
        status="Approved",
        authority="Sample Authority",
        jurisdiction="Sample Jurisdiction",
        entity_number="יוש/ 51/ 51",
        entity_name="Sample Plan Name",
        approval_date="08/01/1992",
        status_date="08/01/1992",
        raw={"PLAN_ID": "12345", "ENTITY_NAME": "Sample Plan"}
    )


@pytest.fixture
def sample_plan():
    """Create a sample MavatPlan."""
    from mavat.scrapers.mavat_api_client import MavatPlan
    return MavatPlan(
        plan_id="12345",
        plan_name="Sample Plan",
        status="Approved",
        authority="Sample Authority",
        jurisdiction="Sample Jurisdiction",
        last_update="08/01/1992",
        entity_number="יוש/ 51/ 51",
        approval_date="08/01/1992",
        status_date="08/01/1992",
        raw={"PLAN_ID": "12345", "ENTITY_NAME": "Sample Plan"}
    )


@pytest.fixture
def sample_attachment():
    """Create a sample MavatAttachment."""
    from mavat.scrapers.mavat_api_client import MavatAttachment
    return MavatAttachment(
        filename="Sample Document.pdf",
        file_type="pdf",
        size=1024,
        url="https://example.com/doc.pdf",
        raw={"filename": "Sample Document.pdf"}
    )


class TestSearchPlans:
    """Test the search_plans function."""

    @pytest.mark.asyncio
    async def test_search_plans_success(self, mock_context, sample_search_hit):
        """Test successful plan search."""
        with patch('server.MavatAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.search_plans.return_value = [sample_search_hit]
            mock_client_class.return_value = mock_client
            
            result = await search_plans(mock_context, "test query", limit=10)
            
            assert result["success"] is True
            assert result["search_criteria"]["query"] == "test query"
            assert result["pagination"]["total_results"] == 1
            assert result["plans"][0]["plan_id"] == "12345"
            assert result["source"] == "mavat.iplan.gov.il REST API"
            
            mock_context.info.assert_called()
            mock_client.search_plans.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_plans_with_location(self, mock_context, sample_search_hit):
        """Test plan search with location parameters."""
        with patch('server.MavatAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.search_plans.return_value = [sample_search_hit]
            mock_client_class.return_value = mock_client
            
            result = await search_plans(
                mock_context, 
                city="תל אביב", 
                street="הירקון", 
                limit=5
            )
            
            assert result["success"] is True
            assert result["search_criteria"]["city"] == "תל אביב"
            assert result["search_criteria"]["street"] == "הירקון"
            mock_client.search_plans.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_plans_api_error(self, mock_context):
        """Test search with API error."""
        with patch('server.MavatAPIClient') as mock_client_class:
            mock_client_class.side_effect = Exception("API connection failed")
            
            result = await search_plans(mock_context, "test query")
            
            assert result["success"] is False
            assert result["error"] == "Search failed"
            mock_context.error.assert_called()


class TestGetPlanDetails:
    """Test the get_plan_details function."""

    @pytest.mark.asyncio
    async def test_get_plan_details_success(self, mock_context, sample_plan):
        """Test successful plan details retrieval."""
        with patch('server.MavatAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_plan_details.return_value = sample_plan
            mock_client_class.return_value = mock_client
            
            result = await get_plan_details(mock_context, "12345")
            
            assert result["success"] is True
            assert result["plan"]["plan_id"] == "12345"
            assert result["plan"]["plan_name"] == "Sample Plan"
            assert result["source"] == "mavat.iplan.gov.il REST API"
            
            mock_context.info.assert_called()
            mock_client.get_plan_details.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_plan_details_api_error(self, mock_context):
        """Test plan details with API error."""
        with patch('server.MavatAPIClient') as mock_client_class:
            mock_client_class.side_effect = Exception("API connection failed")
            
            result = await get_plan_details(mock_context, "12345")
            
            assert result["success"] is False
            assert result["error"] == "Failed to get plan details"
            mock_context.error.assert_called()


class TestGetPlanDocuments:
    """Test the get_plan_documents function."""

    @pytest.mark.asyncio
    async def test_get_plan_documents_success(self, mock_context, sample_attachment):
        """Test successful document retrieval."""
        with patch('server.MavatAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_plan_attachments.return_value = [sample_attachment]
            mock_client_class.return_value = mock_client
            
            # Mock get_plan_details to return entity name
            with patch('server.get_plan_details') as mock_get_details:
                mock_get_details.return_value = {
                    "success": True,
                    "plan": {"entity_name": "Sample Plan"}
                }
                
                result = await get_plan_documents(mock_context, "12345")
                
                assert result["success"] is True
                assert result["plan_id"] == "12345"
                assert result["documents_count"] == 1
                assert len(result["documents"]) == 1
                mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_plan_documents_with_entity_name(self, mock_context, sample_attachment):
        """Test document retrieval with provided entity name."""
        with patch('server.MavatAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.get_plan_attachments.return_value = [sample_attachment]
            mock_client_class.return_value = mock_client
            
            result = await get_plan_documents(mock_context, "12345", "Sample Plan")
            
            assert result["success"] is True
            assert result["entity_name"] == "Sample Plan"
            mock_client.get_plan_attachments.assert_called_once_with("12345", "Sample Plan")


class TestSearchByLocation:
    """Test the search_by_location function."""

    @pytest.mark.asyncio
    async def test_search_by_location_success(self, mock_context):
        """Test successful location-based search."""
        with patch('server.search_plans') as mock_search:
            mock_search.return_value = {
                "success": True,
                "plans": [{"plan_id": "12345"}],
                "source": "mavat.iplan.gov.il REST API"
            }
            
            result = await search_by_location(
                mock_context, 
                city="תל אביב", 
                street="הירקון"
            )
            
            assert result["success"] is True
            assert result["search_type"] == "location"
            assert result["location_criteria"]["city"] == "תל אביב"
            assert result["location_criteria"]["street"] == "הירקון"

    @pytest.mark.asyncio
    async def test_search_by_location_failure(self, mock_context):
        """Test location search failure."""
        with patch('server.search_plans') as mock_search:
            mock_search.side_effect = Exception("Search failed")
            
            result = await search_by_location(mock_context, city="תל אביב")
            
            assert result["success"] is False
            assert result["error"] == "Location search failed"


class TestSearchByBlockParcel:
    """Test the search_by_block_parcel function."""

    @pytest.mark.asyncio
    async def test_search_by_block_parcel_success(self, mock_context):
        """Test successful block/parcel search."""
        with patch('server.search_plans') as mock_search:
            mock_search.return_value = {
                "success": True,
                "plans": [{"plan_id": "12345"}],
                "source": "mavat.iplan.gov.il REST API"
            }
            
            result = await search_by_block_parcel(
                mock_context, 
                block_number="666", 
                parcel_number="1"
            )
            
            assert result["success"] is True
            assert result["search_type"] == "cadastral"
            assert result["cadastral_criteria"]["block_number"] == "666"
            assert result["cadastral_criteria"]["parcel_number"] == "1"

    @pytest.mark.asyncio
    async def test_search_by_block_parcel_failure(self, mock_context):
        """Test block/parcel search failure."""
        with patch('server.search_plans') as mock_search:
            mock_search.side_effect = Exception("Search failed")
            
            result = await search_by_block_parcel(
                mock_context, 
                block_number="666", 
                parcel_number="1"
            )
            
            assert result["success"] is False
            assert result["error"] == "Block/parcel search failed"


class TestGetPlanSummary:
    """Test the get_plan_summary function."""

    @pytest.mark.asyncio
    async def test_get_plan_summary_success(self, mock_context):
        """Test successful plan summary generation."""
        with patch('server.get_plan_details') as mock_get_details, \
             patch('server.get_plan_documents') as mock_get_docs:
            
            mock_get_details.return_value = {"success": True, "plan": {"id": "12345"}}
            mock_get_docs.return_value = {"success": True, "documents": [{"name": "doc1"}]}
            
            result = await get_plan_summary(mock_context, "12345")
            
            assert result["success"] is True
            assert result["plan_id"] == "12345"
            assert "summary" in result
            assert "details" in result["summary"]
            assert "documents" in result["summary"]
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_plan_summary_partial_failure(self, mock_context):
        """Test plan summary when some operations fail."""
        with patch('server.get_plan_details') as mock_get_details, \
             patch('server.get_plan_documents') as mock_get_docs:
            
            mock_get_details.return_value = {"success": True, "plan": {"id": "12345"}}
            mock_get_docs.return_value = {"success": False, "error": "Failed"}
            
            result = await get_plan_summary(mock_context, "12345")
            
            assert result["success"] is False
            assert result["error"] == "Failed to retrieve complete plan information"


class TestMCPTools:
    """Test that all MCP tools are properly registered."""

    def test_tools_registered(self):
        """Test that all expected tools are registered with the MCP server."""
        tool_names = [tool.name for tool in mcp.tools]
        expected_tools = [
            "search_plans",
            "get_plan_details", 
            "get_plan_documents",
            "search_by_location",
            "search_by_block_parcel",
            "get_plan_summary"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tool_names, f"Tool {tool_name} not found in registered tools"

    def test_server_metadata(self):
        """Test MCP server metadata."""
        assert mcp.name == "MavatPlanning"
        assert "requests" in mcp.dependencies


if __name__ == "__main__":
    pytest.main([__file__])

