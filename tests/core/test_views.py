"""
Tests for Django views in backend-django/core/views.py
"""
import json
import pytest
from unittest.mock import Mock, patch
from django.test import TestCase, Client
from django.http import JsonResponse

# We need to add the project root to Python path for imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from backend_django.core.views import (
    sync_address,
    parse_json,
    listings,
    building_permits,
    building_rights,
    decisive_appraisals,
    rami_valuations,
    mortgage_analyze,
)


class TestParseJson:
    """Test the JSON parsing helper function."""
    
    def test_parse_valid_json(self):
        """Test parsing valid JSON."""
        mock_request = Mock()
        mock_request.body.decode.return_value = '{"key": "value"}'
        
        result = parse_json(mock_request)
        assert result == {"key": "value"}
    
    def test_parse_invalid_json(self):
        """Test parsing invalid JSON returns None."""
        mock_request = Mock()
        mock_request.body.decode.return_value = '{"invalid": json'
        
        result = parse_json(mock_request)
        assert result is None
    
    def test_parse_json_decode_error(self):
        """Test handling decode error."""
        mock_request = Mock()
        mock_request.body.decode.side_effect = Exception("Decode error")
        
        result = parse_json(mock_request)
        assert result is None


class TestSyncAddressView:
    """Test the sync_address view function."""
    
    @patch('backend_django.core.views.sync_address_sources')
    def test_sync_address_with_street_and_number(self, mock_sync):
        """Test sync address with explicit street and house number."""
        mock_sync.return_value = [
            {
                "id": "test123",
                "address": "הגולן 1",
                "price": 2500000,
                "confidence": 85
            }
        ]
        
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.body.decode.return_value = json.dumps({
            "street": "הגולן",
            "house_number": 1
        })
        
        response = sync_address(mock_request)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data['rows']) == 1
        assert data['rows'][0]['address'] == "הגולן 1"
        
        # Verify sync was called correctly
        mock_sync.assert_called_once_with("הגולן", 1)
    
    @patch('backend_django.core.views.sync_address_sources')
    def test_sync_address_with_parsed_address(self, mock_sync):
        """Test sync address with address string that needs parsing."""
        mock_sync.return_value = []
        
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.body.decode.return_value = json.dumps({
            "address": "רחוב הרצל 123"
        })
        
        response = sync_address(mock_request)
        
        # Verify response
        assert response.status_code == 200
        
        # Verify sync was called with parsed values
        mock_sync.assert_called_once_with("רחוב הרצל", 123)
    
    def test_sync_address_invalid_method(self):
        """Test sync address with non-POST method."""
        mock_request = Mock()
        mock_request.method = 'GET'
        
        response = sync_address(mock_request)
        
        assert response.status_code == 400
        assert b'POST required' in response.content
    
    def test_sync_address_invalid_json(self):
        """Test sync address with invalid JSON."""
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.body.decode.return_value = '{"invalid": json'
        
        response = sync_address(mock_request)
        
        assert response.status_code == 400
        assert b'Invalid JSON' in response.content
    
    def test_sync_address_missing_data(self):
        """Test sync address with missing street/number data."""
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.body.decode.return_value = json.dumps({
            "other_field": "value"
        })
        
        response = sync_address(mock_request)
        
        assert response.status_code == 400
        assert b'street and house_number required' in response.content


class TestDatabaseViews:
    """Test views that return database data."""
    
    @patch('backend_django.core.views.SQLAlchemyDatabase')
    def test_listings_view(self, mock_db_class):
        """Test listings view returns correct data."""
        # Setup mock database
        mock_listing = Mock()
        mock_listing.id = 1
        mock_listing.source = "yad2"
        mock_listing.external_id = "yad2_123"
        mock_listing.title = "דירה בתל אביב"
        mock_listing.price = 2500000.0
        mock_listing.address = "הרצל 123"
        mock_listing.rooms = 3.0
        mock_listing.floor = "2"
        mock_listing.size = 85.0
        mock_listing.property_type = "דירה"
        mock_listing.description = "דירה יפה"
        mock_listing.images = ["image1.jpg"]
        mock_listing.contact_info = {"phone": "050-1234567"}
        mock_listing.features = ["מעלית", "חניה"]
        mock_listing.url = "http://yad2.co.il/item/123"
        mock_listing.date_posted = "2024-01-15"
        mock_listing.scraped_at = None
        
        mock_db = Mock()
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_listing]
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        mock_request = Mock()
        
        # Execute
        response = listings(mock_request)
        
        # Verify response structure
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'rows' in data
        assert len(data['rows']) == 1
        
        listing_data = data['rows'][0]
        assert listing_data['id'] == 1
        assert listing_data['title'] == "דירה בתל אביב"
        assert listing_data['price'] == 2500000.0
        assert listing_data['address'] == "הרצל 123"
    
    @patch('backend_django.core.views.SQLAlchemyDatabase')
    def test_building_permits_view(self, mock_db_class):
        """Test building permits view."""
        mock_permit = Mock()
        mock_permit.id = 1
        mock_permit.permission_num = "BP-2024-001"
        mock_permit.request_num = "REQ-001"
        mock_permit.url = "http://example.com/permit"
        mock_permit.gush = "6638"
        mock_permit.helka = "96"
        mock_permit.data = {"status": "approved"}
        mock_permit.scraped_at = None
        
        mock_db = Mock()
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_permit]
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        mock_request = Mock()
        
        response = building_permits(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data['rows']) == 1
        assert data['rows'][0]['permission_num'] == "BP-2024-001"
    
    @patch('backend_django.core.views.SQLAlchemyDatabase')
    def test_building_rights_view(self, mock_db_class):
        """Test building rights view."""
        mock_rights = Mock()
        mock_rights.id = 1
        mock_rights.gush = "6638"
        mock_rights.helka = "96"
        mock_rights.file_path = "/path/to/rights.pdf"
        mock_rights.content_type = "application/pdf"
        mock_rights.data = {"rights": "4 floors"}
        mock_rights.scraped_at = None
        
        mock_db = Mock()
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_rights]
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        mock_request = Mock()
        
        response = building_rights(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data['rows']) == 1
        assert data['rows'][0]['gush'] == "6638"
        assert data['rows'][0]['helka'] == "96"
    
    @patch('backend_django.core.views.SQLAlchemyDatabase')
    def test_decisive_appraisals_view(self, mock_db_class):
        """Test decisive appraisals view."""
        mock_appraisal = Mock()
        mock_appraisal.id = 1
        mock_appraisal.title = "הכרעת שמאי - גוש 6638"
        mock_appraisal.date = "2025-07-20"
        mock_appraisal.appraiser = "שמואל כהן"
        mock_appraisal.committee = "ועדה מקומית תל אביב"
        mock_appraisal.pdf_url = "http://example.com/decision.pdf"
        mock_appraisal.data = {"amount": 2800000}
        mock_appraisal.scraped_at = None
        
        mock_db = Mock()
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_appraisal]
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        mock_request = Mock()
        
        response = decisive_appraisals(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data['rows']) == 1
        assert data['rows'][0]['title'] == "הכרעת שמאי - גוש 6638"
        assert data['rows'][0]['appraiser'] == "שמואל כהן"
    
    @patch('backend_django.core.views.SQLAlchemyDatabase')
    def test_rami_valuations_view(self, mock_db_class):
        """Test RAMI valuations view."""
        mock_valuation = Mock()
        mock_valuation.id = 1
        mock_valuation.plan_number = "PLAN-001"
        mock_valuation.name = "תכנית מפורטת"
        mock_valuation.data = {"status": "approved"}
        mock_valuation.scraped_at = None
        
        mock_db = Mock()
        mock_session = Mock()
        mock_session.query.return_value.order_by.return_value.all.return_value = [mock_valuation]
        mock_db.get_session.return_value.__enter__.return_value = mock_session
        mock_db_class.return_value = mock_db
        
        mock_request = Mock()
        
        response = rami_valuations(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert len(data['rows']) == 1
        assert data['rows'][0]['plan_number'] == "PLAN-001"
        assert data['rows'][0]['name'] == "תכנית מפורטת"


class TestMortgageAnalyze:
    """Test mortgage analysis view."""
    
    def test_mortgage_analyze_success(self):
        """Test successful mortgage analysis calculation."""
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.body.decode.return_value = json.dumps({
            "property_price": 2500000,
            "savings_total": 500000,
            "annual_rate_pct": 4.5,
            "term_years": 25,
            "transactions": [
                {"date": "2024-01-15", "amount": 25000},
                {"date": "2024-01-15", "amount": -15000},
                {"date": "2024-02-15", "amount": 26000},
                {"date": "2024-02-15", "amount": -16000}
            ]
        })
        
        response = mortgage_analyze(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Verify response structure
        assert 'metrics' in data
        assert 'recommendation' in data
        assert 'notes' in data
        
        # Verify metrics
        metrics = data['metrics']
        assert 'median_monthly_income' in metrics
        assert 'median_monthly_expense' in metrics
        assert 'monthly_surplus_estimate' in metrics
        
        # Verify recommendation
        recommendation = data['recommendation']
        assert 'recommended_monthly_payment' in recommendation
        assert 'max_loan_from_payment' in recommendation
        assert 'max_loan_by_ltv' in recommendation
        assert 'approved_loan_ceiling' in recommendation
        assert 'cash_gap_for_purchase' in recommendation
    
    def test_mortgage_analyze_invalid_method(self):
        """Test mortgage analysis with non-POST method."""
        mock_request = Mock()
        mock_request.method = 'GET'
        
        response = mortgage_analyze(mock_request)
        
        assert response.status_code == 400
        assert b'POST required' in response.content
    
    def test_mortgage_analyze_invalid_json(self):
        """Test mortgage analysis with invalid JSON."""
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.body.decode.return_value = '{"invalid": json'
        
        response = mortgage_analyze(mock_request)
        
        assert response.status_code == 400
        assert b'Invalid JSON' in response.content
    
    def test_mortgage_analyze_defaults(self):
        """Test mortgage analysis with default values."""
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.body.decode.return_value = json.dumps({})
        
        response = mortgage_analyze(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        
        # Should handle missing data gracefully with defaults
        assert 'metrics' in data
        assert 'recommendation' in data
