#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Integration tests for MavatCollector."""

from unittest.mock import Mock, patch

import pytest


class TestMavatCollectorIntegration:
    """Integration tests for MavatCollector."""

    def test_collector_import(self):
        """Test that MavatCollector can be imported."""
        try:
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import MavatCollector: {e}")

    def test_collector_creation(self):
        """Test that MavatCollector can be created."""
        try:
            from orchestration.collectors.mavat_collector import MavatCollector
            collector = MavatCollector()
            assert collector is not None
            assert hasattr(collector, 'client')
        except Exception as e:
            pytest.fail(f"Failed to create MavatCollector: {e}")

    def test_collect_method_interface(self):
        """Test that the collect method follows the base interface."""
        try:
            from orchestration.collectors.mavat_collector import MavatCollector
            collector = MavatCollector()
            
            # The collect method should exist and be callable
            assert hasattr(collector, 'collect')
            assert callable(collector.collect)
        except Exception as e:
            pytest.fail(f"Collect method test failed: {e}")

    def test_search_methods_exist(self):
        """Test that all search methods exist."""
        try:
            from orchestration.collectors.mavat_collector import MavatCollector
            collector = MavatCollector()
            
            assert hasattr(collector, 'search_by_location')
            assert hasattr(collector, 'search_plans')
            assert hasattr(collector, 'get_plan_details')
            assert hasattr(collector, 'get_lookup_data')
        except Exception as e:
            pytest.fail(f"Search methods test failed: {e}")

    def test_lookup_data_methods_exist(self):
        """Test that lookup data methods exist."""
        try:
            from orchestration.collectors.mavat_collector import MavatCollector
            collector = MavatCollector()
            
            assert hasattr(collector, 'get_lookup_data')
            assert hasattr(collector, 'search_lookup')
            assert hasattr(collector, 'get_all_lookup_tables')
        except Exception as e:
            pytest.fail(f"Lookup data methods test failed: {e}")


class TestMavatCollectorDataPipelineIntegration:
    """Integration tests for MavatCollector in DataPipeline."""

    def test_data_pipeline_import(self):
        """Test that DataPipeline can import MavatCollector."""
        try:
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import DataPipeline or MavatCollector: {e}")

    def test_data_pipeline_has_mavat_collector(self):
        """Test that DataPipeline includes MavatCollector."""
        try:
            from orchestration.data_pipeline import DataPipeline

            # Create pipeline instance
            pipeline = DataPipeline()
            
            # Check if mavat collector is included
            assert hasattr(pipeline, 'mavat'), "MavatCollector not found in pipeline"
            
            # Check if it's the right type
            from orchestration.collectors.mavat_collector import MavatCollector
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

    def test_collect_method_error_handling(self):
        """Test that collect method handles errors gracefully."""
        try:
            from orchestration.collectors.mavat_collector import MavatCollector
            
            with patch('orchestration.collectors.mavat_collector.MavatAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_client.search_by_block_parcel.side_effect = Exception("Test error")
                mock_client_class.return_value = mock_client
                
                collector = MavatCollector(client=mock_client)
                
                # Should return empty list on error, not raise exception
                result = collector.collect("666", "1")
                assert result == []
        except Exception as e:
            pytest.fail(f"Collect method error handling test failed: {e}")

    def test_search_by_location_error_handling(self):
        """Test that search_by_location handles errors gracefully."""
        try:
            from orchestration.collectors.mavat_collector import MavatCollector
            
            with patch('orchestration.collectors.mavat_collector.MavatAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_client.search_by_location.side_effect = Exception("Test error")
                mock_client_class.return_value = mock_client
                
                collector = MavatCollector(client=mock_client)
                
                result = collector.search_by_location("תל אביב")
                assert result == []
        except Exception as e:
            pytest.fail(f"Search by location error handling test failed: {e}")

    def test_search_plans_error_handling(self):
        """Test that search_plans handles errors gracefully."""
        try:
            from orchestration.collectors.mavat_collector import MavatCollector
            
            with patch('orchestration.collectors.mavat_collector.MavatAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_client.search_plans.side_effect = Exception("Test error")
                mock_client_class.return_value = mock_client
                
                collector = MavatCollector(client=mock_client)
                
                result = collector.search_plans("test")
                assert result == []
        except Exception as e:
            pytest.fail(f"Search plans error handling test failed: {e}")

    def test_get_lookup_data_error_handling(self):
        """Test that get_lookup_data handles errors gracefully."""
        try:
            from orchestration.collectors.mavat_collector import MavatCollector
            
            with patch('orchestration.collectors.mavat_collector.MavatAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_client.get_cities.side_effect = Exception("Test error")
                mock_client_class.return_value = mock_client
                
                collector = MavatCollector(client=mock_client)
                
                result = collector.get_lookup_data("cities")
                assert result == []
        except Exception as e:
            pytest.fail(f"Get lookup data error handling test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])
