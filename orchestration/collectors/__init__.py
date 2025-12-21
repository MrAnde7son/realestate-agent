"""Data collectors package for the realestate-agent project."""

from .base_collector import BaseCollector
from .gis_collector import GISCollector
from .municipal_gis import (
    MultiCityGISCollector,
    MunicipalGisAdapter,
    TelAvivMunicipalGisAdapter,
)
from .handasa_collector import HandasaCollector
from .tikbinyan_collector import (
    BatYamTikbinyanCollector,
    HerzliyaTikbinyanCollector,
    RamatGanTikbinyanCollector,
    TikbinyanCollector,
)
from .tikbinyan_adapter import (
    MultiCityTikbinyanCollector,
    TikbinyanAdapter,
    BatYamTikbinyanAdapter,
    HerzliyaTikbinyanAdapter,
    RamatGanTikbinyanAdapter,
)
from .gov_collector import GovCollector
from .govmap_collector import GovMapCollector
from .madlan_collector import MadlanCollector
from .mavat_collector import MavatCollector
from .michrazim_collector import MichrazimCollector
from .rami_collector import RamiCollector
from .yad2_collector import Yad2Collector

__all__ = [
    'BaseCollector',
    'Yad2Collector', 
    'GISCollector',
    'MunicipalGisAdapter',
    'TelAvivMunicipalGisAdapter',
    'MultiCityGISCollector',
    'HandasaCollector',
    'TikbinyanCollector',
    'BatYamTikbinyanCollector',
    'HerzliyaTikbinyanCollector',
    'RamatGanTikbinyanCollector',
    'TikbinyanAdapter',
    'MultiCityTikbinyanCollector',
    'BatYamTikbinyanAdapter',
    'HerzliyaTikbinyanAdapter',
    'RamatGanTikbinyanAdapter',
    'GovCollector',
    'GovMapCollector',
    'MadlanCollector',
    'MavatCollector',
    'MichrazimCollector',
    'RamiCollector',
]
