"""Collector for residential tenders (MichrazimSite)."""

from __future__ import annotations

import logging
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from gov.michrazim import MichrazimClient

from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class MichrazimCollector(BaseCollector):
    """Collect tenders from RAMI/Amidar and convert them into listing-like objects."""

    def __init__(self, client: Optional[MichrazimClient] = None) -> None:
        self.client = client or MichrazimClient()

    def _extract_yeshuv_code(self, govmap_data: Optional[Dict[str, Any]]) -> Optional[int]:
        """Try to pull a settlement code from GovMap data if available."""
        if not govmap_data:
            return None

        def _coerce_int(value: Any) -> Optional[int]:
            try:
                return int(str(value).strip())
            except Exception:
                return None

        parcel_props = (
            govmap_data.get("api_data", {}).get("parcel", {}) if isinstance(govmap_data, dict) else {}
        )
        if isinstance(parcel_props, dict):
            props = parcel_props.get("properties") or parcel_props
            for key in ("settlementcode", "setlcode", "settlement_code", "setl_code", "city_code"):
                code = _coerce_int(props.get(key))
                if code:
                    return code

        for address in govmap_data.get("addresses", []) if isinstance(govmap_data, dict) else []:
            code = _coerce_int(address.get("settlement_code") or address.get("setl_code"))
            if code:
                return code

        return None

    @staticmethod
    def _matches_asset(details: Dict[str, Any], block: Optional[str], parcel: Optional[str]) -> bool:
        """Return True when tender details reference the same block/parcel."""
        if not block and not parcel:
            return True
        tik_list = details.get("Tik") or []
        for tik in tik_list:
            for gush_helka in tik.get("GushHelka", []):
                gush = str(gush_helka.get("Gush") or "").strip()
                helka = str(gush_helka.get("Helka") or "").strip()
                if block and gush and gush != str(block):
                    continue
                if parcel and helka and helka != str(parcel):
                    continue
                return True
        return False

    def _build_listing_payload(
        self, summary: Dict[str, Any], details: Dict[str, Any]
    ) -> SimpleNamespace:
        """Convert tender details into a listing-like payload."""
        tik = (details.get("Tik") or [{}])[0] if isinstance(details.get("Tik"), list) else {}
        price = (
            details.get("MechirSafMichraz")
            or details.get("MechirSaf")
            or tik.get("MechirSaf")
            or tik.get("mechirShuma")
        )
        try:
            price_int = int(price) if price is not None else None
        except Exception:
            price_int = None

        area = tik.get("Shetach") or tik.get("ShetachBniya")
        try:
            area_val = float(area) if area not in (None, "") else None
        except Exception:
            area_val = None

        address = (
            details.get("Shchuna")
            or summary.get("Shchuna")
            or (tik.get("MitchamName") if isinstance(tik, dict) else None)
        )
        listing_id = f"michraz_{summary.get('MichrazID')}"

        meta = {
            "source": "michrazim",
            "price_label": "מחיר מכרז",
            "status": details.get("StatusMichraz"),
            "closingDate": details.get("SgiraDate"),
            "openingDate": details.get("PtichaDate"),
            "docs": details.get("MichrazDocList", []),
            "tik": tik,
            "raw": details,
        }

        return SimpleNamespace(
            title=f"מכרז {summary.get('MichrazName')}" + (f" - {address}" if address else ""),
            price=price_int,
            address=address,
            rooms=None,
            floor=None,
            size=area_val,
            total_size=None,
            property_type="auction",
            description=None,
            url=f"{MichrazimClient.BASE_URL}/#/michraz/{summary.get('MichrazID')}",
            listing_id=listing_id,
            listing_type="auction",
            ad_type="auction",
            contact_name=None,
            contact_phone=None,
            recent_deal=False,
            images=[],
            video=None,
            meta=meta,
            raw={
                **summary,
                "details": details,
                "source": "michrazim",
                "price_label": "מחיר מכרז",
            },
        )

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        govmap_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> List[Any]:
        """Collect tenders relevant to the given location."""
        query = ensure_location_query(location)
        yeshuv_code = self._extract_yeshuv_code(govmap_data)

        try:
            search_results = self.client.search(yeshuv_code=yeshuv_code)
        except Exception as exc:
            logger.warning("Michrazim search failed: %s", exc)
            return []

        if not search_results:
            return []

        filtered: List[Dict[str, Any]] = []
        for item in search_results:
            if yeshuv_code and item.get("KodYeshuv") != yeshuv_code:
                continue
            if query.city and not yeshuv_code:
                city_norm = query.city.replace(" ", "")
                if city_norm and city_norm not in (item.get("Shchuna") or "").replace(" ", ""):
                    continue
            filtered.append(item)

        listings: List[Any] = []
        for item in filtered:
            michraz_id = item.get("MichrazID")
            if not michraz_id:
                continue
            try:
                details = self.client.get_details(michraz_id)
            except Exception as exc:
                logger.debug("Skipping michraz %s due to details fetch error: %s", michraz_id, exc)
                continue

            if not self._matches_asset(details, query.block, query.parcel):
                continue

            listings.append(self._build_listing_payload(item, details))

        return listings
