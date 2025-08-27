"""Data pipeline for collecting and processing real estate data from multiple sources."""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from .collectors import (
    BaseCollector,
    Yad2Collector,
    GISCollector, 
    GovCollector,
    RamiCollector
)
from mavat.collector.mavat_collector import MavatCollector

logger = logging.getLogger(__name__)


class DataPipeline:
    """Orchestrates data collection from multiple sources."""
    
    def __init__(
        self,
        yad2: Optional[Yad2Collector] = None,
        gis: Optional[GISCollector] = None,
        gov: Optional[GovCollector] = None,
        rami: Optional[RamiCollector] = None,
        mavat: Optional[MavatCollector] = None,
        db_session=None
    ) -> None:
        """Initialize the data pipeline with collectors."""
        self.yad2 = yad2 or Yad2Collector()
        self.gis = gis or GISCollector()
        self.gov = gov or GovCollector()
        self.rami = rami or RamiCollector()
        self.mavat = mavat or MavatCollector()
        self.db_session = db_session
        
        # Validate all collectors implement the required interface
        self._validate_collectors()
    
    def _validate_collectors(self) -> None:
        """Validate that all collectors implement the required interface."""
        collectors = [self.yad2, self.gis, self.gov, self.rami, self.mavat]
        for collector in collectors:
            if not isinstance(collector, BaseCollector):
                raise TypeError(f"Collector {collector} must inherit from BaseCollector")
    
    def run(self, address: str, house_number: int, max_pages: int = 1) -> List[int]:
        """Run the data pipeline for a given address."""
        logger.info(f"Starting data pipeline for {address} {house_number}")
        
        # Get coordinates from address
        try:
            x, y = self.gis.geocode(address, house_number)
        except Exception as e:
            logger.warning(f"Failed to geocode address: {e}")
            x, y = 0.0, 0.0
        
        # Get block and parcel from GIS data
        gis_data = self.gis.collect(x, y)
        block, parcel = self.gis.extract_block_parcel(gis_data)
        
        # Collect data from all sources
        results = []
        
        # Collect from Yad2
        try:
            yad2_data = self.yad2.collect(address=address, max_pages=max_pages)
            if yad2_data:
                results.extend(yad2_data)
        except Exception as e:
            logger.warning(f"Failed to collect Yad2 data: {e}")
        
        # Collect from GIS (already collected above)
        if gis_data:
            results.append({"source": "gis", "data": gis_data})
        
        # Collect from Government sources
        try:
            gov_data = self.gov.collect(block=block, parcel=parcel, address=address)
            if gov_data:
                results.append({"source": "gov", "data": gov_data})
        except Exception as e:
            logger.warning(f"Failed to collect government data: {e}")
        
        # Collect from Rami
        try:
            rami_data = self.rami.collect(block=block, parcel=parcel)
            if rami_data:
                results.append({"source": "rami", "data": rami_data})
        except Exception as e:
            logger.warning(f"Failed to collect RAMI data: {e}")
        
        # Collect from Mavat
        try:
            mavat_plans = self.mavat.collect(block, parcel)
            if mavat_plans:
                results.append({"source": "mavat", "data": mavat_plans})
        except Exception as e:
            logger.warning(f"Failed to collect Mavat data: {e}")
        
        logger.info(f"Data pipeline completed. Found {len(results)} results.")
        return results
    
    def _parse_address(self, address: str, house_number: int) -> tuple[str, str]:
        """Parse address to extract block and parcel numbers."""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated address parsing
        return "1", "1"  # Placeholder values
    
    def _add_source_record(self, session, listing_id: int, source: str, data: List[Dict[str, Any]]) -> None:
        """Add source record to database."""
        if not self.db_session:
            return
            
        # Implementation would go here
        logger.info(f"Adding {len(data)} records from {source} for listing {listing_id}")
