"""
Tests for the NadlanDealsScraper module.
"""

import pytest
import responses
from unittest.mock import Mock, patch, MagicMock

from gov.nadlan_deals_scraper import (
    NadlanDealsScraper,
    DealRecord,
    NadlanAPIError,
    NadlanScrapingError
)


class TestDealRecord:
    """Test the DealRecord dataclass."""
    
    def test_deal_record_creation(self):
        """Test creating a DealRecord with all fields."""
        deal = DealRecord(
            asset_address="רחוב הרצל 1, תל אביב",
            deal_date="2024-01-15",
            price=1500000.0,
            rooms="3",
            floor="2",
            asset_type="דירה",
            building_year="1990",
            total_area=80.0
        )
        
        assert deal.asset_address == "רחוב הרצל 1, תל אביב"
        assert deal.price == 1500000.0
        assert deal.total_area == 80.0
    
    def test_from_dict(self):
        """Test creating DealRecord from dictionary."""
        data = {
            "AssetAddress": "רחוב הרצל 1, תל אביב",
            "DealDate": "2024-01-15",
            "Price": "1,500,000",
            "Rooms": "3",
            "Floor": "2",
            "AssetType": "דירה",
            "BuildingYear": "1990",
            "TotalArea": "80 מ²"
        }
        
        deal = DealRecord.from_dict(data)
        assert deal.asset_address == "רחוב הרצל 1, תל אביב"
        assert deal.price == 1500000.0
        assert deal.total_area == 80.0
        assert deal.raw_data == data
    
    def test_parse_price(self):
        """Test price parsing from various formats."""
        # Test with commas
        deal = DealRecord.from_dict({"Price": "1,500,000"})
        assert deal.price == 1500000.0
        
        # Test with shekel symbol
        deal = DealRecord.from_dict({"Price": "₪1,500,000"})
        assert deal.price == 1500000.0
        
        # Test with spaces
        deal = DealRecord.from_dict({"Price": "1 500 000"})
        assert deal.price == 1500000.0
        
        # Test with None
        deal = DealRecord.from_dict({"Price": None})
        assert deal.price is None
        
        # Test with invalid value
        deal = DealRecord.from_dict({"Price": "invalid"})
        assert deal.price is None
    
    def test_parse_area(self):
        """Test area parsing from various formats."""
        # Test with Hebrew square meter symbol
        deal = DealRecord.from_dict({"TotalArea": "80 מ²"})
        assert deal.total_area == 80.0
        
        # Test with commas (should be converted to decimal point)
        deal = DealRecord.from_dict({"TotalArea": "80,5"})
        assert deal.total_area == 80.5
        
        # Test with decimal point
        deal = DealRecord.from_dict({"TotalArea": "80.5"})
        assert deal.total_area == 80.5
        
        # Test with None
        deal = DealRecord.from_dict({"TotalArea": None})
        assert deal.total_area is None
        
        # Test with invalid value
        deal = DealRecord.from_dict({"TotalArea": "invalid"})
        assert deal.total_area is None
    
    def test_to_dict(self):
        """Test converting DealRecord back to dictionary."""
        deal = DealRecord(
            asset_address="רחוב הרצל 1, תל אביב",
            price=1500000.0,
            rooms="3"
        )
        
        result = deal.to_dict()
        assert result["asset_address"] == "רחוב הרצל 1, תל אביב"
        assert result["price"] == 1500000.0
        assert result["rooms"] == "3"
        assert result["raw_data"] is None


class TestNadlanDealsScraper:
    """Test the NadlanDealsScraper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = NadlanDealsScraper(timeout=5.0)
    
    def teardown_method(self):
        """Clean up after tests."""
        self.scraper.session.close()
    
    def test_init(self):
        """Test scraper initialization."""
        assert self.scraper.timeout == 5.0
        assert self.scraper.user_agent == "NadlanDealsScraper/1.0"
        assert "User-Agent" in self.scraper.session.headers
        assert "Accept" in self.scraper.session.headers
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with NadlanDealsScraper() as scraper:
            assert scraper.session is not None
        # Session should be closed after context exit
    
    @responses.activate
    def test_get_data_by_query_success(self):
        """Test successful query to GetDataByQuery endpoint."""
        mock_response = {
            "PageNo": 0,
            "Query": "שכונת רמת החייל",
            "Results": []
        }
        
        responses.add(
            responses.GET,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery",
            json=mock_response,
            status=200
        )
        
        result = self.scraper.get_data_by_query("שכונת רמת החייל")
        assert result == mock_response
    
    @responses.activate
    def test_get_data_by_query_http_error(self):
        """Test handling of HTTP errors in GetDataByQuery."""
        responses.add(
            responses.GET,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery",
            status=500,
            body="Internal Server Error"
        )
        
        with pytest.raises(NadlanAPIError, match="GetDataByQuery returned status 500"):
            self.scraper.get_data_by_query("שכונת רמת החייל")
    
    @responses.activate
    def test_get_data_by_query_connection_error(self):
        """Test handling of connection errors in GetDataByQuery."""
        responses.add(
            responses.GET,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery",
            body=Exception("Connection failed")
        )
        
        with pytest.raises(NadlanAPIError, match="Failed to connect"):
            self.scraper.get_data_by_query("שכונת רמת החייל")
    
    @responses.activate
    def test_get_assets_and_deals_success(self):
        """Test successful POST to GetAssestAndDeals endpoint."""
        mock_response = {
            "AssetsAndDeals": [
                {"AssetAddress": "רחוב הרצל 1", "Price": "1500000"}
            ]
        }
        
        responses.add(
            responses.POST,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetAssestAndDeals",
            json=mock_response,
            status=200
        )
        
        payload = {"PageNo": 0, "Query": "test"}
        result = self.scraper.get_assets_and_deals(payload)
        
        assert result == mock_response
        # Check that PageNo was set to 1
        assert payload["PageNo"] == 1
    
    @responses.activate
    def test_get_assets_and_deals_with_existing_pageno(self):
        """Test that existing PageNo is preserved."""
        mock_response = {"Results": []}
        
        responses.add(
            responses.POST,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetAssestAndDeals",
            json=mock_response,
            status=200
        )
        
        payload = {"PageNo": 5, "Query": "test"}
        self.scraper.get_assets_and_deals(payload)
        
        # PageNo should remain 5
        assert payload["PageNo"] == 5
    
    @responses.activate
    def test_get_deals_by_address_success(self):
        """Test successful retrieval of deals by address."""
        # Mock the first API call
        query_response = {"PageNo": 0, "Query": "שכונת רמת החייל"}
        responses.add(
            responses.GET,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery",
            json=query_response,
            status=200
        )
        
        # Mock the second API call
        deals_response = {
            "AssetsAndDeals": [
                {
                    "AssetAddress": "רחוב הרצל 1",
                    "DealDate": "2024-01-15",
                    "Price": "1,500,000",
                    "Rooms": "3"
                }
            ]
        }
        responses.add(
            responses.POST,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetAssestAndDeals",
            json=deals_response,
            status=200
        )
        
        deals = self.scraper.get_deals_by_address("שכונת רמת החייל")
        
        assert len(deals) == 1
        assert isinstance(deals[0], DealRecord)
        assert deals[0].asset_address == "רחוב הרצל 1"
        assert deals[0].price == 1500000.0
    
    @responses.activate
    def test_get_deals_by_address_no_deals_found(self):
        """Test handling when no deals are found in response."""
        query_response = {"PageNo": 0, "Query": "שכונת רמת החייל"}
        responses.add(
            responses.GET,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery",
            json=query_response,
            status=200
        )
        
        deals_response = {"NoDeals": True}
        responses.add(
            responses.POST,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetAssestAndDeals",
            json=deals_response,
            status=200
        )
        
        with pytest.raises(NadlanAPIError, match="Could not locate deals list"):
            self.scraper.get_deals_by_address("שכונת רמת החייל")
    
    @responses.activate
    def test_get_deals_by_neighborhood_id_success(self):
        """Test successful retrieval of deals by neighborhood ID."""
        # Mock the neighborhood page lookup
        neighborhood_html = """
        <html>
            <head>
                <title>שכונת רמת החייל, תל אביב - יפו - nadlan.gov.il</title>
            </head>
        </html>
        """
        responses.add(
            responses.GET,
            "https://www.nadlan.gov.il/?view=neighborhood&id=12345",
            body=neighborhood_html,
            status=200
        )
        
        # Mock the subsequent API calls
        query_response = {"PageNo": 0, "Query": "שכונת רמת החייל, תל אביב - יפו"}
        responses.add(
            responses.GET,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery",
            json=query_response,
            status=200
        )
        
        deals_response = {
            "AssetsAndDeals": [
                {
                    "AssetAddress": "רחוב הרצל 1",
                    "DealDate": "2024-01-15",
                    "Price": "1,500,000",
                    "Rooms": "3"
                }
            ]
        }
        responses.add(
            responses.POST,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetAssestAndDeals",
            json=deals_response,
            status=200
        )
        
        deals = self.scraper.get_deals_by_neighborhood_id("12345")
        assert len(deals) == 1
        assert deals[0].asset_address == "רחוב הרצל 1"
        assert deals[0].price == 1500000.0
    
    @responses.activate
    def test_get_deals_by_neighborhood_id_title_parsing(self):
        """Test parsing of neighborhood name from page title."""
        # Test with different title formats
        test_cases = [
            ("שכונת רמת החייל, תל אביב - יפו - nadlan.gov.il", "שכונת רמת החייל, תל אביב - יפו"),
            ("שכונת גבעת מרדכי, ירושלים", "שכונת גבעת מרדכי, ירושלים"),
            ("שכונה - תל אביב", "שכונה"),
        ]
        
        for title, expected in test_cases:
            neighborhood_html = f'<html><head><title>{title}</title></head></html>'
            
            responses.add(
                responses.GET,
                "https://www.nadlan.gov.il/?view=neighborhood&id=12345",
                body=neighborhood_html,
                status=200
            )
            
            # Mock the subsequent API calls
            query_response = {"PageNo": 0, "Query": expected}
            responses.add(
                responses.GET,
                "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery",
                json=query_response,
                status=200
            )
            
            deals_response = {
                "AssetsAndDeals": [
                    {
                        "AssetAddress": "רחוב הרצל 1",
                        "Price": "1,500,000"
                    }
                ]
            }
            responses.add(
                responses.POST,
                "https://www.nadlan.gov.il/Nadlan.REST/Main/GetAssestAndDeals",
                json=deals_response,
                status=200
            )
            
            deals = self.scraper.get_deals_by_neighborhood_id("12345")
            assert len(deals) == 1
            assert deals[0].asset_address == "רחוב הרצל 1"
    
    @responses.activate
    def test_get_deals_by_neighborhood_id_no_title(self):
        """Test handling when page has no title."""
        neighborhood_html = "<html><head></head></html>"
        responses.add(
            responses.GET,
            "https://www.nadlan.gov.il/?view=neighborhood&id=12345",
            body=neighborhood_html,
            status=200
        )
        
        with pytest.raises(NadlanAPIError, match="Could not determine neighbourhood name"):
            self.scraper.get_deals_by_neighborhood_id("12345")
    
    def test_scrape_deals_from_page(self):
        """Test HTML scraping functionality."""
        html_content = """
        <table>
            <thead>
                <tr>
                    <th>כתובת</th>
                    <th>מחיר</th>
                    <th>חדרים</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>רחוב הרצל 1</td>
                    <td>1,500,000</td>
                    <td>3</td>
                </tr>
                <tr>
                    <td>רחוב הרצל 2</td>
                    <td>1,600,000</td>
                    <td>4</td>
                </tr>
            </tbody>
        </table>
        """
        
        deals = self.scraper.scrape_deals_from_page(html_content)
        
        assert len(deals) == 2
        assert deals[0].asset_address == "רחוב הרצל 1"
        assert deals[0].price == 1500000.0
        assert deals[0].rooms == "3"
        assert deals[1].asset_address == "רחוב הרצל 2"
        assert deals[1].price == 1600000.0
        assert deals[1].rooms == "4"
    
    def test_scrape_deals_from_page_no_table(self):
        """Test scraping when no table is found."""
        html_content = "<html><body><p>No table here</p></body></html>"
        deals = self.scraper.scrape_deals_from_page(html_content)
        assert deals == []
    
    def test_scrape_deals_from_page_mismatched_cells(self):
        """Test scraping when row has different number of cells than headers."""
        html_content = """
        <table>
            <thead>
                <tr>
                    <th>כתובת</th>
                    <th>מחיר</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>רחוב הרצל 1</td>
                    <td>1,500,000</td>
                    <td>Extra cell</td>
                </tr>
            </tbody>
        </table>
        """
        
        deals = self.scraper.scrape_deals_from_page(html_content)
        assert deals == []
    
    def test_get_deals_with_fallback_api_failure(self):
        """Test fallback mechanism when API fails."""
        with patch.object(self.scraper, 'get_deals_by_address') as mock_get:
            mock_get.side_effect = NadlanAPIError("API failed")
            
            with pytest.raises(NadlanAPIError, match="API failed and HTML scraping not implemented"):
                self.scraper.get_deals_with_fallback("test query")


class TestLegacyFunctions:
    """Test legacy function compatibility."""
    
    @responses.activate
    def test_legacy_get_deals_by_address(self):
        """Test legacy get_deals_by_address function."""
        from gov.nadlan_deals_scraper import get_deals_by_address
        
        # Mock API responses
        query_response = {"PageNo": 0, "Query": "שכונת רמת החייל"}
        responses.add(
            responses.GET,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetDataByQuery",
            json=query_response,
            status=200
        )
        
        deals_response = {
            "AssetsAndDeals": [
                {
                    "AssetAddress": "רחוב הרצל 1",
                    "Price": "1,500,000"
                }
            ]
        }
        responses.add(
            responses.POST,
            "https://www.nadlan.gov.il/Nadlan.REST/Main/GetAssestAndDeals",
            json=deals_response,
            status=200
        )
        
        deals = get_deals_by_address("שכונת רמת החייל")
        assert len(deals) == 1
        assert deals[0]["asset_address"] == "רחוב הרצל 1"
        assert deals[0]["price"] == 1500000.0


if __name__ == "__main__":
    pytest.main([__file__])
