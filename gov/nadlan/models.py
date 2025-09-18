# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Optional


@dataclass
class Deal:
    address: Optional[str] = None
    deal_date: Optional[str] = None
    deal_amount: Optional[float] = None
    rooms: Optional[str] = None
    floor: Optional[str] = None
    asset_type: Optional[str] = None
    year_built: Optional[str] = None
    area: Optional[float] = None
    # Parcel information
    parcel_block: Optional[str] = None      # גוש
    parcel_parcel: Optional[str] = None     # חלקה
    parcel_sub_parcel: Optional[str] = None # תת-חלקה
    raw: Optional[Dict[str, Any]] = None

    @staticmethod
    def _num(x):
        if x is None:
            return None
        try:
            # Convert to string and clean up
            s = str(x).strip()
            # Remove currency symbols and commas
            s = s.replace("₪", "").replace(",", "").replace(" ", "")
            # Handle Hebrew square meter symbol
            s = s.replace("מ²", "").replace("מ'", "")
            # Try to convert to float
            if s:
                return float(s)
            return None
        except Exception:
            return None

    @staticmethod
    def _parse_number(x):
        """Parse number with proper handling of European decimal notation."""
        if x is None:
            return None
        try:
            # Convert to string and clean up
            s = str(x).strip()
            # Remove currency symbols
            s = s.replace("₪", "")
            # Handle Hebrew square meter symbol
            s = s.replace("מ²", "").replace("מ'", "")
            
            # Handle European decimal notation (comma as decimal separator)
            if "," in s and "." in s:
                # If both comma and dot exist, comma is likely thousands separator
                s = s.replace(",", "")
            elif "," in s and s.count(",") == 1:
                # Single comma, likely decimal separator
                s = s.replace(",", ".")
            
            # Remove spaces
            s = s.replace(" ", "")
            
            # Try to convert to float
            if s:
                return float(s)
            return None
        except Exception:
            return None

    @staticmethod
    def _parse_parcel_num(parcel_num: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse parcel number into block, parcel, and sub-parcel.
        
        Args:
            parcel_num: Parcel number in format "block-parcel-sub_parcel" (e.g., "6638-68-5")
            
        Returns:
            Tuple of (block, parcel, sub_parcel)
        """
        if not parcel_num:
            return None, None, None
        
        try:
            parts = str(parcel_num).split('-')
            if len(parts) >= 3:
                return parts[0], parts[1], parts[2]
            elif len(parts) == 2:
                return parts[0], parts[1], None
            elif len(parts) == 1:
                return parts[0], None, None
            else:
                return None, None, None
        except Exception:
            return None, None, None

    @classmethod
    def from_item(cls, d: Dict[str, Any]) -> "Deal":
        # Parse parcel number
        parcel_num = d.get("parcelNum") or d.get("ParcelNum")
        block, parcel, sub_parcel = cls._parse_parcel_num(parcel_num)
        
        return cls(
            address=d.get("address") or d.get("AssetAddress"),
            deal_date=d.get("deal_date") or d.get("dealDate") or d.get("DealDate"),
            deal_amount=cls._num(d.get("deal_amount") or d.get("dealAmount") or d.get("Price")),
            rooms=(str(d.get("rooms") or d.get("Rooms") or "") or None),
            floor=(str(d.get("floor") or d.get("Floor") or "") or None),
            asset_type=d.get("asset_type") or d.get("assetType") or d.get("AssetType"),
            year_built=(str(d.get("year_built") or d.get("yearBuilt") or d.get("BuildingYear") or "") or None),
            area=cls._parse_number(d.get("area") or d.get("TotalArea")),
            # Parcel information
            parcel_block=block,
            parcel_parcel=parcel,
            parcel_sub_parcel=sub_parcel,
            raw=d,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class NeighborhoodInfo:
    neigh_id: str
    neigh_name: str
    setl_id: str
    setl_name: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)