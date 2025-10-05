"""Tests for the Dekel-style cost estimation service."""

import pytest

from core.services.cost_service import CostService


@pytest.mark.parametrize(
    "area_input,expected_area",
    [
        (150, 150.0),
        ("200", 200.0),
        (" 85.5 ", 85.5),
    ],
)
def test_estimate_build_cost_parses_area(area_input, expected_area):
    service = CostService()

    estimate = service.estimate_build_cost(
        {
            "area_m2": area_input,
            "scope": ["shell"],
            "region": "CENTER",
            "quality": "standard",
        }
    )

    assert estimate["metadata"]["area_m2"] == pytest.approx(expected_area)
    assert estimate["totals"]["base_cost"] > 0


def test_estimate_build_cost_handles_invalid_area():
    service = CostService()

    estimate = service.estimate_build_cost(
        {
            "area_m2": "not-a-number",
            "scope": ["shell"],
            "region": "CENTER",
            "quality": "standard",
        }
    )

    assert estimate["totals"]["base_cost"] == 0
    assert estimate["metadata"]["area_m2"] == 0


def test_estimate_build_cost_unknown_region_fallback():
    service = CostService()

    estimate = service.estimate_build_cost(
        {
            "area_m2": 100,
            "scope": ["shell"],
            "region": "UNKNOWN",
            "quality": "standard",
        }
    )

    assert estimate["metadata"]["region"] == "CENTER"
    assert estimate["totals"]["base_cost"] > 0
