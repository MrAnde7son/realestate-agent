"""Utilities for computing distance from a location to the sea coastline.

The calculator converts coordinates to the national ITM projection so that
distances are returned in meters. A lightweight, pre-defined coastline outline
is included to avoid external data dependencies while still providing
reasonable proximity estimates for Israeli properties.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence, Tuple

from govmap.api_client import wgs84_to_itm
from shapely.geometry import LineString, MultiLineString, Point


DEFAULT_COASTLINES_WGS84: Sequence[Sequence[Tuple[float, float]]] = (
    # Mediterranean shoreline (south to north)
    (
        (34.23, 31.22),
        (34.35, 31.5),
        (34.55, 31.8),
        (34.72, 32.1),
        (34.77, 32.3),
        (34.8, 32.5),
        (34.95, 32.8),
        (35.02, 33.05),
        (34.99, 33.1),
    ),
    # Gulf of Eilat (Red Sea)
    (
        (34.91, 29.45),
        (34.95, 29.55),
        (34.98, 29.7),
    ),
)


@dataclass(frozen=True)
class SeaDistanceCalculator:
    """Calculate distance to the nearest sea coastline in meters."""

    coastlines_wgs84: Sequence[Sequence[Tuple[float, float]]] = DEFAULT_COASTLINES_WGS84

    def __post_init__(self) -> None:
        object.__setattr__(self, "_coastline_geometry", self._build_itm_geometry())

    def _build_itm_geometry(self) -> Optional[MultiLineString | LineString]:
        lines = []
        for coastline in self.coastlines_wgs84:
            try:
                projected: Iterable[Tuple[float, float]] = (
                    wgs84_to_itm(lon, lat) for lon, lat in coastline
                )
                line = LineString(projected)
                if line.length:
                    lines.append(line)
            except Exception:
                # Skip malformed coastlines but keep processing the rest
                continue

        if not lines:
            return None
        if len(lines) == 1:
            return lines[0]
        return MultiLineString(lines)

    def distance_to_sea_meters(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        x_itm: Optional[float] = None,
        y_itm: Optional[float] = None,
    ) -> Optional[float]:
        """Return distance to the closest coastline in meters.

        Coordinates can be provided either in WGS84 (lat/lon) or directly in
        ITM (x/y). The method prefers ITM values when supplied.
        """

        coastline_geometry = getattr(self, "_coastline_geometry", None)
        if coastline_geometry is None:
            return None

        if x_itm is None or y_itm is None:
            if lat is None or lon is None:
                return None
            try:
                x_itm, y_itm = wgs84_to_itm(lon, lat)
            except Exception:
                return None

        try:
            point = Point(x_itm, y_itm)
            return float(point.distance(coastline_geometry))
        except Exception:
            return None

