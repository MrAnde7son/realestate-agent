# -*- coding: utf-8 -*-
"""
Real Estate Transactions module for fetching and analyzing comparable transactions from data.gov.il.

This module provides functionality to search for real estate transactions from government datasets,
process and filter them by location, date, and area, and calculate comparative statistics.
"""

from __future__ import annotations

import math
import time
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from pyproj import Transformer
from dateutil import parser as dtp

from .constants import CKAN_BASE_URL, USER_AGENT, SEARCH_TIMEOUT


class RealEstateTransactions:
    """
    A class for fetching and analyzing comparable real estate transactions from data.gov.il.
    
    This class provides methods to search for transaction data, process records,
    and calculate comparative statistics for real estate appraisal purposes.
    """
    
    def __init__(self):
        """Initialize the real estate transactions handler."""
        self.headers = {"User-Agent": USER_AGENT}
        self._trans_2039_4326 = Transformer.from_crs(2039, 4326, always_xy=True)
    
    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in meters using haversine formula."""
        R = 6_371_000.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dlat = p2 - p1
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    @staticmethod
    def _norm_field(rec: Dict[str, Any], keys: List[str]):
        """Extract first non-empty value from record using list of possible keys."""
        for k in keys:
            if k in rec and rec[k] not in (None, ""):
                return rec[k]
        return None

    @staticmethod
    def _try_date(s) -> Optional[str]:
        """Parse date string and return in YYYY-MM-DD format."""
        if not s:
            return None
        try:
            return dtp.parse(str(s), dayfirst=True, yearfirst=False, fuzzy=True).strftime("%Y-%m-%d")
        except Exception:
            return None

    @staticmethod
    def _to_float(x):
        """Convert value to float, handling commas."""
        try:
            return float(str(x).replace(",", ""))
        except Exception:
            return None

    @staticmethod
    def _median(vals: List[Optional[float]]) -> Optional[float]:
        """Calculate median of a list of values, ignoring None values."""
        vals = sorted([v for v in vals if v is not None])
        if not vals:
            return None
        n = len(vals)
        m = n // 2
        return vals[m] if n % 2 else (vals[m - 1] + vals[m]) / 2

    def _process_transaction_record(
        self,
        r: Dict[str, Any],
        subj_lat: float,
        subj_lon: float,
        date_from: Optional[str],
        date_to: Optional[str],
        target_area: Optional[float],
    ) -> Optional[Dict[str, Any]]:
        """Process and filter a transaction record from data.gov.il."""
        city = self._norm_field(r, ["עיר", "ישוב", "City"])
        if city and "תל" not in str(city):
            return None
        
        street_r = self._norm_field(r, ["רחוב", "Street"])
        house_r = self._norm_field(r, ["מספר_בית", "House_Number", "מספר בית"])
        
        deal_date = self._try_date(
            self._norm_field(r, ["תאריך_עסקה", "תאריך העסקה", "DealDate", "Deal_Date"])
        )
        if date_from and deal_date and deal_date < date_from:
            return None
        if date_to and deal_date and deal_date > date_to:
            return None
        
        price = self._to_float(
            self._norm_field(r, ["שווי_עסקה", "שווי העסקה", "DealAmount", "Deal_Amount"])
        )
        rooms = self._to_float(self._norm_field(r, ["מספר_חדרים", "מספר חדרים", "Rooms"]))
        area = self._to_float(self._norm_field(r, ["שטח_דירה", "שטח דירה", "BuiltArea", "Area"]))
        
        # Handle coordinates
        lon_r = self._to_float(self._norm_field(r, ["lon", "LONG", "Long", "longitude"]))
        lat_r = self._to_float(self._norm_field(r, ["lat", "LAT", "Lat", "latitude"]))
        if not (lat_r and lon_r):
            X = self._to_float(self._norm_field(r, ["X", "itm_x", "ITM_X"]))
            Y = self._to_float(self._norm_field(r, ["Y", "itm_y", "ITM_Y"]))
            if X and Y:
                lon_r, lat_r = self._trans_2039_4326.transform(X, Y)
        
        # Calculate distance
        dist_m = (
            self._haversine(subj_lat, subj_lon, lat_r, lon_r)
            if (lat_r and lon_r)
            else None
        )
        
        # Calculate price per sqm
        price_sqm = (price / area) if (price and area and area > 0) else None
        
        # Filter by area if specified
        if target_area and area:
            if not (0.8 * target_area <= area <= 1.2 * target_area):
                return None
        
        return {
            "deal_date": deal_date,
            "price": price,
            "price_sqm": price_sqm,
            "rooms": rooms,
            "area_sqm": area,
            "city": city,
            "street": street_r,
            "house_number": house_r,
            "lat": lat_r,
            "lon": lon_r,
            "distance_m": dist_m,
            "raw": r,
        }

    def find_transactions_resource(self) -> Dict[str, Any]:
        """Find the best real estate transactions resource on data.gov.il."""
        queries = [
            'עסקאות נדל"ן רשות המסים',
            "real estate transactions israel tax authority",
            "עסקאות מקרקעין",
        ]
        best_csv: Optional[Dict[str, Any]] = None
        
        for q in queries:
            r = requests.get(
                f"{CKAN_BASE_URL}/package_search", 
                params={"q": q, "rows": 25}, 
                headers=self.headers,
                timeout=30
            )
            r.raise_for_status()
            
            for pkg in r.json().get("result", {}).get("results", []):
                for res in pkg.get("resources", []):
                    name = (res.get("name") or "") + " " + (res.get("description") or "")
                    fmt = (res.get("format") or "").lower()
                    if not re.search(r"(עסקאות|transactions|מקרקעין|נדל)", name):
                        continue
                    if res.get("datastore_active"):
                        return res
                    if fmt in ("csv", "excel", "xlsx") and not best_csv:
                        best_csv = res
        
        return best_csv or {}

    def fetch_datastore_records(self, resource_id: str, q: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """Fetch all records from a datastore resource with pagination."""
        out: List[Dict[str, Any]] = []
        offset = 0
        page = min(limit, 32_000)
        
        while True:
            params = {
                "resource_id": resource_id,
                "limit": min(page, limit - len(out)),
                "offset": offset,
            }
            if q:
                params["q"] = q
            
            r = requests.get(
                f"{CKAN_BASE_URL}/datastore_search", 
                params=params, 
                headers=self.headers,
                timeout=60
            )
            r.raise_for_status()
            
            jr = r.json()
            if not jr.get("success"):
                break
            
            recs = jr["result"].get("records", [])
            if not recs:
                break
            
            out.extend(recs)
            if len(out) >= limit or len(recs) < page:
                break
            
            offset += page
            time.sleep(0.3)
        
        return out

    def calculate_statistics(self, comparables: List[Dict[str, Any]], 
                           subject_info: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate statistical summary of comparable transactions."""
        return {
            "count": len(comparables),
            "median_price_sqm": self._median([c["price_sqm"] for c in comparables]),
            "avg_price_sqm": (
                sum([c["price_sqm"] for c in comparables if c["price_sqm"]])
                / max(1, len([c for c in comparables if c["price_sqm"]]))
                if comparables
                else None
            ),
            "median_price": self._median([c["price"] for c in comparables]),
            "avg_price": (
                sum([c["price"] for c in comparables if c["price"]])
                / max(1, len([c for c in comparables if c["price"]]))
                if comparables
                else None
            ),
            "median_area": self._median([c["area_sqm"] for c in comparables]),
            "subject": subject_info,
        }

    def fetch_comparable_transactions(
        self,
        x: float, 
        y: float,
        street: str,
        house: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        target_area: Optional[float] = None,
        limit: int = 2000,
        top: int = 20,
    ) -> Dict[str, Any]:
        """
        Fetch comparable Tel-Aviv real-estate transactions from data.gov.il.

        Locates the active real-estate transactions dataset on data.gov.il 
        and returns basic statistics along with the top-N comparable transactions.
        
        Example:
            # Fetch comparables for הגולן 1, תל אביב (Block 6638, Plot 96)
            transactions = RealEstateTransactions()
            
            result = transactions.fetch_comparable_transactions(
                x=184320.94, y=668548.65,  # EPSG:2039 coordinates
                street="הגולן",
                house=1,
                date_from="2020-01-01",  # Optional: filter by date range
                date_to="2025-12-31",
                target_area=80.0,        # Optional: filter by similar area (±20%)
                top=15                   # Top 15 closest comparables
            )
            
            # Expected output for הגולן 1 area:
            # Based on government data (Ministry of Housing public housing purchases):
            # - Recent transactions (2023-2025): ₪2.1-2.6M for 3-4 room apartments
            # - Price per sqm: ~₪27,000-33,000
            # - Block 6638 has decisive appraiser decisions available
        
        Args:
            x: X coordinate in EPSG:2039
            y: Y coordinate in EPSG:2039
            street: Street name for reference
            house: House number for reference
            date_from: Start date filter (YYYY-MM-DD), optional
            date_to: End date filter (YYYY-MM-DD), optional  
            target_area: Filter by apartment area ±20% tolerance, optional
            limit: Max records to fetch from data.gov.il (default: 2000)
            top: Number of top comparable transactions to return (default: 20)
            
        Returns:
            Dict with 'stats' (median/avg prices) and 'comps' (comparable transactions)
            
        Raises:
            RuntimeError: If no transaction dataset found on data.gov.il
        """
        # Convert coordinates to lat/lon
        lon, lat = self._trans_2039_4326.transform(x, y)
        subj = {"x": x, "y": y, "lon": lon, "lat": lat}

        # Find the best transactions resource
        res = self.find_transactions_resource()
        if not res:
            raise RuntimeError("לא נמצא משאב עסקאות פעיל ב-data.gov.il")
        
        # Fetch raw data
        rid = res.get("id")
        raw = self.fetch_datastore_records(rid, "תל אביב-יפו", limit)

        # Process and filter transactions
        comps: List[Dict[str, Any]] = []
        for r in raw:
            comp = self._process_transaction_record(
                r, subj["lat"], subj["lon"], date_from, date_to, target_area
            )
            if comp:
                comps.append(comp)

        # Sort by distance and date
        comps.sort(
            key=lambda c: (
                c["distance_m"] if c["distance_m"] is not None else 9e12,
                -int(datetime.fromisoformat(c["deal_date"]).timestamp()) if c["deal_date"] else 0,
            )
        )
        
        # Get top N comparables
        topn = comps[:top]

        # Calculate statistics
        subject_info = {"street": street, "house": house, "lat": subj["lat"], "lon": subj["lon"]}
        stats = self.calculate_statistics(topn, subject_info)

        return {"stats": stats, "comps": topn}


# Convenience function for backwards compatibility
def fetch_comparable_transactions(
    x: float, y: float, street: str, house: int,
    date_from: Optional[str] = None, date_to: Optional[str] = None,
    target_area: Optional[float] = None, limit: int = 2000, top: int = 20,
) -> Dict[str, Any]:
    """
    Convenience function to fetch comparable transactions.
    Creates a RealEstateTransactions instance and calls the method.
    """
    transactions = RealEstateTransactions()
    return transactions.fetch_comparable_transactions(
        x, y, street, house, date_from, date_to, target_area, limit, top
    )
