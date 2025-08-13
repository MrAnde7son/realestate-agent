"""
GIS module for real estate data collection and analysis.
"""

from .gis_client import TelAvivGS
from .parse_zchuyot import parse_zchuyot, parse_html_privilege_page

__all__ = [
    "TelAvivGS",
    "parse_zchuyot", 
    "parse_html_privilege_page"
]
