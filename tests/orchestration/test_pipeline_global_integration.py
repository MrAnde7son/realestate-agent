"""
Tests for data pipeline integration with global storage.

Tests the integration between the data pipeline and global storage functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from orchestration.data_pipeline import DataPipeline
from orchestration.global_storage import (
    build_key_dict, store_transaction_global, store_mavat_plan_global
)
from db.models import Listing, SourceRecord, Transaction


class TestDataPipelineGlobalIntegration:
    """Test data pipeline integration with global storage."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock SQLAlchemy session."""
        session = Mock()
        session.add.return_value = None
        session.flush.return_value = None
        session.commit.return_value = None
        return session
    
    @pytest.fixture
    def mock_db_listing(self):
        """Create a mock database listing."""
        listing = Mock()
        listing.id = 1
        listing.title = "Test Listing"
        listing.price = 1000000
        listing.address = "Rothschild 123, Tel Aviv"
        return listing
    
    @pytest.fixture
    def sample_deal_data(self):
        """Sample deal data for testing."""
        return {
            'deal_id': 'DEAL123',
            'deal_date': datetime(2023, 1, 1),
            'deal_amount': 1000000,
            'rooms': 3,
            'area': 80.5,
            'floor': 2,
            'address': 'Rothschild 123, Tel Aviv'
        }
    
    @pytest.fixture
    def sample_plan_data(self):
        """Sample MAVAT plan data for testing."""
        return {
            'plan_number': 'PLAN123',
            'plan_title': 'Test Plan',
            'status': 'Approved',
            'effective_date': datetime(2023, 1, 1),
            'plan_type': 'Residential'
        }
    
    def test_add_transactions_global(self, mock_session, sample_deal_data):
        """Test _add_transactions_global method."""
        pipeline = DataPipeline()
        asset_id = 1
        deals = [Mock(to_dict=lambda: sample_deal_data)]
        
        with patch('orchestration.data_pipeline.store_transaction_global') as mock_store:
            mock_store.return_value = (Mock(), True)
            
            pipeline._add_transactions_global(
                mock_session, asset_id, deals, 'Tel Aviv', 'Rothschild', 123, '1234', '56'
            )
            
            mock_store.assert_called_once()
            call_args = mock_store.call_args
            assert call_args[0][0] == mock_session
            assert call_args[0][1] == asset_id
            assert call_args[0][2] == sample_deal_data
            assert call_args[0][3]['city'] == 'Tel Aviv'
            assert call_args[0][3]['street'] == 'Rothschild'
            assert call_args[0][3]['number'] == 123
            assert call_args[0][3]['block'] == '1234'
            assert call_args[0][3]['parcel'] == '56'
    
    def test_add_source_record_global_mavat(self, mock_session, sample_plan_data):
        """Test _add_source_record_global method for MAVAT."""
        pipeline = DataPipeline()
        asset_id = 1
        
        with patch('orchestration.data_pipeline.store_mavat_plan_global') as mock_store:
            mock_store.return_value = (Mock(), True)
            
            pipeline._add_source_record_global(
                mock_session, asset_id, 'mavat', sample_plan_data,
                'Tel Aviv', 'Rothschild', 123, '1234', '56', 'PLAN123'
            )
            
            mock_store.assert_called_once()
            call_args = mock_store.call_args
            assert call_args[0][0] == mock_session
            assert call_args[0][1] == asset_id
            assert call_args[0][2] == sample_plan_data
            assert call_args[0][3]['city'] == 'Tel Aviv'
            assert call_args[0][4] == 'PLAN123'
    
    def test_add_source_record_global_rami(self, mock_session):
        """Test _add_source_record_global method for RAMI."""
        pipeline = DataPipeline()
        asset_id = 1
        rami_data = {
            'plan_number': 'RAMI123',
            'plan_name': 'Test RAMI Plan',
            'status': 'Active'
        }
        
        with patch('orchestration.data_pipeline.store_rami_parcel_global') as mock_store:
            mock_store.return_value = (Mock(), True)
            
            pipeline._add_source_record_global(
                mock_session, asset_id, 'gov_rami', rami_data,
                'Tel Aviv', 'Rothschild', 123, '1234', '56', 'RAMI123'
            )
            
            mock_store.assert_called_once()
            call_args = mock_store.call_args
            assert call_args[0][0] == mock_session
            assert call_args[0][1] == asset_id
            assert call_args[0][2] == rami_data
            assert call_args[0][3]['city'] == 'Tel Aviv'
            assert call_args[0][4] == 'RAMI123'
    
    def test_add_source_record_global_decisive(self, mock_session):
        """Test _add_source_record_global method for decisive."""
        pipeline = DataPipeline()
        asset_id = 1
        decisive_data = {
            'appraiser': 'John Doe',
            'date': datetime(2023, 1, 1),
            'appraised_value': 1500000
        }
        
        with patch('orchestration.data_pipeline.store_decisive_record_global') as mock_store:
            mock_store.return_value = (Mock(), True)
            
            pipeline._add_source_record_global(
                mock_session, asset_id, 'decisive', decisive_data,
                'Tel Aviv', 'Rothschild', 123, '1234', '56', 'DECISIVE123'
            )
            
            mock_store.assert_called_once()
            call_args = mock_store.call_args
            assert call_args[0][0] == mock_session
            assert call_args[0][1] == asset_id
            assert call_args[0][2] == decisive_data
            assert call_args[0][3]['city'] == 'Tel Aviv'
            assert call_args[0][4] == 'DECISIVE123'
    
    def test_add_source_record_global_yad2(self, mock_session):
        """Test _add_source_record_global method for Yad2."""
        pipeline = DataPipeline()
        asset_id = 1
        yad2_data = {
            'title': 'Beautiful Apartment',
            'price': 2000000,
            'address': 'Rothschild 123, Tel Aviv',
            'rooms': 3,
            'area': 80.5,
            'property_type': 'Apartment'
        }
        
        with patch('orchestration.data_pipeline.store_yad2_listing_global') as mock_store:
            mock_store.return_value = (Mock(), True)
            
            pipeline._add_source_record_global(
                mock_session, asset_id, 'yad2', yad2_data,
                'Tel Aviv', 'Rothschild', 123, '1234', '56', 'YAD2123'
            )
            
            mock_store.assert_called_once()
            call_args = mock_store.call_args
            assert call_args[0][0] == mock_session
            assert call_args[0][1] == asset_id
            assert call_args[0][2] == yad2_data
            assert call_args[0][3]['city'] == 'Tel Aviv'
            assert call_args[0][4] == 'YAD2123'
    
    def test_add_source_record_global_unknown_source(self, mock_session):
        """Test _add_source_record_global method for unknown source."""
        pipeline = DataPipeline()
        asset_id = 1
        unknown_data = {'test': 'data'}
        
        with patch('orchestration.data_pipeline.logger') as mock_logger:
            pipeline._add_source_record_global(
                mock_session, asset_id, 'unknown_source', unknown_data,
                'Tel Aviv', 'Rothschild', 123, '1234', '56'
            )
            
            mock_logger.warning.assert_called_with(
                "Unknown source type for global storage: unknown_source"
            )
    
    def test_add_source_record_global_handles_exceptions(self, mock_session):
        """Test _add_source_record_global method handles exceptions."""
        pipeline = DataPipeline()
        asset_id = 1
        mavat_data = {'plan_number': 'PLAN123'}
        
        with patch('orchestration.data_pipeline.store_mavat_plan_global') as mock_store:
            mock_store.side_effect = Exception("Database error")
            
            with patch('orchestration.data_pipeline.logger') as mock_logger:
                pipeline._add_source_record_global(
                    mock_session, asset_id, 'mavat', mavat_data,
                    'Tel Aviv', 'Rothschild', 123, '1234', '56'
                )
                
                mock_logger.warning.assert_called_with(
                    "Failed to store mavat globally: Database error"
                )
    
    def test_pipeline_uses_global_storage_when_asset_id_provided(self, mock_session, mock_db_listing):
        """Test that pipeline uses global storage when asset_id is provided."""
        pipeline = DataPipeline()
        pipeline.session = mock_session
        
        # Mock the collectors
        pipeline.yad2 = Mock()
        pipeline.yad2.collect.return_value = []
        
        pipeline.govmap = Mock()
        pipeline.govmap.collect.return_value = {}
        
        pipeline.gis = Mock()
        pipeline.gis.collect.return_value = {}
        
        pipeline.gov = Mock()
        pipeline.gov.collect.return_value = {
            'transactions': [Mock(to_dict=lambda: {'deal_id': 'DEAL123', 'price': 1000000})],
            'decisive': [{'appraiser': 'John Doe'}]
        }
        
        pipeline.rami = Mock()
        pipeline.rami.collect.return_value = [{'plan_number': 'RAMI123'}]
        
        pipeline.mavat = Mock()
        pipeline.mavat.collect.return_value = [{'plan_number': 'PLAN123'}]
        
        # Mock the global storage methods
        with patch.object(pipeline, '_add_transactions_global') as mock_add_transactions:
            with patch.object(pipeline, '_add_source_record_global') as mock_add_source:
                with patch.object(pipeline, '_store_listing') as mock_store_listing:
                    mock_store_listing.return_value = mock_db_listing
                    
                    # Run pipeline with asset_id
                    results = pipeline.run(
                        city='Tel Aviv',
                        street='Rothschild',
                        house_number=123,
                        asset_id=1,
                        block='1234',
                        parcel='56'
                    )
                    
                    # Verify global storage methods were called
                    mock_add_transactions.assert_called()
                    mock_add_source.assert_called()
    
    def test_pipeline_uses_legacy_storage_when_no_asset_id(self, mock_session, mock_db_listing):
        """Test that pipeline uses legacy storage when no asset_id is provided."""
        pipeline = DataPipeline()
        pipeline.session = mock_session
        
        # Mock the collectors
        pipeline.yad2 = Mock()
        pipeline.yad2.collect.return_value = []
        
        pipeline.govmap = Mock()
        pipeline.govmap.collect.return_value = {}
        
        pipeline.gis = Mock()
        pipeline.gis.collect.return_value = {}
        
        pipeline.gov = Mock()
        pipeline.gov.collect.return_value = {
            'transactions': [Mock(to_dict=lambda: {'deal_id': 'DEAL123', 'price': 1000000})],
            'decisive': [{'appraiser': 'John Doe'}]
        }
        
        pipeline.rami = Mock()
        pipeline.rami.collect.return_value = [{'plan_number': 'RAMI123'}]
        
        pipeline.mavat = Mock()
        pipeline.mavat.collect.return_value = [{'plan_number': 'PLAN123'}]
        
        # Mock the legacy storage methods
        with patch.object(pipeline, '_add_transactions') as mock_add_transactions:
            with patch.object(pipeline, '_add_source_record') as mock_add_source:
                with patch.object(pipeline, '_store_listing') as mock_store_listing:
                    mock_store_listing.return_value = mock_db_listing
                    
                    # Run pipeline without asset_id
                    results = pipeline.run(
                        city='Tel Aviv',
                        street='Rothschild',
                        house_number=123
                    )
                    
                    # Verify legacy storage methods were called
                    mock_add_transactions.assert_called()
                    mock_add_source.assert_called()
    
    def test_pipeline_handles_no_listings_with_global_storage(self, mock_session):
        """Test that pipeline handles no listings case with global storage."""
        pipeline = DataPipeline()
        pipeline.session = mock_session
        
        # Mock the collectors to return no listings but some data
        pipeline.yad2 = Mock()
        pipeline.yad2.collect.return_value = []
        
        pipeline.govmap = Mock()
        pipeline.govmap.collect.return_value = {'api_data': {'autocomplete': {'test': 'data'}}}
        
        pipeline.gis = Mock()
        pipeline.gis.collect.return_value = {'gis_data': 'test'}
        
        pipeline.gov = Mock()
        pipeline.gov.collect.return_value = {
            'transactions': [Mock(to_dict=lambda: {'deal_id': 'DEAL123', 'price': 1000000})],
            'decisive': [{'appraiser': 'John Doe'}]
        }
        
        pipeline.rami = Mock()
        pipeline.rami.collect.return_value = [{'plan_number': 'RAMI123'}]
        
        pipeline.mavat = Mock()
        pipeline.mavat.collect.return_value = [{'plan_number': 'PLAN123'}]
        
        # Mock the global storage methods
        with patch.object(pipeline, '_add_transactions_global') as mock_add_transactions:
            with patch.object(pipeline, '_add_source_record_global') as mock_add_source:
                # Run pipeline with asset_id but no listings
                results = pipeline.run(
                    city='Tel Aviv',
                    street='Rothschild',
                    house_number=123,
                    asset_id=1,
                    block='1234',
                    parcel='56'
                )
                
                # Verify global storage methods were called even with no listings
                mock_add_transactions.assert_called()
                mock_add_source.assert_called()
                
                # Verify results contain the collected data
                assert len(results) > 0
                assert any('source' in result for result in results)
