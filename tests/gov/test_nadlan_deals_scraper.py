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
        # raw field is excluded to prevent recursive nesting in cache
        assert "raw" not in result


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
    
    @patch('gov.nadlan.scraper_selenium.NadlanDealsScraper.get_deals_by_address')
    def test_get_deals_by_address_success(self, mock_get_deals):
        """Test successful retrieval of deals by address."""
        # Mock the deals
        mock_deals = [
            Deal(address="רחוב הרצל 1", deal_amount=1500000.0)
        ]
        
        mock_get_deals.return_value = mock_deals
        
        deals = self.scraper.get_deals_by_address("רמת החייל")
        
        assert len(deals) == 1
        assert deals[0].address == "רחוב הרצל 1"
        assert deals[0].deal_amount == 1500000.0
    
    @patch('gov.nadlan.scraper_selenium.NadlanDealsScraper.get_deals_by_address')
    def test_get_deals_by_address_no_search_results(self, mock_get_deals):
        """Test handling when no addresses are found."""
        mock_get_deals.return_value = []
        
        deals = self.scraper.get_deals_by_address("רמת החייל")
        
        assert len(deals) == 0
    
    @patch('gov.nadlan.scraper_selenium.NadlanDealsScraper.get_deals_by_address')
    def test_get_deals_by_address_no_neighborhood_id(self, mock_get_deals):
        """Test handling when neighborhood ID cannot be determined."""
        mock_get_deals.return_value = []
        
        deals = self.scraper.get_deals_by_address("רמת החייל")
        
        assert len(deals) == 0
    
    @patch('gov.nadlan.scraper_selenium.NadlanDealsScraper.get_neighborhood_info')
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
    



if __name__ == "__main__":
    pytest.main([__file__])
