"""
Tests for global storage operations.

Tests the functionality of storing data in global tables and creating links to assets.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from orchestration.global_storage import (
    compute_key_fingerprint, build_key_dict,
    store_transaction_global, store_mavat_plan_global,
    store_rami_parcel_global, store_decisive_record_global,
    store_yad2_listing_global
)


class TestKeyFingerprinting:
    """Test key fingerprinting functionality."""
    
    def test_compute_key_fingerprint_basic(self):
        """Test basic fingerprint computation."""
        key_dict = {
            'city': 'Tel Aviv',
            'street': 'Rothschild',
            'number': 123,
            'block': '1234',
            'parcel': '56'
        }
        
        fingerprint = compute_key_fingerprint(key_dict)
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64  # SHA256 hex length
        assert fingerprint.isalnum()
    
    def test_compute_key_fingerprint_deterministic(self):
        """Test that fingerprints are deterministic."""
        key_dict = {
            'city': 'Tel Aviv',
            'street': 'Rothschild',
            'number': 123,
            'block': '1234',
            'parcel': '56'
        }
        
        fp1 = compute_key_fingerprint(key_dict)
        fp2 = compute_key_fingerprint(key_dict)
        
        assert fp1 == fp2
    
    def test_compute_key_fingerprint_order_independent(self):
        """Test that fingerprint is independent of key order."""
        key_dict1 = {
            'city': 'Tel Aviv',
            'street': 'Rothschild',
            'number': 123,
            'block': '1234',
            'parcel': '56'
        }
        
        key_dict2 = {
            'parcel': '56',
            'block': '1234',
            'number': 123,
            'street': 'Rothschild',
            'city': 'Tel Aviv'
        }
        
        fp1 = compute_key_fingerprint(key_dict1)
        fp2 = compute_key_fingerprint(key_dict2)
        
        assert fp1 == fp2
    
    def test_compute_key_fingerprint_handles_none(self):
        """Test that fingerprint handles None values."""
        key_dict = {
            'city': 'Tel Aviv',
            'street': None,
            'number': 123,
            'block': '',
            'parcel': None
        }
        
        fingerprint = compute_key_fingerprint(key_dict)
        
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 64
    
    def test_build_key_dict(self):
        """Test building key dictionary from parameters."""
        key_dict = build_key_dict(
            city='Tel Aviv',
            street='Rothschild',
            number=123,
            block='1234',
            parcel='56',
            subparcel='78'
        )
        
        expected = {
            'city': 'Tel Aviv',
            'street': 'Rothschild',
            'number': 123,
            'block': '1234',
            'parcel': '56',
            'subparcel': '78'
        }
        
        assert key_dict == expected


class TestGlobalStorage:
    """Test global storage operations."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        session = Mock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        session.query.return_value.filter_by.return_value.exists.return_value = False
        return session
    
    @pytest.fixture
    def sample_key_dict(self):
        """Sample key dictionary for testing."""
        return {
            'city': 'Tel Aviv',
            'street': 'Rothschild',
            'number': 123,
            'block': '1234',
            'parcel': '56'
        }
    
    def test_store_transaction_global_new(self, mock_session, sample_key_dict):
        """Test storing a new transaction globally."""
        asset_id = 1
        deal_data = {
            'deal_id': 'DEAL123',
            'deal_date': datetime(2023, 1, 1),
            'deal_amount': 1000000,
            'rooms': 3,
            'area': 80.5,
            'floor': 2,
            'address': 'Rothschild 123, Tel Aviv'
        }
        
        # Mock the global transaction creation
        mock_global_transaction = Mock()
        mock_global_transaction.id = 1
        mock_session.add.return_value = None
        mock_session.flush.return_value = None
        
        with patch('orchestration.global_storage.RealEstateTransactionGlobal') as mock_model:
            mock_model.return_value = mock_global_transaction
            
            result_transaction, created = store_transaction_global(
                mock_session, asset_id, deal_data, sample_key_dict
            )
            
            assert created is True
            assert result_transaction == mock_global_transaction
            mock_session.add.assert_called()
            mock_session.flush.assert_called()
    
    def test_store_transaction_global_existing(self, mock_session, sample_key_dict):
        """Test updating an existing transaction globally."""
        asset_id = 1
        deal_data = {
            'deal_id': 'DEAL123',
            'deal_date': datetime(2023, 1, 1),
            'deal_amount': 1000000,
            'rooms': 3,
            'area': 80.5,
            'floor': 2,
            'address': 'Rothschild 123, Tel Aviv'
        }
        
        # Mock existing transaction
        mock_existing_transaction = Mock()
        mock_existing_transaction.id = 1
        mock_session.query.return_value.filter_by.return_value.first.return_value = mock_existing_transaction
        
        with patch('orchestration.global_storage.AssetToDeal') as mock_link_model:
            mock_link_model.return_value = Mock()
            
            result_transaction, created = store_transaction_global(
                mock_session, asset_id, deal_data, sample_key_dict
            )
            
            assert created is False
            assert result_transaction == mock_existing_transaction
    
    def test_store_mavat_plan_global_new(self, mock_session, sample_key_dict):
        """Test storing a new MAVAT plan globally."""
        asset_id = 1
        plan_data = {
            'plan_number': 'PLAN123',
            'plan_title': 'Test Plan',
            'status': 'Approved',
            'effective_date': datetime(2023, 1, 1),
            'plan_type': 'Residential'
        }
        external_id = 'PLAN123'
        
        # Mock the global plan creation
        mock_global_plan = Mock()
        mock_global_plan.id = 1
        mock_session.add.return_value = None
        mock_session.flush.return_value = None
        
        with patch('orchestration.global_storage.MavatPlanGlobal') as mock_model:
            mock_model.return_value = mock_global_plan
            
            result_plan, created = store_mavat_plan_global(
                mock_session, asset_id, plan_data, sample_key_dict, external_id
            )
            
            assert created is True
            assert result_plan == mock_global_plan
            mock_session.add.assert_called()
            mock_session.flush.assert_called()
    
    def test_store_rami_parcel_global_new(self, mock_session, sample_key_dict):
        """Test storing a new RAMI parcel globally."""
        asset_id = 1
        parcel_data = {
            'plan_number': 'RAMI123',
            'plan_name': 'Test RAMI Plan',
            'status': 'Active',
            'status_date': datetime(2023, 1, 1),
            'market_value': 2000000,
            'building_rights': 150.0
        }
        external_id = 'RAMI123'
        
        # Mock the global parcel creation
        mock_global_parcel = Mock()
        mock_global_parcel.id = 1
        mock_session.add.return_value = None
        mock_session.flush.return_value = None
        
        with patch('orchestration.global_storage.RamiParcelGlobal') as mock_model:
            mock_model.return_value = mock_global_parcel
            
            result_parcel, created = store_rami_parcel_global(
                mock_session, asset_id, parcel_data, sample_key_dict, external_id
            )
            
            assert created is True
            assert result_parcel == mock_global_parcel
            mock_session.add.assert_called()
            mock_session.flush.assert_called()
    
    def test_store_decisive_record_global_new(self, mock_session, sample_key_dict):
        """Test storing a new decisive record globally."""
        asset_id = 1
        record_data = {
            'appraiser': 'John Doe',
            'date': datetime(2023, 1, 1),
            'appraised_value': 1500000
        }
        external_id = 'DECISIVE123'
        url = 'https://example.com/decisive'
        
        # Mock the global record creation
        mock_global_record = Mock()
        mock_global_record.id = 1
        mock_session.add.return_value = None
        mock_session.flush.return_value = None
        
        with patch('orchestration.global_storage.DecisiveRecordGlobal') as mock_model:
            mock_model.return_value = mock_global_record
            
            result_record, created = store_decisive_record_global(
                mock_session, asset_id, record_data, sample_key_dict, external_id, url
            )
            
            assert created is True
            assert result_record == mock_global_record
            mock_session.add.assert_called()
            mock_session.flush.assert_called()
    
    def test_store_yad2_listing_global_new(self, mock_session, sample_key_dict):
        """Test storing a new Yad2 listing globally."""
        asset_id = 1
        listing_data = {
            'title': 'Beautiful Apartment',
            'price': 2000000,
            'address': 'Rothschild 123, Tel Aviv',
            'rooms': 3,
            'area': 80.5,
            'property_type': 'Apartment'
        }
        external_id = 'YAD2123'
        url = 'https://yad2.co.il/listing/123'
        
        # Mock the global listing creation
        mock_global_listing = Mock()
        mock_global_listing.id = 1
        mock_session.add.return_value = None
        mock_session.flush.return_value = None
        
        with patch('orchestration.global_storage.Yad2ListingGlobal') as mock_model:
            mock_model.return_value = mock_global_listing
            
            result_listing, created = store_yad2_listing_global(
                mock_session, asset_id, listing_data, sample_key_dict, external_id, url
            )
            
            assert created is True
            assert result_listing == mock_global_listing
            mock_session.add.assert_called()
            mock_session.flush.assert_called()
    
    def test_store_transaction_global_without_deal_id(self, mock_session, sample_key_dict):
        """Test storing transaction without deal_id (uses content hash)."""
        asset_id = 1
        deal_data = {
            'deal_date': datetime(2023, 1, 1),
            'deal_amount': 1000000,
            'address': 'Rothschild 123, Tel Aviv'
        }
        
        # Mock the global transaction creation
        mock_global_transaction = Mock()
        mock_global_transaction.id = 1
        mock_session.add.return_value = None
        mock_session.flush.return_value = None
        
        with patch('orchestration.global_storage.RealEstateTransactionGlobal') as mock_model:
            mock_model.return_value = mock_global_transaction
            
            result_transaction, created = store_transaction_global(
                mock_session, asset_id, deal_data, sample_key_dict
            )
            
            assert created is True
            assert result_transaction == mock_global_transaction
            mock_session.add.assert_called()
            mock_session.flush.assert_called()
    
    def test_store_functions_handle_exceptions(self, mock_session, sample_key_dict):
        """Test that storage functions handle exceptions gracefully."""
        asset_id = 1
        deal_data = {'deal_id': 'DEAL123'}
        
        # Mock session to raise exception
        mock_session.add.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            store_transaction_global(mock_session, asset_id, deal_data, sample_key_dict)
