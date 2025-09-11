# -*- coding: utf-8 -*-
"""
GovMap collector that plugs into your existing orchestration layer.

Usage
-----
from govmap import GovMapClient
from orchestration.collectors.govmap_collector import GovMapCollector

collector = GovMapCollector(GovMapClient())
# Example (re-using TelAvivGS geocoder if available):
# x,y = TelAvivGS().get_address_coordinates("רוזוב", 14)
# data = collector.collect(x=x, y=y)
"""
from typing import Any, Dict, Optional

from .base_collector import BaseCollector
from govmap.api_client import GovMapClient


class GovMapCollector(BaseCollector):
    """Collects national-level parcel + nearby layers from GovMap OpenData."""

    def __init__(self, client: Optional[GovMapClient] = None) -> None:
        self.client = client or GovMapClient()

    def collect(
        self,
        *,
        x: float,
        y: float,
        parcel_layer: str = "opendata:PARCEL_ALL",
        extra_layers: Optional[list[str]] = None,
        buffer_m: int = 150,
    ) -> Dict[str, Any]:
        """Collect parcel at point + selected nearby layers.

        Parameters
        ----------
        x, y : EPSG:2039 coordinates of the target point.
        parcel_layer : WFS/WMS layer name for parcels.
        extra_layers : optional list of layer names to query with WMS GetFeatureInfo around the point.
        buffer_m : search buffer for WMS queries.
        """
        out: Dict[str, Any] = {
            "x": x,
            "y": y,
            "parcel": None,
            "nearby": {},
        }

        # 1) parcel at point
        parcel = self.client.get_parcel_at_point(x, y, layer=parcel_layer)
        out["parcel"] = parcel

        # 2) nearby layers (risk/amenities/etc.)
        for layer in (extra_layers or []):
            info = self.client.wms_getfeatureinfo(layer=layer, x=x, y=y, buffer_m=buffer_m)
            out["nearby"][layer] = [fi.attributes for fi in info]

        return out

    def validate_parameters(self, **kwargs) -> bool:
        return isinstance(kwargs.get("x"), (int, float)) and isinstance(kwargs.get("y"), (int, float))
