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
    raw: Optional[Dict[str, Any]] = None

    @staticmethod
    def _num(x):
        if x is None:
            return None
        try:
            return float(str(x).replace(",", "").replace("₪", "").strip())
        except Exception:
            return None

    @classmethod
    def from_item(cls, d: Dict[str, Any]) -> "Deal":
        return cls(
            address=d.get("address") or d.get("AssetAddress"),
            deal_date=d.get("dealDate") or d.get("DealDate"),
            deal_amount=cls._num(d.get("dealAmount") or d.get("Price")),
            rooms=(str(d.get("rooms") or d.get("Rooms") or "") or None),
            floor=(str(d.get("floor") or d.get("Floor") or "") or None),
            asset_type=d.get("assetType") or d.get("AssetType"),
            year_built=(str(d.get("yearBuilt") or d.get("BuildingYear") or "") or None),
            area=cls._num(d.get("area") or d.get("TotalArea")),
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