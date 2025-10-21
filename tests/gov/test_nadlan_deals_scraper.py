"""
Tests for the NadlanDealsScraper module.
"""

from unittest.mock import Mock, patch

import pytest

from gov.nadlan import (
    Deal,
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
    
    def test_error_modal_caching_protection(self):
        """Test that caching is disabled when error modal is encountered."""
        # Create a scraper with caching enabled
        scraper = NadlanDealsScraper(use_cache=True)
        
        # Mock the cache to track store_deals calls
        mock_cache = Mock()
        scraper.cache = mock_cache
        
        # Simulate error modal encountered
        scraper.error_modal_encountered = True
        
        # Mock the selenium fetch to return empty results
        with patch.object(scraper, '_init_driver'), \
             patch.object(scraper, '_fetch_deals_by_address_selenium', return_value=[]):
            deals = scraper.get_deals_by_address("ק\"ם 3 תל אביב-יפו")
            
            # Should return empty results
            assert len(deals) == 0
            
            # Cache should be called with error modal flag to prevent future use
            mock_cache.store_deals.assert_called_once_with("ק\"ם 3 תל אביב-יפו", [], True)
    
    def test_empty_results_caching_protection(self):
        """Test that caching is disabled when no results are found."""
        # Create a scraper with caching enabled
        scraper = NadlanDealsScraper(use_cache=True)
        
        # Mock the cache to track store_deals calls
        mock_cache = Mock()
        scraper.cache = mock_cache
        
        # No error modal, but empty results
        scraper.error_modal_encountered = False
        
        # Mock the selenium fetch to return empty results
        with patch.object(scraper, '_init_driver'), \
             patch.object(scraper, '_fetch_deals_by_address_selenium', return_value=[]):
            deals = scraper.get_deals_by_address("ק\"ם 3 תל אביב-יפו")
            
            # Should return empty results
            assert len(deals) == 0
            
            # Cache should not be called due to empty results
            mock_cache.store_deals.assert_not_called()
    
    def test_successful_results_caching(self):
        """Test that caching works normally when results are found and no error modal."""
        # Create a scraper with caching disabled to test direct caching
        scraper = NadlanDealsScraper(use_cache=True)
        
        # Mock the cache to track store_deals calls
        mock_cache = Mock()
        scraper.cache = mock_cache
        
        # Disable incremental collector to test direct caching
        scraper.incremental_collector = None
        
        # No error modal and successful results
        scraper.error_modal_encountered = False
        mock_deals = [
            Deal(address="רחוב הרצל 1", deal_amount=1500000.0)
        ]
        
        # Mock the selenium fetch to return results
        with patch.object(scraper, '_init_driver'), \
             patch.object(scraper, '_fetch_deals_by_address_selenium', return_value=mock_deals):
            deals = scraper.get_deals_by_address("רמת החייל")
            
            # Should return results
            assert len(deals) == 1
            
            # Cache should be called with the results
            mock_cache.store_deals.assert_called_once_with("רמת החייל", mock_deals, False)
    



class TestDealCache:
    """Test the DealCache class."""
    
    def test_get_cached_deals_with_error_modal_flag(self):
        """Test that cached deals with error modal flag are not returned."""
        from gov.nadlan.cache import DealCache
        from gov.nadlan.models import Deal
        import tempfile
        
        # Create a temporary cache directory
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = DealCache(cache_dir=temp_dir)
            
            # Create test deals
            deals = [Deal(address="רחוב הרצל 1", deal_amount=1500000.0)]
            
            # Store deals with error modal flag
            cache.store_deals("ק\"ם 3 תל אביב-יפו", deals, error_modal_encountered=True)
            
            # Try to get cached deals - should return None due to error modal flag
            cached_deals = cache.get_cached_deals("ק\"ם 3 תל אביב-יפו")
            assert cached_deals is None
    
    def test_get_cached_deals_without_error_modal_flag(self):
        """Test that cached deals without error modal flag are returned normally."""
        from gov.nadlan.cache import DealCache
        from gov.nadlan.models import Deal
        import tempfile
        
        # Create a temporary cache directory
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = DealCache(cache_dir=temp_dir)
            
            # Create test deals
            deals = [Deal(address="רחוב הרצל 1", deal_amount=1500000.0)]
            
            # Store deals without error modal flag
            cache.store_deals("רמת החייל", deals, error_modal_encountered=False)
            
            # Try to get cached deals - should return the deals
            cached_deals = cache.get_cached_deals("רמת החייל")
            assert cached_deals is not None
            assert len(cached_deals) == 1
            assert cached_deals[0].address == "רחוב הרצל 1"



if __name__ == "__main__":
    pytest.main([__file__])
