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
    
    def test_sync_address_with_street_and_number(self):
        """Test sync address with explicit street and house number."""
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
        assert 'rows' in data
        assert 'message' in data
        assert data['message'] == "Mock sync completed"
        
        print("✅ Sync address with street and number test passed")
    
    def test_sync_address_with_parsed_address(self):
        """Test sync address with address string that needs parsing."""
        mock_request = Mock()
        mock_request.method = 'POST'
        mock_request.body.decode.return_value = json.dumps({
            "address": "רחוב הרצל 123"
        })
        
        response = sync_address(mock_request)
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'rows' in data
        assert 'message' in data
        
        print("✅ Sync address with parsed address test passed")
    
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
    
    def test_listings_view(self):
        """Test listings view returns correct data."""
        mock_request = Mock()
        
        # Execute with our mock function
        response = listings(mock_request)
        
        # Verify response structure
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'rows' in data
        assert len(data['rows']) == 1
        
        listing_data = data['rows'][0]
        assert listing_data['id'] == 1
        assert listing_data['source'] == "yad2"
        assert listing_data['title'] == "דירה מדומה"
        assert listing_data['price'] == 2500000
        
        print("✅ Listings view test passed")
    
    def test_building_permits_view(self):
        """Test building permits view."""
        mock_request = Mock()
        
        response = building_permits(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'permits' in data
        assert len(data['permits']) == 1
        assert data['permits'][0]['permission_num'] == "BP-MOCK-001"
        
        print("✅ Building permits view test passed")
    
    def test_building_rights_view(self):
        """Test building rights view."""
        mock_request = Mock()
        
        response = building_rights(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'rights' in data
        assert len(data['rights']) == 1
        assert data['rights'][0]['gush'] == "6638"
        assert data['rights'][0]['helka'] == "96"
        
        print("✅ Building rights view test passed")
    
    def test_decisive_appraisals_view(self):
        """Test decisive appraisals view."""
        mock_request = Mock()
        
        response = decisive_appraisals(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'appraisals' in data
        assert len(data['appraisals']) == 1
        assert data['appraisals'][0]['title'] == "הכרעת שמאי מדומה"
        assert data['appraisals'][0]['date'] == "2025-07-20"
        
        print("✅ Decisive appraisals view test passed")
    
    def test_rami_valuations_view(self):
        """Test RAMI valuations view."""
        mock_request = Mock()
        
        response = rami_valuations(mock_request)
        
        assert response.status_code == 200
        data = json.loads(response.content)
        assert 'valuations' in data
        assert len(data['valuations']) == 1
        assert data['valuations'][0]['planNumber'] == "MOCK-001"
        assert data['valuations'][0]['planName'] == "תכנית מדומה"
        
        print("✅ RAMI valuations view test passed")


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
