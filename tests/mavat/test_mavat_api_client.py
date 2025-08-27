#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Mavat API client."""

import json
from unittest.mock import Mock

import pytest

from mavat.scrapers.mavat_api_client import MavatAPIClient, MavatLookupItem


class TestMavatLookupItem:
    """Test the MavatLookupItem dataclass."""

    def test_mavat_lookup_item_creation(self):
        """Test creating a MavatLookupItem instance."""
        item = MavatLookupItem(
            code="5000",
            description="תל אביב-יפו",
            raw={"CODE": "5000", "DESCRIPTION": "תל אביב-יפו"}
        )
        
        assert item.code == "5000"
        assert item.description == "תל אביב-יפו"
        assert item.raw == {"CODE": "5000", "DESCRIPTION": "תל אביב-יפו"}

    def test_mavat_lookup_item_defaults(self):
        """Test creating a MavatLookupItem with only required parameters."""
        item = MavatLookupItem(code="5000", description="Tel Aviv-Yafo")
        
        assert item.code == "5000"
        assert item.description == "Tel Aviv-Yafo"
        assert item.raw is None


class TestMavatAPIClient:
    """Test the MavatAPIClient class."""

    @pytest.fixture
    def api_client(self, mock_requests_session):
        """Create an API client with mocked session."""
        return MavatAPIClient(session=mock_requests_session)

    @pytest.fixture
    def sample_lookup_response(self):
        """Sample lookup table response from the API."""
        return [
            {
                "type": "4",
                "result": [
                    {"CODE": "5", "DESCRIPTION": "תל-אביב"},
                    {"CODE": "6", "DESCRIPTION": "חיפה"}
                ]
            },
            {
                "type": "5",
                "result": [
                    {"CODE": "5000", "DESCRIPTION": "תל אביב-יפו"},
                    {"CODE": "6000", "DESCRIPTION": "חיפה"}
                ]
            },
            {
                "type": "7",
                "result": [
                    {"CODE": "461", "DESCRIPTION": "הירקון"},
                    {"CODE": "462", "DESCRIPTION": "דיזנגוף"}
                ]
            }
        ]

    @pytest.fixture
    def sample_search_response(self):
        """Sample search response from the API."""
        return [
            {
                "type": "1",
                "result": {
                    "dtResults": [
                        {
                            "PLAN_ID": "12345",
                            "ENTITY_NAME": "Sample Plan",
                            "INTERNET_SHORT_STATUS": "Approved",
                            "AUTH_NAME": "Sample Authority",
                            "ENTITY_LOCATION": "Sample Location",
                            "ENTITY_NUMBER": "יוש/ 51/ 51",
                            "APP_DATE": "08/01/1992",
                            "INTERNET_STATUS_DATE": "08/01/1992"
                        }
                    ]
                }
            }
        ]

    def test_api_client_initialization(self, mock_requests_session):
        """Test API client initialization."""
        client = MavatAPIClient(session=mock_requests_session)
        
        assert client.session == mock_requests_session
        assert client.BASE_URL == "https://mavat.iplan.gov.il/rest/api"
        assert client.SEARCH_URL == "https://mavat.iplan.gov.il/rest/api/sv3/Search"
        assert client.LOOKUP_URL == "https://mavat.iplan.gov.il/rest/api/Luts/4-5-6-7-8-9-10-11-39-48-52-53"
        
        # Check that headers were updated
        mock_requests_session.headers.update.assert_called_once()

    def test_api_client_initialization_without_session(self):
        """Test API client initialization without providing session."""
        client = MavatAPIClient()
        
        assert client.session is not None
        assert hasattr(client.session, 'headers')
        assert client._lookup_cache == {}

    def test_get_lookup_tables_success(self, api_client, sample_lookup_response):
        """Test successful lookup table retrieval."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        # Call the method
        result = api_client.get_lookup_tables()
        
        # Verify the result
        assert "4" in result  # Districts
        assert "5" in result  # Cities
        assert "7" in result  # Streets
        
        assert len(result["4"]) == 2  # 2 districts
        assert len(result["5"]) == 2  # 2 cities
        assert len(result["7"]) == 2  # 2 streets
        
        # Check first district
        district = result["4"][0]
        assert district.code == "5"
        assert district.description == "תל-אביב"
        
        # Verify API call was made
        api_client.session.get.assert_called_once_with(
            api_client.LOOKUP_URL, timeout=30
        )

    def test_get_lookup_tables_caching(self, api_client, sample_lookup_response):
        """Test that lookup tables are cached."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        # First call - should make API request
        result1 = api_client.get_lookup_tables()
        
        # Second call - should use cache
        result2 = api_client.get_lookup_tables()
        
        # Results should be the same
        assert result1 == result2
        
        # API should only be called once
        api_client.session.get.assert_called_once()

    def test_get_lookup_tables_force_refresh(self, api_client, sample_lookup_response):
        """Test force refresh of lookup tables."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        # First call
        api_client.get_lookup_tables()
        
        # Second call with force refresh
        api_client.get_lookup_tables(force_refresh=True)
        
        # API should be called twice
        assert api_client.session.get.call_count == 2

    def test_get_lookup_tables_api_error(self, api_client):
        """Test lookup table retrieval with API error."""
        # Mock API error using the correct exception type
        from requests.exceptions import RequestException
        api_client.session.get.side_effect = RequestException("Network error")
        
        with pytest.raises(RuntimeError, match="Failed to fetch lookup tables"):
            api_client.get_lookup_tables()

    def test_get_lookup_tables_invalid_json(self, api_client):
        """Test lookup table retrieval with invalid JSON."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="Invalid JSON response"):
            api_client.get_lookup_tables()

    def test_get_lookup_tables_malformed_response(self, api_client):
        """Test lookup table retrieval with malformed response."""
        # Mock malformed response
        malformed_response = [
            {"type": "4", "result": "not a list"},  # result should be a list
            {"type": "5"},  # missing result
            {"result": [{"CODE": "5000"}]}  # missing type
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = malformed_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        # Should handle gracefully and return what it can
        result = api_client.get_lookup_tables()
        
        # Should only have valid entries
        assert len(result) == 0  # No valid entries in malformed response

    def test_get_districts(self, api_client, sample_lookup_response):
        """Test getting districts from lookup tables."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        districts = api_client.get_districts()
        
        assert len(districts) == 2
        assert districts[0].code == "5"
        assert districts[0].description == "תל-אביב"
        assert districts[1].code == "6"
        assert districts[1].description == "חיפה"

    def test_get_cities(self, api_client, sample_lookup_response):
        """Test getting cities from lookup tables."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        cities = api_client.get_cities()
        
        assert len(cities) == 2
        assert cities[0].code == "5000"
        assert cities[0].description == "תל אביב-יפו"
        assert cities[1].code == "6000"
        assert cities[1].description == "חיפה"

    def test_get_streets(self, api_client, sample_lookup_response):
        """Test getting streets from lookup tables."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        streets = api_client.get_streets()
        
        assert len(streets) == 2
        assert streets[0].code == "461"
        assert streets[0].description == "הירקון"
        assert streets[1].code == "462"
        assert streets[1].description == "דיזנגוף"

    def test_get_plan_areas(self, api_client, sample_lookup_response):
        """Test getting plan areas from lookup tables."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        # Add plan areas to the response
        sample_lookup_response.append({
            "type": "6",
            "result": [
                {"CODE": "507", "DESCRIPTION": "תל אביב-יפו"},
                {"CODE": "607", "DESCRIPTION": "חיפה"}
            ]
        })
        
        plan_areas = api_client.get_plan_areas()
        
        assert len(plan_areas) == 2
        assert plan_areas[0].code == "507"
        assert plan_areas[0].description == "תל אביב-יפו"

    def test_search_lookup_by_text(self, api_client, sample_lookup_response):
        """Test searching lookup tables by text."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        # Search for "תל" in all tables
        results = api_client.search_lookup_by_text("תל")
        
        assert len(results) == 2
        assert any("תל-אביב" in result.description for result in results)
        assert any("תל אביב-יפו" in result.description for result in results)

    def test_search_lookup_by_text_specific_table(self, api_client, sample_lookup_response):
        """Test searching lookup tables by text in specific table."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        # Search for "תל" only in cities table (type 5)
        results = api_client.search_lookup_by_text("תל", table_type="5")
        
        assert len(results) == 1
        assert "תל אביב-יפו" in results[0].description

    def test_search_lookup_by_text_no_matches(self, api_client, sample_lookup_response):
        """Test searching lookup tables with no matches."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        # Search for something that doesn't exist
        results = api_client.search_lookup_by_text("nonexistent")
        
        assert len(results) == 0

    def test_search_lookup_by_text_case_insensitive(self, api_client, sample_lookup_response):
        """Test that lookup search is case insensitive."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_lookup_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.get.return_value = mock_response
        
        # Search with different case
        results_lower = api_client.search_lookup_by_text("תל")
        results_upper = api_client.search_lookup_by_text("תל")
        
        assert len(results_lower) == len(results_upper)
        assert len(results_lower) == 2

    def test_search_plans_success(self, api_client, sample_search_response):
        """Test successful plan search."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        # Perform search
        results = api_client.search_plans(query="test", limit=10)
        
        assert len(results) == 1
        hit = results[0]
        
        assert hit.plan_id == "12345"
        assert hit.title == "Sample Plan"
        assert hit.status == "Approved"
        assert hit.authority == "Sample Authority"
        assert hit.jurisdiction == "Sample Location"
        assert hit.entity_number == "יוש/ 51/ 51"
        assert hit.approval_date == "08/01/1992"
        assert hit.status_date == "08/01/1992"
        
        # Verify API call was made
        call_args = api_client.session.post.call_args
        assert call_args[0][0] == api_client.SEARCH_URL  # URL
        assert call_args[1]['timeout'] == 30  # timeout
        
        # Verify key search parameters
        search_params = call_args[1]['json']
        assert search_params['searchEntity'] == 1
        assert search_params['plName'] == "test"
        assert search_params['fromResult'] == 1
        assert search_params['toResult'] == 10
        assert search_params['_page'] == 1

    def test_search_plans_with_location(self, api_client, sample_search_response):
        """Test plan search with location parameters."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        # Search with location parameters
        results = api_client.search_plans(
            city="תל אביב",
            district="תל-אביב",
            street="הירקון",
            limit=5
        )
        
        assert len(results) == 1
        
        # Verify search parameters were passed correctly
        call_args = api_client.session.post.call_args
        search_params = call_args[1]['json']
        
        assert search_params['modelCity']['DESCRIPTION'] == "תל אביב"
        assert search_params['intDistrict']['DESCRIPTION'] == "תל-אביב"
        assert search_params['intStreetCode']['DESCRIPTION'] == "הירקון"
        assert search_params['toResult'] == 5

    def test_search_plans_with_pagination(self, api_client, sample_search_response):
        """Test plan search with pagination."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        # Search with pagination
        results = api_client.search_plans(query="test", limit=5, page=2)
        
        assert len(results) == 1
        
        # Verify pagination parameters
        call_args = api_client.session.post.call_args
        search_params = call_args[1]['json']
        
        assert search_params['fromResult'] == 6  # (2-1) * 5 + 1
        assert search_params['toResult'] == 10  # 2 * 5
        assert search_params['_page'] == 2

    def test_search_plans_with_block_parcel(self, api_client, sample_search_response):
        """Test plan search with block and parcel numbers."""
        # Mock the session response
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        # Search with block/parcel
        results = api_client.search_plans(
            block_number="666",
            parcel_number="1",
            limit=10
        )
        
        assert len(results) == 1
        
        # Verify block/parcel parameters
        call_args = api_client.session.post.call_args
        search_params = call_args[1]['json']
        
        assert search_params['blockNumber'] == "666"
        assert search_params['toBlockNumber'] == "666"
        assert search_params['parcelNumber'] == "1"
        assert search_params['toParcelNumber'] == "1"

    def test_search_plans_empty_response(self, api_client):
        """Test plan search with empty response."""
        # Mock empty response
        empty_response = [{"type": "1", "result": {"dtResults": []}}]
        
        mock_response = Mock()
        mock_response.json.return_value = empty_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        # Search should return empty list
        results = api_client.search_plans(query="nonexistent")
        
        assert len(results) == 0

    def test_search_plans_malformed_response(self, api_client):
        """Test plan search with malformed response."""
        # Mock malformed response that the API client can handle
        malformed_response = [
            {"type": "1", "result": {}},  # missing dtResults
            {"type": "1", "result": {"dtResults": []}},  # empty dtResults
            {"type": "2", "result": {"dtResults": []}}  # wrong type
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = malformed_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        # Should handle gracefully and return empty list
        results = api_client.search_plans(query="test")
        
        assert len(results) == 0

    def test_search_plans_api_error(self, api_client):
        """Test plan search with API error."""
        # Mock API error using the correct exception type
        from requests.exceptions import RequestException
        api_client.session.post.side_effect = RequestException("Network error")
        
        with pytest.raises(RuntimeError, match="API request failed"):
            api_client.search_plans(query="test")

    def test_search_plans_invalid_json(self, api_client):
        """Test plan search with invalid JSON response."""
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="Invalid JSON response"):
            api_client.search_plans(query="test")

    def test_get_plan_details_success(self, api_client, sample_search_response):
        """Test successful plan details retrieval."""
        # Mock the search response
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        # Get plan details
        plan = api_client.get_plan_details("12345")
        
        assert plan.plan_id == "12345"
        assert plan.plan_name == "Sample Plan"
        assert plan.status == "Approved"
        assert plan.authority == "Sample Authority"
        assert plan.jurisdiction == "Sample Location"
        assert plan.entity_number == "יוש/ 51/ 51"
        assert plan.approval_date == "08/01/1992"
        assert plan.status_date == "08/01/1992"

    def test_get_plan_details_not_found(self, api_client):
        """Test plan details retrieval for non-existent plan."""
        # Mock empty search response
        mock_response = Mock()
        mock_response.json.return_value = [{"type": "1", "result": {"dtResults": []}}]
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        with pytest.raises(RuntimeError, match="Plan 12345 not found"):
            api_client.get_plan_details("12345")

    def test_get_plan_details_api_error(self, api_client):
        """Test plan details retrieval with API error."""
        # Mock API error
        api_client.session.post.side_effect = Exception("Network error")
        
        with pytest.raises(RuntimeError, match="Failed to get plan details"):
            api_client.get_plan_details("12345")

    def test_get_plan_attachments(self, api_client):
        """Test getting plan attachments."""
        attachments = api_client.get_plan_attachments("12345", "Sample Plan")
        
        assert len(attachments) == 1
        attachment = attachments[0]
        
        assert attachment.filename == "Sample Plan"
        assert "12345" in attachment.url
        assert "Sample%20Plan" in attachment.url

    def test_get_plan_attachments_with_special_characters(self, api_client):
        """Test getting plan attachments with special characters in name."""
        attachments = api_client.get_plan_attachments("12345", "תוכנית עם תווים מיוחדים")
        
        assert len(attachments) == 1
        attachment = attachments[0]
        
        assert attachment.filename == "תוכנית עם תווים מיוחדים"
        assert "12345" in attachment.url
        # Check that Hebrew characters are properly encoded
        assert "%D7%AA%D7%95%D7%9B%D7%A0%D7%99%D7%AA" in attachment.url

    def test_search_by_location(self, api_client, sample_search_response):
        """Test location-based search."""
        # Mock the search response
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        results = api_client.search_by_location(
            city="תל אביב",
            district="תל-אביב",
            street="הירקון"
        )
        
        assert len(results) == 1
        
        # Verify search parameters were passed correctly
        call_args = api_client.session.post.call_args
        search_params = call_args[1]['json']
        
        assert search_params['modelCity']['DESCRIPTION'] == "תל אביב"
        assert search_params['intDistrict']['DESCRIPTION'] == "תל-אביב"
        assert search_params['intStreetCode']['DESCRIPTION'] == "הירקון"

    def test_search_by_block_parcel(self, api_client, sample_search_response):
        """Test block/parcel search."""
        # Mock the search response
        mock_response = Mock()
        mock_response.json.return_value = sample_search_response
        mock_response.raise_for_status.return_value = None
        
        api_client.session.post.return_value = mock_response
        
        results = api_client.search_by_block_parcel("666", "1")
        
        assert len(results) == 1
        
        # Verify search parameters were passed correctly
        call_args = api_client.session.post.call_args
        search_params = call_args[1]['json']
        
        assert search_params['blockNumber'] == "666"
        assert search_params['toBlockNumber'] == "666"
        assert search_params['parcelNumber'] == "1"
        assert search_params['toParcelNumber'] == "1"

    def test_close_session(self, api_client):
        """Test closing the session."""
        api_client.close()
        
        # Verify session was closed
        api_client.session.close.assert_called_once()

    def test_close_session_no_session(self):
        """Test closing when no session exists."""
        client = MavatAPIClient()
        # Should not raise an error
        client.close()


class TestBackwardCompatibility:
    """Test backward compatibility with old class names."""

    def test_mavat_scraper_alias(self):
        """Test that MavatScraper is available as an alias."""
        from mavat.scrapers.mavat_api_client import MavatScraper

        # Should be the same class
        assert MavatScraper == MavatAPIClient
        
        # Should work the same way
        scraper = MavatScraper()
        assert isinstance(scraper, MavatAPIClient)


if __name__ == "__main__":
    pytest.main([__file__])
