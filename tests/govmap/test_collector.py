# -*- coding: utf-8 -*-
from unittest import mock

from govmap.api_client import GovMapClient
from orchestration.collectors.govmap_collector import GovMapCollector


def test_collector_initialization():
    """Test collector initialization with default client"""
    collector = GovMapCollector()
    assert isinstance(collector.client, GovMapClient)


def test_collector_initialization_custom_client():
    """Test collector initialization with custom client"""
    custom_client = GovMapClient()
    collector = GovMapCollector(client=custom_client)
    assert collector.client is custom_client


def test_collect_success():
    """Test successful data collection using address autocomplete."""
    collector = GovMapCollector()

    autocomplete_payload = {
        "results": [
            {
                "shape": "POINT(100.0 200.0)",
            }
        ]
    }
    parcel_data = {"parcel_id": "12345", "area": 500.0}

    with mock.patch.object(
        collector.client,
        "autocomplete",
        return_value=autocomplete_payload,
    ) as mock_autocomplete, mock.patch.object(
        collector.client,
        "get_parcel_data",
        return_value=parcel_data,
    ) as mock_get_parcel:

        result = collector.collect(address="Example Address")

        mock_autocomplete.assert_called_once_with("Example Address")
        mock_get_parcel.assert_called_once_with(100.0, 200.0)

        assert result["address"] == "Example Address"
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert result["api_data"]["autocomplete"] == autocomplete_payload
        assert result["api_data"]["parcel"] == parcel_data


def test_collect_with_parcel_failure():
    """Test collection when parcel data retrieval fails."""
    collector = GovMapCollector()

    autocomplete_payload = {
        "results": [
            {
                "shape": "POINT(100.0 200.0)",
            }
        ]
    }

    with mock.patch.object(
        collector.client,
        "autocomplete",
        return_value=autocomplete_payload,
    ), mock.patch.object(
        collector.client,
        "get_parcel_data",
        side_effect=Exception("API Error"),
    ):

        result = collector.collect(address="Example Address")

        assert result["address"] == "Example Address"
        assert result["x"] == 100.0
        assert result["y"] == 200.0
        assert result["api_data"]["autocomplete"] == autocomplete_payload
        assert "parcel" not in result["api_data"]


def test_collect_without_coordinates():
    """Ensure collection handles autocomplete results without coordinates."""
    collector = GovMapCollector()

    autocomplete_payload = {"results": []}

    with mock.patch.object(
        collector.client,
        "autocomplete",
        return_value=autocomplete_payload,
    ):
        result = collector.collect(address="Unknown Address")

    assert result["address"] == "Unknown Address"
    assert "x" not in result
    assert "y" not in result
    assert result["api_data"]["autocomplete"] == autocomplete_payload


def test_validate_parameters_valid():
    """Test parameter validation with valid parameters."""
    collector = GovMapCollector()
    assert collector.validate_parameters(address="Example Address") is True


def test_validate_parameters_invalid():
    """Test parameter validation with invalid parameters."""
    collector = GovMapCollector()
    assert collector.validate_parameters() is False
    assert collector.validate_parameters(address=None) is False
    assert collector.validate_parameters(address=123) is False
