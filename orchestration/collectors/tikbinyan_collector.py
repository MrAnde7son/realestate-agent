"""Collectors for municipal tikbinyan (building files) portals."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from handasa.tikbinyan_client import (
    BatYamTikbinyanClient,
    HerzliyaTikbinyanClient,
    RamatGanTikbinyanClient,
    TikbinyanClient,
)

from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class TikbinyanCollector(BaseCollector):
    """Base collector for tikbinyan portals."""

    def __init__(self, client: TikbinyanClient) -> None:
        """Initialize the collector with a tikbinyan client."""
        self.client = client

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Collect building info and permits from tikbinyan portal.
        
        This method ensures comprehensive data collection by:
        - Collecting all building documents (permits, plans, requests, drawings)
        - Trying multiple search methods when possible (block/parcel, address)
        - Merging and deduplicating results from different sources
        - Collecting from all available endpoints (GetGushFile, GetUnifiedFile, building pages)
        
        Args:
            location: Location query with block, parcel,
            **kwargs: Additional parameters (address, etc.)
            
        Returns:
            List of building info and permit documents with comprehensive data including:
            - Building permits (היתר בנייה)
            - Building plans (תכניות בנייה)
            - Requests (בקשות)
            - Technical drawings (מפות מדידה, תכניות אדריכליות)
            - All other relevant building documents
        """
        query = ensure_location_query(location)
        
        # Try block/parcel
        block = query.block
        parcel = query.parcel
        
        # Try address
        address = kwargs.get("address")
        if not address and query.street:
            address_parts = [query.street]
            if query.house_number:
                address_parts.append(str(query.house_number))
            address = " ".join(address_parts)
        
        all_documents = []
        seen_doc_ids = set()
        
        try:
            documents = self.client.get_building_info(
                block=str(block) if block else None,
                parcel=str(parcel) if parcel else None,
                address=address,
            )
            
            # Deduplicate documents by external_id, request_num, or permission_num
            for doc in documents:
                doc_id = (
                    doc.get("external_id") 
                    or doc.get("request_num") 
                    or doc.get("permission_num")
                    or f"{doc.get('building_id')}_{doc.get('title')}_{doc.get('document_date')}"
                )
                if doc_id and doc_id not in seen_doc_ids:
                    seen_doc_ids.add(doc_id)
                    all_documents.append(doc)
            
            # Log collection summary with document type breakdown
            if all_documents:
                doc_types = {}
                doc_categories = {}
                building_ids = set()
                
                for doc in all_documents:
                    # Track document types
                    doc_type = doc.get("document_type", "other")
                    doc_category = doc.get("document_category", "document")
                    key = f"{doc_category}:{doc_type}"
                    doc_types[key] = doc_types.get(key, 0) + 1
                    doc_categories[doc_category] = doc_categories.get(doc_category, 0) + 1
                    
                    # Track building IDs
                    bid = doc.get("building_id")
                    if bid:
                        building_ids.add(bid)
                
                logger.info(
                    "Collected %d documents from tikbinyan for %d building(s): %s. "
                    "Categories: %s",
                    len(all_documents),
                    len(building_ids),
                    ", ".join(f"{k}({v})" for k, v in sorted(doc_types.items())),
                    ", ".join(f"{k}({v})" for k, v in sorted(doc_categories.items()))
                )
            else:
                logger.warning(
                    "No documents found for block=%s parcel=%s address=%s",
                    block,
                    parcel,
                    address,
                )
            
            return all_documents
            
        except Exception:
            logger.exception(
                "Failed to fetch tikbinyan data for block=%s parcel=%s address=%s",
                block,
                parcel,
                address,
            )
            raise

    def validate_parameters(self, **kwargs) -> bool:
        """Validate parameters for collection."""
        location = ensure_location_query(kwargs.get("location"))
        block = location.block
        address = kwargs.get("address") or location.street
        
        return bool(block or address)


class BatYamTikbinyanCollector(TikbinyanCollector):
    """Collector for Bat Yam tikbinyan portal."""

    def __init__(self, client: Optional[BatYamTikbinyanClient] = None) -> None:
        super().__init__(client or BatYamTikbinyanClient())


class HerzliyaTikbinyanCollector(TikbinyanCollector):
    """Collector for Herzliya tikbinyan portal."""

    def __init__(self, client: Optional[HerzliyaTikbinyanClient] = None) -> None:
        super().__init__(client or HerzliyaTikbinyanClient())


class RamatGanTikbinyanCollector(TikbinyanCollector):
    """Collector for Ramat Gan tikbinyan portal."""

    def __init__(self, client: Optional[RamatGanTikbinyanClient] = None) -> None:
        super().__init__(client or RamatGanTikbinyanClient())


__all__ = [
    "TikbinyanCollector",
    "BatYamTikbinyanCollector",
    "HerzliyaTikbinyanCollector",
    "RamatGanTikbinyanCollector",
]


if __name__ == "__main__":
    # Example usage
    collector = BatYamTikbinyanCollector()
    result = collector.collect(location=LocationQuery(street="הצפירה", house_number=8, city="בת ים"))
    print(result)

