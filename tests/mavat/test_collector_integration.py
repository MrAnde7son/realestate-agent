#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for MavatCollector."""

import pytest
from unittest.mock import Mock, patch
from mavat.collector.mavat_collector import MavatCollector


class TestMavatCollectorIntegration:
    """Integration tests for MavatCollector."""

    @pytest.fixture
    def collector(self):
        """Create a MavatCollector instance for testing."""
        return MavatCollector()

    def test_collector_creation(self, collector):
        """Test that MavatCollector can be created."""
        assert collector is not None
        assert hasattr(collector, 'client')

    def test_collect_method_interface(self, collector):
        """Test that the collect method follows the base interface."""
        # The collect method should exist and be callable
        assert hasattr(collector, 'collect')
        assert callable(collector.collect)

    def test_search_methods_exist(self, collector):
        """Test that all search methods exist."""
        assert hasattr(collector, 'search_by_location')
        assert hasattr(collector, 'search_plans')
        assert hasattr(collector, 'get_plan_details')
        assert hasattr(collector, 'get_lookup_data')

    def test_lookup_data_methods_exist(self, collector):
        """Test that lookup data methods exist."""
        assert hasattr(collector, 'get_lookup_data')
        assert hasattr(collector, 'search_lookup')
        assert hasattr(collector, 'get_all_lookup_tables')


class TestMavatCollectorDataPipelineIntegration:
    """Integration tests for MavatCollector in DataPipeline."""

    def test_data_pipeline_import(self):
        """Test that DataPipeline can import MavatCollector."""
        try:
            from orchestration.data_pipeline import DataPipeline, MavatCollector
            assert True
        except ImportError:
            pytest.fail("Failed to import DataPipeline or MavatCollector")

    def test_data_pipeline_has_mavat_collector(self):
        """Test that DataPipeline includes MavatCollector."""
        try:
            from orchestration.data_pipeline import DataPipeline
            
            # Create pipeline instance
            pipeline = DataPipeline()
            
            # Check if mavat collector is included
            assert hasattr(pipeline, 'mavat'), "MavatCollector not found in pipeline"
            
            # Check if it's the right type
            from mavat.collector.mavat_collector import MavatCollector
            assert isinstance(pipeline.mavat, MavatCollector), "Pipeline mavat is not MavatCollector"
            
        except Exception as e:
            pytest.fail(f"DataPipeline integration test failed: {e}")

    def test_collector_methods_in_pipeline(self):
        """Test that the collector in pipeline has required methods."""
        try:
            from orchestration.data_pipeline import DataPipeline
            
            pipeline = DataPipeline()
            collector = pipeline.mavat
            
            # Check required methods exist
            required_methods = ['collect', 'search_by_location', 'search_plans', 'get_lookup_data']
            for method in required_methods:
                assert hasattr(collector, method), f"Method {method} not found in pipeline collector"
                assert callable(getattr(collector, method)), f"Method {method} is not callable"
                
        except Exception as e:
            pytest.fail(f"Collector methods test failed: {e}")


class TestMavatCollectorErrorHandling:
    """Test error handling in MavatCollector."""

    @pytest.fixture
    def mock_collector(self):
        """Create a collector with mocked client for error testing."""
        with patch('mavat.collector.mavat_collector.MavatAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client.search_by_block_parcel.side_effect = Exception("Test error")
            mock_client.search_by_location.side_effect = Exception("Test error")
            mock_client.search_plans.side_effect = Exception("Test error")
            mock_client.get_lookup_data.side_effect = Exception("Test error")
            mock_client_class.return_value = mock_client
            
            collector = MavatCollector(client=mock_client)
            yield collector

    def test_collect_method_error_handling(self, mock_collector):
        """Test that collect method handles errors gracefully."""
        # Should return empty list on error, not raise exception
        result = mock_collector.collect("666", "1")
        assert result == []

    def test_search_by_location_error_handling(self, mock_collector):
        """Test that search_by_location handles errors gracefully."""
        result = mock_collector.search_by_location("תל אביב")
        assert result == []

    def test_search_plans_error_handling(self, mock_collector):
        """Test that search_plans handles errors gracefully."""
        result = mock_collector.search_plans("test")
        assert result == []

    def test_get_lookup_data_error_handling(self, mock_collector):
        """Test that get_lookup_data handles errors gracefully."""
        result = mock_collector.get_lookup_data("cities")
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__])
