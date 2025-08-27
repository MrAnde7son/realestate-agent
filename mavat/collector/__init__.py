"""Data collectors for Mavat.

This subpackage exposes classes and helpers for integrating the
``MavatScraper`` into a data pipeline.  Collectors wrap the raw
scraper and provide a stable interface for orchestration modules.
"""

from .mavat_collector import MavatCollector

__all__ = ["MavatCollector"]