"""Mavat data collector implementation."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from orchestration.collectors.base_collector import BaseCollector
from mavat.scrapers.mavat_selenium_client import MavatSeleniumClient


class MavatCollector(BaseCollector):
    """Wrapper around :class:`MavatSeleniumClient` providing a stable API."""

    def __init__(self, client: Optional[MavatSeleniumClient] = None) -> None:
        self.client = client or MavatSeleniumClient()

    def collect(self, block: str, parcel: str, city: Optional[str] = None) -> List[Dict[str, Any]]:
        """Collect Mavat plans for a given block/parcel.
        
        This method implements the base collect interface and provides
        planning data from the Mavat system.
        
        Parameters
        ----------
        block: str
            Block number for cadastral search.
        parcel: str
            Parcel number for cadastral search.
        city: str, optional
            City name for additional context.
            
        Returns
        -------
        List[Dict[str, Any]]
            A list of plan summaries in consistent format.
        """
        try:
            # Search by block and parcel using Selenium client
            with self.client as client:
                plans = client.search_plans(block=block, parcel=parcel, city=city)
                
                # Convert to consistent format
                formatted_plans = []
                for plan in plans:
                    formatted_plans.append({
                        "plan_id": plan.plan_id,
                        "title": plan.title,
                        "status": plan.status,
                        "authority": plan.authority,
                        "entity_number": plan.entity_number,
                        "approval_date": plan.approval_date,
                        "status_date": plan.status_date,
                        "raw": plan.raw
                    })
                
                return formatted_plans
        except Exception:
            return []

    def search_by_location(self, city: str, district: Optional[str] = None, 
                          street: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for plans by location criteria.
        
        Parameters
        ----------
        city: str
            City name for location-based search.
        district: str, optional
            District name for location-based search.
        street: str, optional
            Street name for location-based search.
        limit: int, optional
            Maximum number of plans to return. Defaults to 20.
            
        Returns
        -------
        List[Dict[str, Any]]
            A list of plan summaries in consistent format.
        """
        try:
            with self.client as client:
                plans = client.search_plans(city=city, district=district, 
                                           street=street, limit=limit)
                
                # Convert to consistent format
                formatted_plans = []
                for plan in plans:
                    formatted_plans.append({
                        "plan_id": plan.plan_id,
                        "title": plan.title,
                        "status": plan.status,
                        "authority": plan.authority,
                        "entity_number": plan.entity_number,
                        "approval_date": plan.approval_date,
                        "status_date": plan.status_date,
                        "raw": plan.raw
                    })
                
                return formatted_plans
        except Exception:
            return []

    def search_plans(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for plans using free text query.
        
        Parameters
        ----------
        query: str
            Free text to search for in plan names.
        limit: int, optional
            Maximum number of plans to return. Defaults to 20.
            
        Returns
        -------
        List[Dict[str, Any]]
            A list of plan summaries in consistent format.
        """
        try:
            with self.client as client:
                plans = client.search_plans(query=query, limit=limit)
                
                # Convert to consistent format
                formatted_plans = []
                for plan in plans:
                    formatted_plans.append({
                        "plan_id": plan.plan_id,
                        "title": plan.title,
                        "status": plan.status,
                        "authority": plan.authority,
                        "entity_number": plan.entity_number,
                        "approval_date": plan.approval_date,
                        "status_date": plan.status_date,
                        "raw": plan.raw
                    })
                
                return formatted_plans
        except Exception as e:
            # Log the error for debugging
            import logging
            logging.error(f"MavatCollector.search_plans failed: {e}")
            return []

    def get_plan_details(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed information for a single plan.
        
        Parameters
        ----------
        plan_id: str
            Identifier of the plan to retrieve.
            
        Returns
        -------
        Optional[Dict[str, Any]]
            A dictionary containing plan details and raw payloads,
            or None if the plan is not found.
        """
        try:
            with self.client as client:
                plan = client.get_plan_details(plan_id)
                
                return {
                    "plan_id": plan.plan_id,
                    "plan_name": plan.plan_name,
                    "status": plan.status,
                    "authority": plan.authority,
                    "jurisdiction": plan.jurisdiction,
                    "last_update": plan.last_update,
                    "entity_number": plan.entity_number,
                    "approval_date": plan.approval_date,
                    "status_date": plan.status_date,
                    "raw": plan.raw
                }
        except Exception:
            return None

    def get_plan_attachments(self, plan_id: str, entity_name: str) -> List[Dict[str, Any]]:
        """Get attachments for a specific plan.
        
        Parameters
        ----------
        plan_id: str
            The unique identifier of the plan.
        entity_name: str
            The entity name for constructing the attachment URL.
            
        Returns
        -------
        List[Dict[str, Any]]
            A list of attachment information.
        """
        try:
            # Selenium client doesn't have get_plan_attachments method yet
            # For now, return empty list - can be implemented later
            return []
        except Exception:
            return []

    def get_lookup_data(self, data_type: str = "cities", force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get lookup data for various planning entities.
        
        Parameters
        ----------
        data_type: str
            Type of lookup data to retrieve. Options: "cities", "districts", 
            "streets", "plan_areas", "authorities", "plan_types", "statuses".
        force_refresh: bool, optional
            Whether to force refresh the cache. Defaults to False.
            
        Returns
        -------
        List[Dict[str, Any]]
            A list of lookup items in consistent format.
        """
        try:
            # Selenium client doesn't have lookup methods yet
            # Return empty list for now - can be implemented later
            return []
        except Exception:
            return []

    def search_lookup(self, search_text: str, table_type: Optional[str] = None, 
                     force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Search lookup tables by text.
        
        Parameters
        ----------
        search_text: str
            Text to search for in lookup tables.
        table_type: str, optional
            Specific table type to search (4=districts, 5=cities, 6=plan_areas, 
            7=streets, 8=authorities, 9=plan_types, 10=statuses).
        force_refresh: bool, optional
            Whether to force refresh the cache. Defaults to False.
            
        Returns
        -------
        List[Dict[str, Any]]
            A list of matching lookup items in consistent format.
        """
        try:
            # Selenium client doesn't have lookup methods yet
            # Return empty list for now - can be implemented later
            return []
        except Exception:
            return []

    def get_all_lookup_tables(self, force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available lookup tables.
        
        Parameters
        ----------
        force_refresh: bool, optional
            Whether to force refresh the cache. Defaults to False.
            
        Returns
        -------
        Dict[str, List[Dict[str, Any]]]
            A dictionary containing all lookup tables in consistent format.
        """
        try:
            # Selenium client doesn't have lookup methods yet
            # Return empty dict for now - can be implemented later
            return {}
        except Exception:
            return {}

    def validate_parameters(self, **kwargs) -> bool:
        """Validate the parameters for Mavat collection."""
        required_params = ['block', 'parcel']
        return all(param in kwargs for param in required_params)
