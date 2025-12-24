"""
GIS module for real estate data collection and analysis.
"""

from .gis_client import TelAvivGS
from .parse_zchuyot import parse_zchuyot

__all__ = [
    "TelAvivGS",
    "parse_zchuyot",
]
