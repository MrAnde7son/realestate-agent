#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mavat MCP server."""

# Import the MCP server
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastmcp import Context

from mavat.mcp_server import (
    get_plan_details,
    get_plan_documents,
    search_plans,
)

# Extract the underlying functions from the FastMCP tools
search_plans_func = search_plans.fn
get_plan_details_func = get_plan_details.fn
get_plan_documents_func = get_plan_documents.fn


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
    from mavat.mavat_api_client import MavatSearchHit

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
        raw={"PLAN_ID": "12345", "ENTITY_NAME": "Sample Plan"},
    )


@pytest.fixture
def sample_plan():
    """Create a sample MavatPlan."""
    from mavat.mavat_api_client import MavatPlan

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
        raw={"PLAN_ID": "12345", "ENTITY_NAME": "Sample Plan"},
    )


@pytest.fixture
def sample_attachment():
    """Create a sample MavatAttachment."""
    from mavat.mavat_api_client import MavatAttachment

    return MavatAttachment(
        filename="Sample Document.pdf",
        file_type="pdf",
        size=1024,
        url="https://example.com/doc.pdf",
        raw={"filename": "Sample Document.pdf"},
    )


class TestSearchPlans:
    """Test the search_plans function."""

    @pytest.mark.asyncio
    async def test_search_plans_success(self, mock_context, sample_search_hit):
        """Test successful plan search."""
        with patch("mavat.mcp_server.MavatAPIClient") as mock_client_class:
            mock_client = Mock()
            mock_client.search_plans.return_value = [sample_search_hit]
            mock_client_class.return_value = mock_client

            result = await search_plans_func(mock_context, "test query", limit=10)

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
        with patch("mavat.mcp_server.MavatAPIClient") as mock_client_class:
            mock_client = Mock()
            mock_client.search_plans.return_value = [sample_search_hit]
            mock_client_class.return_value = mock_client

            result = await search_plans_func(
                mock_context, city="תל אביב", street="הירקון", limit=5
            )

            assert result["success"] is True
            assert result["search_criteria"]["city"] == "תל אביב"
            assert result["search_criteria"]["street"] == "הירקון"
            mock_client.search_plans.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_plans_api_error(self, mock_context):
        """Test search with API error."""
        with patch("mavat.mcp_server.MavatAPIClient") as mock_client_class:
            mock_client_class.side_effect = Exception("API connection failed")

            result = await search_plans_func(mock_context, "test query")

            assert result["success"] is False
            assert result["error"] == "Search failed"
            mock_context.error.assert_called()


class TestGetPlanDetails:
    """Test the get_plan_details function."""

    @pytest.mark.asyncio
    async def test_get_plan_details_success(self, mock_context, sample_plan):
        """Test successful plan details retrieval."""
        with (
            patch("mavat.mcp_server.MavatAPIClient") as mock_client_class,
            patch("mavat.mcp_server._current_client", None),
        ):
            mock_client = Mock()
            mock_client.get_plan_details.return_value = sample_plan
            mock_client_class.return_value = mock_client

            result = await get_plan_details_func(mock_context, "12345")

            assert result["success"] is True
            assert result["plan"]["plan_id"] == "12345"
            assert result["plan"]["plan_name"] == "Sample Plan"
            assert result["source"] == "mavat.iplan.gov.il REST API"

            mock_context.info.assert_called()
            mock_client.get_plan_details.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_plan_details_api_error(self, mock_context):
        """Test plan details with API error."""
        with (
            patch("mavat.mcp_server.MavatAPIClient") as mock_client_class,
            patch("mavat.mcp_server._current_client", None),
        ):
            mock_client_class.side_effect = Exception("API connection failed")

            result = await get_plan_details_func(mock_context, "12345")

            assert result["success"] is False
            assert result["error"] == "Failed to get plan details"
            mock_context.error.assert_called()


class TestGetPlanDocuments:
    """Test the get_plan_documents function."""

    @pytest.mark.asyncio
    async def test_get_plan_documents_success(self, mock_context, sample_attachment):
        """Test successful document retrieval."""
        with patch("mavat.mcp_server.MavatAPIClient") as mock_client_class:
            mock_client = Mock()
            mock_client.get_plan_attachments.return_value = [sample_attachment]
            mock_client_class.return_value = mock_client

            # Provide entity_name directly to avoid calling get_plan_details
            result = await get_plan_documents_func(mock_context, "12345", "Sample Plan")

            assert result["success"] is True
            assert result["plan_id"] == "12345"
            assert result["documents_count"] == 1
            assert len(result["documents"]) == 1
            mock_context.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_plan_documents_with_entity_name(
        self, mock_context, sample_attachment
    ):
        """Test document retrieval with provided entity name."""
        with patch("mavat.mcp_server.MavatAPIClient") as mock_client_class:
            mock_client = Mock()
            mock_client.get_plan_attachments.return_value = [sample_attachment]
            mock_client_class.return_value = mock_client

            result = await get_plan_documents_func(mock_context, "12345", "Sample Plan")

            assert result["success"] is True
            assert result["entity_name"] == "Sample Plan"
            mock_client.get_plan_attachments.assert_called_once_with(
                "12345", "Sample Plan"
            )


if __name__ == "__main__":
    pytest.main([__file__])
