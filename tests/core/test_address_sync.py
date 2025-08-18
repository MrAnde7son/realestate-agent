"""
Tests for address sync functionality in backend-django/core/tasks.py
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# We need to add the project root to Python path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from backend_django.core.tasks import (
    sync_address_sources,
    pull_new_listings,
    pull_gis_permits,
    pull_gis_rights,
    pull_decisive_appraisals,
    pull_rami_valuations,
    _parse_street_number,
)


class TestParseStreetNumber:
    """Test the address parsing helper function."""
    
    def test_parse_valid_address(self):
        """Test parsing valid address string."""
        street, number = _parse_street_number("רחוב הרצל 123")
        assert street == "רחוב הרצל"
        assert number == 123
    
    def test_parse_address_with_extra_spaces(self):
        """Test parsing address with extra spaces."""
        street, number = _parse_street_number("  שדרות רוטשילד   45  ")
        assert street == "שדרות רוטשילד"
        assert number == 45
    
    def test_parse_invalid_address(self):
        """Test parsing invalid address returns None."""
        street, number = _parse_street_number("רחוב ללא מספר")
        assert street is None
        assert number is None
    
    def test_parse_empty_address(self):
        """Test parsing empty/None address."""
        street, number = _parse_street_number(None)
        assert street is None
        assert number is None
        
        street, number = _parse_street_number("")
        assert street is None
        assert number is None


class TestSyncAddressSources:
    """Test the main address sync functionality."""
    
    @patch('backend_django.core.tasks.TelAvivGS')
    @patch('backend_django.core.tasks.pull_new_listings')
    @patch('backend_django.core.tasks.pull_gis_permits')
    @patch('backend_django.core.tasks.pull_gis_rights')
    @patch('backend_django.core.tasks.pull_decisive_appraisals')
    @patch('backend_django.core.tasks.pull_rami_valuations')
    def test_sync_address_sources_success(
        self, mock_rami, mock_decisive, mock_rights, mock_permits, 
        mock_listings, mock_gs_class
    ):
        """Test successful address sync with all data sources."""
        # Setup mocks
        mock_gs = Mock()
        mock_gs_class.return_value = mock_gs
        mock_gs.get_address_coordinates.return_value = (184320.94, 668548.65)
        mock_gs.get_parcels.return_value = [{"GUSH": "6638", "HELKA": "96"}]
        
        mock_listings.return_value = [
            {
                "id": "test123",
                "address": "הגולן 1",
                "price": 2500000,
                "confidence": 85,
                "riskFlags": [],
                "remaining_rights": 45,
                "link": "http://example.com"
            }
        ]
        
        # Execute
        result = sync_address_sources("הגולן", 1)
        
        # Verify
        assert len(result) == 1
        assert result[0]["address"] == "הגולן 1"
        
        # Verify all external calls were made
        mock_gs.get_address_coordinates.assert_called_once_with("הגולן", 1)
        mock_listings.assert_called_once_with(address_filter="הגולן 1")
        mock_permits.assert_called_once_with(184320.94, 668548.65)
        mock_rights.assert_called_once_with(184320.94, 668548.65)
        mock_decisive.assert_called_once_with("6638", "96")
        mock_rami.assert_called_once_with({"gush": "6638", "chelka": "96", "city": 5000})
    
    @patch('backend_django.core.tasks.TelAvivGS')
    @patch('backend_django.core.tasks.pull_new_listings')
    def test_sync_address_sources_geocode_failure(self, mock_listings, mock_gs_class):
        """Test handling of geocoding failure."""
        # Setup mocks
        mock_gs = Mock()
        mock_gs_class.return_value = mock_gs
        mock_gs.get_address_coordinates.side_effect = Exception("Geocoding failed")
        
        # Execute
        result = sync_address_sources("Invalid Street", 999)
        
        # Verify empty result due to geocoding failure
        assert result == []
        mock_listings.assert_not_called()
    
    @patch('backend_django.core.tasks.TelAvivGS')
    @patch('backend_django.core.tasks.pull_new_listings')
    @patch('backend_django.core.tasks.pull_gis_permits')
    @patch('backend_django.core.tasks.pull_gis_rights')
    def test_sync_address_sources_no_parcels(
        self, mock_rights, mock_permits, mock_listings, mock_gs_class
    ):
        """Test sync when no parcels are found."""
        # Setup mocks
        mock_gs = Mock()
        mock_gs_class.return_value = mock_gs
        mock_gs.get_address_coordinates.return_value = (184320.94, 668548.65)
        mock_gs.get_parcels.return_value = []  # No parcels found
        
        mock_listings.return_value = []
        
        # Execute
        result = sync_address_sources("הגולן", 1)
        
        # Verify basic GIS calls were made but not parcel-dependent calls
        mock_permits.assert_called_once()
        mock_rights.assert_called_once()
        # These should not be called without parcels
        assert mock_gs.get_parcels.called


class TestPullNewListings:
    """Test Yad2 listing ingestion."""
    
    @patch('backend_django.core.tasks.Yad2Scraper')
    @patch('backend_django.core.tasks.SQLAlchemyDatabase')
    def test_pull_new_listings_success(self, mock_db_class, mock_scraper_class):
        """Test successful listing pull from Yad2."""
        # Setup mocks
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        
        mock_listing = Mock()
        mock_listing.to_dict.return_value = {
            "listing_id": "yad2_123",
            "title": "דירה בתל אביב",
            "price": 2500000,
            "address": "הרצל 123, תל אביב",
            "rooms": 3,
            "size": 85,
            "url": "http://yad2.co.il/item/123"
        }
        mock_scraper.scrape_all_pages.return_value = [mock_listing]
        
        mock_db = Mock()
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        # Execute
        result = pull_new_listings()
        
        # Verify
        assert len(result) == 1
        assert result[0]["id"] == "yad2_123"
        assert result[0]["address"] == "הרצל 123, תל אביב"
        assert result[0]["price"] == 2500000
        
        # Verify database operations
        mock_session.merge.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('backend_django.core.tasks.Yad2Scraper')
    def test_pull_new_listings_scrape_failure(self, mock_scraper_class):
        """Test handling of Yad2 scraping failure."""
        # Setup mock to raise exception
        mock_scraper = Mock()
        mock_scraper_class.return_value = mock_scraper
        mock_scraper.scrape_all_pages.side_effect = Exception("Network error")
        
        # Execute
        result = pull_new_listings()
        
        # Verify empty result on failure
        assert result == []


class TestPullGisData:
    """Test GIS data pulling functions."""
    
    @patch('backend_django.core.tasks.TelAvivGS')
    @patch('backend_django.core.tasks.SQLAlchemyDatabase')
    def test_pull_gis_permits_success(self, mock_db_class, mock_gs_class):
        """Test successful building permits fetch."""
        # Setup mocks
        mock_gs = Mock()
        mock_gs_class.return_value = mock_gs
        mock_gs.get_building_permits.return_value = [
            {
                "permission_num": "BP-2024-001",
                "request_num": "REQ-001",
                "url_hadmaya": "http://example.com/permit1"
            }
        ]
        
        mock_db = Mock()
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        # Execute
        pull_gis_permits(184320.94, 668548.65)
        
        # Verify
        mock_gs.get_building_permits.assert_called_once_with(
            184320.94, 668548.65, radius=30, download_pdfs=False
        )
        mock_session.merge.assert_called_once()
        mock_session.commit.assert_called_once()
    
    @patch('backend_django.core.tasks.TelAvivGS')
    @patch('backend_django.core.tasks.SQLAlchemyDatabase')
    def test_pull_gis_rights_success(self, mock_db_class, mock_gs_class):
        """Test successful building rights fetch."""
        # Setup mocks
        mock_gs = Mock()
        mock_gs_class.return_value = mock_gs
        mock_gs.get_building_privilege_page.return_value = {
            "gush": "6638",
            "helka": "96",
            "file_path": "/path/to/rights.pdf",
            "content_type": "application/pdf"
        }
        
        mock_db = Mock()
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        # Execute
        pull_gis_rights(184320.94, 668548.65)
        
        # Verify
        mock_gs.get_building_privilege_page.assert_called_once_with(
            184320.94, 668548.65, save_dir="privilege_pages"
        )
        mock_session.merge.assert_called_once()
        mock_session.commit.assert_called_once()


class TestPullDecisiveAppraisals:
    """Test decisive appraisal data pulling."""
    
    @patch('backend_django.core.tasks.fetch_decisive_appraisals')
    @patch('backend_django.core.tasks.SQLAlchemyDatabase')
    def test_pull_decisive_appraisals_success(self, mock_db_class, mock_fetch):
        """Test successful decisive appraisal fetch."""
        # Setup mocks
        mock_fetch.return_value = [
            {
                "title": "הכרעת שמאי - גוש 6638 חלקה 96",
                "date": "2025-07-20",
                "appraiser": "שמואל כהן",
                "committee": "ועדה מקומית תל אביב",
                "pdf_url": "http://example.com/decision.pdf"
            }
        ]
        
        mock_db = Mock()
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        # Execute
        pull_decisive_appraisals("6638", "96")
        
        # Verify
        mock_fetch.assert_called_once_with(block="6638", plot="96", max_pages=1)
        mock_session.merge.assert_called_once()
        mock_session.commit.assert_called_once()


class TestPullRamiValuations:
    """Test RAMI valuation data pulling."""
    
    @patch('backend_django.core.tasks.RamiClient')
    @patch('backend_django.core.tasks.SQLAlchemyDatabase')
    def test_pull_rami_valuations_success(self, mock_db_class, mock_client_class):
        """Test successful RAMI valuation fetch."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock DataFrame with to_dict() method
        mock_row = Mock()
        mock_row.get.side_effect = lambda key: {
            "planNumber": "PLAN-001",
            "planName": "תכנית מפורטת"
        }.get(key)
        mock_row.to_dict.return_value = {
            "planNumber": "PLAN-001",
            "planName": "תכנית מפורטת"
        }
        
        mock_df = Mock()
        mock_df.iterrows.return_value = [(0, mock_row)]
        mock_client.fetch_plans.return_value = mock_df
        
        mock_db = Mock()
        mock_session = Mock()
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        # Execute
        pull_rami_valuations({"gush": "6638", "chelka": "96"})
        
        # Verify
        mock_client.fetch_plans.assert_called_once_with({"gush": "6638", "chelka": "96"})
        mock_session.merge.assert_called_once()
        mock_session.commit.assert_called_once()
