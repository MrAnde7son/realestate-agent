# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass, asdict
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
    parcel_gush: Optional[str] = None      # גוש
    parcel_helka: Optional[str] = None     # חלקה
    parcel_sub_helka: Optional[str] = None # תת-חלקה
    raw: Optional[Dict[str, Any]] = None

    @staticmethod
    def _num(x):
        if x is None:
            return None
        try:
            return float(str(x).replace(",", "").replace("₪", "").strip())
        except Exception:
            return None

    @staticmethod
    def _parse_parcel_num(parcel_num: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Parse parcel number into gush, helka, and sub-helka.
        
        Args:
            parcel_num: Parcel number in format "gush-helka-sub_helka" (e.g., "6638-68-5")
            
        Returns:
            Tuple of (gush, helka, sub_helka)
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
        gush, helka, sub_helka = cls._parse_parcel_num(parcel_num)
        
        return cls(
            address=d.get("address") or d.get("AssetAddress"),
            deal_date=d.get("dealDate") or d.get("DealDate"),
            deal_amount=cls._num(d.get("dealAmount") or d.get("Price")),
            rooms=(str(d.get("rooms") or d.get("Rooms") or "") or None),
            floor=(str(d.get("floor") or d.get("Floor") or "") or None),
            asset_type=d.get("assetType") or d.get("AssetType"),
            year_built=(str(d.get("yearBuilt") or d.get("BuildingYear") or "") or None),
            area=cls._num(d.get("area") or d.get("TotalArea")),
            # Parcel information
            parcel_gush=gush,
            parcel_helka=helka,
            parcel_sub_helka=sub_helka,
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