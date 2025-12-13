import datetime

import pytest

from govmap.api_client import wgs84_to_itm
from orchestration.pipeline.asset_enrichment import _update_distance_to_sea
from orchestration.pipeline.sea_distance import SeaDistanceCalculator


class FakeAsset:
    def __init__(self, lat=None, lon=None):
        self.lat = lat
        self.lon = lon
        self.meta = {}
        self.properties = {}

    def set_property(self, key, value, source=None, url=None, meta_prefix=""):
        self.properties[key] = value
        meta_key = f"{meta_prefix}_{key}" if meta_prefix else key
        self.meta[meta_key] = {
            "value": value,
            "source": source,
            "url": url,
            "fetched_at": datetime.datetime.now().isoformat(),
        }


def test_distance_zero_on_coastline_segment():
    calculator = SeaDistanceCalculator(coastlines_wgs84=[[(34.0, 30.0), (34.0, 31.0)]])
    assert calculator.distance_to_sea_meters(lat=30.5, lon=34.0) == pytest.approx(0.0, abs=10)


def test_distance_uses_itm_coordinates_when_available():
    calculator = SeaDistanceCalculator(coastlines_wgs84=[[(34.0, 30.0), (34.0, 31.0)]])
    x_itm, y_itm = wgs84_to_itm(34.02, 30.5)
    distance = calculator.distance_to_sea_meters(x_itm=x_itm, y_itm=y_itm)
    assert distance > 0


def test_update_distance_to_sea_sets_meta_and_property():
    calculator = SeaDistanceCalculator(coastlines_wgs84=[[(34.0, 30.0), (34.0, 31.0)]])
    asset = FakeAsset(lat=30.5, lon=34.01)

    _update_distance_to_sea(asset, {}, calculator=calculator)

    assert "distance_to_beach_m" in asset.meta
    assert asset.properties.get("distanceToSeaM")
