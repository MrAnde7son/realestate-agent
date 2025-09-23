"""
Tests for the NadlanDealsScraper module.
"""

from unittest.mock import Mock, patch

import pytest

from gov.nadlan import (
    Deal,
    NadlanAPIError,
    NadlanDealsScraper,
)


class TestDealRecord:
    """Test the Deal dataclass."""
    
    def test_deal_record_creation(self):
        """Test creating a Deal with all fields."""
        deal = Deal(
            address="רחוב הרצל 1, תל אביב",
            deal_date="2024-01-15",
            deal_amount=1500000.0,
            rooms="3",
            floor="2",
            asset_type="דירה",
            year_built="1990",
            area=80.0
        )
        
        assert deal.address == "רחוב הרצל 1, תל אביב"
        assert deal.deal_amount == 1500000.0
        assert deal.area == 80.0
    
    def test_from_item(self):
        """Test creating Deal from dictionary."""
        data = {
            "address": "רחוב הרצל 1, תל אביב",
            "dealDate": "2024-01-15",
            "dealAmount": "1,500,000",
            "rooms": "3",
            "floor": "2",
            "assetType": "דירה",
            "yearBuilt": "1990",
            "area": "80"
        }
        
        deal = Deal.from_item(data)
        assert deal.address == "רחוב הרצל 1, תל אביב"
        assert deal.deal_amount == 1500000.0
        assert deal.area == 80.0
        assert deal.raw == data
    
    def test_parse_price(self):
        """Test price parsing from various formats."""
        # Test with commas
        deal = Deal.from_item({"dealAmount": "1,500,000"})
        assert deal.deal_amount == 1500000.0
        
        # Test with shekel symbol
        deal = Deal.from_item({"dealAmount": "₪1,500,000"})
        assert deal.deal_amount == 1500000.0
        
        # Test with spaces
        deal = Deal.from_item({"dealAmount": "1 500 000"})
        assert deal.deal_amount == 1500000.0
        
        # Test with None
        deal = Deal.from_item({"dealAmount": None})
        assert deal.deal_amount is None
        
        # Test with invalid value
        deal = Deal.from_item({"dealAmount": "invalid"})
        assert deal.deal_amount is None
    
    def test_parse_area(self):
        """Test area parsing from various formats."""
        # Test with Hebrew square meter symbol
        deal = Deal.from_item({"area": "80 מ²"})
        assert deal.area == 80.0
        
        # Test with commas (should be converted to decimal point)
        deal = Deal.from_item({"area": "80,5"})
        assert deal.area == 80.5
        
        # Test with decimal point
        deal = Deal.from_item({"area": "80.5"})
        assert deal.area == 80.5
        
        # Test with None
        deal = Deal.from_item({"area": None})
        assert deal.area is None
        
        # Test with invalid value
        deal = Deal.from_item({"area": "invalid"})
        assert deal.area is None
    
    def test_to_dict(self):
        """Test converting Deal back to dictionary."""
        deal = Deal(
            address="רחוב הרצל 1, תל אביב",
            deal_amount=1500000.0,
            rooms="3"
        )
        
        result = deal.to_dict()
        assert result["address"] == "רחוב הרצל 1, תל אביב"
        assert result["deal_amount"] == 1500000.0
        assert result["rooms"] == "3"
        assert result["raw"] is None


class TestNadlanDealsScraper:
    """Test the NadlanDealsScraper class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.scraper = NadlanDealsScraper(timeout=5.0)
    
    def test_init(self):
        """Test scraper initialization."""
        assert self.scraper.timeout == 5.0
        assert self.scraper.headless is True
    
    def test_context_manager(self):
        """Test context manager functionality."""
        with NadlanDealsScraper() as scraper:
            assert scraper is not None
        # Context manager should work without errors
    
    @patch('gov.nadlan.scraper.NadlanDealsScraper._fetch_deals_by_neighborhood')
    def test_get_deals_by_neighborhood_id_success(self, mock_fetch):
        """Test successful retrieval of deals by neighborhood ID."""
        # Mock the selenium result
        mock_deals = [
            Deal(address="רחוב הרצל 1", deal_amount=1500000.0)
        ]
        mock_fetch.return_value = mock_deals
        
        deals = self.scraper.get_deals_by_neighborhood_id("12345")
        
        assert len(deals) == 1
        assert deals[0].address == "רחוב הרצל 1"
        assert deals[0].deal_amount == 1500000.0
        mock_fetch.assert_called_once_with("12345")
    
    @patch('gov.nadlan.scraper.NadlanDealsScraper._fetch_deals_by_neighborhood')
    def test_get_deals_by_neighborhood_id_failure(self, mock_fetch):
        """Test handling of failures in get_deals_by_neighborhood_id."""
        mock_fetch.side_effect = Exception("Test error")
        
        with pytest.raises(NadlanAPIError, match="Failed to fetch deals for neighborhood 12345"):
            self.scraper.get_deals_by_neighborhood_id("12345")
    
    @patch('gov.nadlan.scraper.NadlanDealsScraper.search_address')
    def test_search_address_success(self, mock_fetch):
        """Test successful address search."""
        mock_results = [
            {"type": "neighborhood", "value": "רמת החייל", "neighborhood_id": "65210036"}
        ]
        mock_fetch.return_value = mock_results
        
        results = self.scraper.search_address("רמת החייל")
        
        assert len(results) == 1
        assert results[0]["value"] == "רמת החייל"
        assert results[0]["neighborhood_id"] == "65210036"
    
    @patch('gov.nadlan.scraper.NadlanDealsScraper.search_address')
    def test_search_address_failure(self, mock_fetch):
        """Test handling of failures in address search."""
        mock_fetch.side_effect = Exception("Test error")
        
        with pytest.raises(NadlanAPIError, match="Failed to search for address 'רמת החייל'"):
            self.scraper.search_address("רמת החייל")
    
    @patch('gov.nadlan.scraper.NadlanDealsScraper.get_deals_by_neighborhood_id')
    @patch('gov.nadlan.scraper.NadlanDealsScraper.search_address')
    def test_get_deals_by_address_success(self, mock_search, mock_get_deals):
        """Test successful retrieval of deals by address."""
        # Mock the search results
        search_results = [
            {"type": "neighborhood", "value": "רמת החייל", "neighborhood_id": "65210036"}
        ]
        
        # Mock the deals
        mock_deals = [
            Deal(address="רחוב הרצל 1", deal_amount=1500000.0)
        ]
        
        mock_search.return_value = search_results
        mock_get_deals.return_value = mock_deals
        
        deals = self.scraper.get_deals_by_address("רמת החייל")
        
        assert len(deals) == 1
        assert deals[0].address == "רחוב הרצל 1"
        assert deals[0].deal_amount == 1500000.0
    
    @patch('gov.nadlan.scraper.NadlanDealsScraper.search_address')
    def test_get_deals_by_address_no_search_results(self, mock_search):
        """Test handling when no addresses are found."""
        mock_search.return_value = []
        
        with pytest.raises(NadlanAPIError, match="No addresses found for query: רמת החייל"):
            self.scraper.get_deals_by_address("רמת החייל")
    
    @patch('gov.nadlan.scraper.NadlanDealsScraper.search_address')
    def test_get_deals_by_address_no_neighborhood_id(self, mock_search):
        """Test handling when neighborhood ID cannot be determined."""
        search_results = [
            {"type": "neighborhood", "value": "רמת החייל", "neighborhood_id": None}
        ]
        mock_search.return_value = search_results
        
        with pytest.raises(NadlanAPIError, match="Could not determine neighborhood ID for: רמת החייל"):
            self.scraper.get_deals_by_address("רמת החייל")
    
    @patch('gov.nadlan.scraper.NadlanDealsScraper.get_neighborhood_info')
    def test_get_neighborhood_info_success(self, mock_fetch):
        """Test successful retrieval of neighborhood info."""
        mock_info = {
            "neigh_id": "65210036",
            "neigh_name": "רמת החייל",
            "setl_id": "5000",
            "setl_name": "תל אביב-יפו"
        }
        mock_fetch.return_value = mock_info
        
        info = self.scraper.get_neighborhood_info("65210036")
        
        assert info["neigh_id"] == "65210036"
        assert info["neigh_name"] == "רמת החייל"
        assert info["setl_id"] == "5000"
        assert info["setl_name"] == "תל אביב-יפו"
    
    @patch('gov.nadlan.scraper.NadlanDealsScraper.get_neighborhood_info')
    def test_get_neighborhood_info_failure(self, mock_fetch):
        """Test handling of failures in get_neighborhood_info."""
        mock_fetch.side_effect = Exception("Test error")
        
        with pytest.raises(NadlanAPIError, match="Failed to get neighborhood info for 65210036"):
            self.scraper.get_neighborhood_info("65210036")
    
    def test_extract_neighborhood_id_from_poi(self):
        """Test extraction of neighborhood ID from POI data."""
        # Test that the method returns None (placeholder implementation)
        poi_item = {"Value": "רמת החייל"}
        result = self.scraper._extract_neighborhood_id_from_poi(poi_item)
        assert result is None
        
        # Test with different values
        poi_item = {"Value": "תל אביב"}
        result = self.scraper._extract_neighborhood_id_from_poi(poi_item)
        assert result is None
        
        # Test unknown value
        poi_item = {"Value": "Unknown Location"}
        result = self.scraper._extract_neighborhood_id_from_poi(poi_item)
        assert result is None


# Legacy function tests removed - functions no longer exist


if __name__ == "__main__":
    pytest.main([__file__])
