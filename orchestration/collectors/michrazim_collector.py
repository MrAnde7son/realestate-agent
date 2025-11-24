"""Collector for residential tenders (MichrazimSite)."""

from __future__ import annotations

import logging
import time
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
    TimeoutError as FuturesTimeoutError,
)

from gov.michrazim import MichrazimClient

from orchestration.collectors.base_collector import BaseCollector
from orchestration.location import LocationQuery, ensure_location_query

logger = logging.getLogger(__name__)


class MichrazimCollector(BaseCollector):
    """Collect tenders from RAMI/Amidar and convert them into listing-like objects."""

    _KOD_YEUD_OBJECTS: Dict[int, Dict[str, Any]] = {
        1: {
            "TableID": 318,
            "TableName": "ייעוד מכרז",
            "Code": 1,
            "Value": "בנייה רוויה",
            "Group": None,
            "Status": 1,
            "MichrazPail": 0,
            "OrderBy": 0,
        },
        2: {
            "TableID": 318,
            "TableName": "ייעוד מכרז",
            "Code": 2,
            "Value": "בנייה נמוכה/צמודת קרקע",
            "Group": None,
            "Status": 1,
            "MichrazPail": 0,
            "OrderBy": 0,
        },
        3: {
            "TableID": 318,
            "TableName": "ייעוד מכרז",
            "Code": 3,
            "Value": "דיור מוגן",
            "Group": None,
            "Status": 1,
            "MichrazPail": 0,
            "OrderBy": 0,
        },
        4: {
            "TableID": 318,
            "TableName": "ייעוד מכרז",
            "Code": 4,
            "Value": "תעסוקה (תעשייה, מסחר, תיירות ושימושים כלכלים נוספים)",
            "Group": None,
            "Status": 1,
            "MichrazPail": 0,
            "OrderBy": 0,
        },
    }

    def __init__(self, client: Optional[MichrazimClient] = None) -> None:
        self.client = client or MichrazimClient()

    @staticmethod
    def _matches_asset(
        details: Dict[str, Any], block: Optional[str], parcel: Optional[str]
    ) -> bool:
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
                # if parcel and helka and helka != str(parcel):
                #     continue
                return True
        return False

    def _build_listing_payload(
        self, summary: Dict[str, Any], details: Dict[str, Any]
    ) -> SimpleNamespace:
        """Convert tender details into a listing-like payload."""
        tik = (
            (details.get("Tik") or [{}])[0]
            if isinstance(details.get("Tik"), list)
            else {}
        )
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

        address = details.get("Shchuna").strip() or summary.get("Shchuna").strip()
        listing_id = f"michraz_{summary.get('MichrazID')}"

        meta = {
            "source": "michrazim",
            "price_label": "מחיר מכרז",
            "tender_price": price_int,
            "status": details.get("StatusMichraz"),
            "closingDate": details.get("SgiraDate"),
            "openingDate": details.get("PtichaDate"),
            "docs": details.get("MichrazDocList", []),
            "tik": tik,
            "raw": details,
        }

        return SimpleNamespace(
            title=f"מכרז {summary.get('MichrazName')}"
            + (f" - {address}" if address else ""),
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
                "tender_price": price_int,
                "price_label": "מחיר מכרז",
                "source": "michrazim",
            },
        )

    def collect(
        self,
        location: Optional[LocationQuery] = None,
        **kwargs,
    ) -> List[Any]:
        """Collect tenders relevant to the given location.

        max_results: limit number of tenders to process to avoid long-running runs.
        details_timeout: per-request timeout (seconds) when fetching tender details.
        overall_timeout: total time budget (seconds) for the collector; ``None`` to disable.
        max_workers: concurrent detail fetches.
        """

        max_results: int = kwargs.get("max_results", 500)
        details_timeout: float = kwargs.get("details_timeout", 30.0)
        overall_timeout: float = kwargs.get("overall_timeout", 180.0)
        max_workers: int = kwargs.get("max_workers", 5)
        yeud_codes: List[int] = list(kwargs.get("yeud_codes") or [1, 2, 3, 4])

        query = ensure_location_query(location)
        deadline = time.perf_counter() + overall_timeout if overall_timeout else None
        start_time = time.perf_counter()

        logger.info(
            "🔍 Starting michrazim collection for city='%s', block=%s, parcel=%s (max_results=%d, max_workers=%d)",
            query.city,
            query.block,
            query.parcel,
            max_results,
            max_workers,
        )

        yeud_objects = [
            self._KOD_YEUD_OBJECTS[code]
            for code in yeud_codes
            if code in yeud_codes
        ]
        
        # Try to find settlement code by name for proper filtering
        yeshuv_code: Optional[int] = None
        if query.city:
            try:
                yeshuv_code = self.client.find_yishuv_code(query.city, timeout=details_timeout)
                if yeshuv_code:
                    logger.info("Found settlement code %d for city '%s'", yeshuv_code, query.city)
                else:
                    logger.warning("Could not find settlement code for city '%s', using name filter", query.city)
            except Exception as exc:
                logger.warning("Failed to lookup settlement code for '%s': %s", query.city, exc)
        
        search_filters: Dict[str, Any] = {
            "ActiveQuickSearch": False,
            "ActiveMichraz": None,
            "KodYeud": yeud_codes,
            "KodYeud_Obj": yeud_objects,
        }

        try:
            logger.info("Searching for michrazim tenders...")
            search_results = self.client.search(
                yeshuv_code=yeshuv_code,
                extra_payload=search_filters,
                timeout=details_timeout,
            )
            logger.info(
                "Found %d michrazim tenders in search results",
                len(search_results) if search_results else 0,
            )
        except Exception as exc:
            logger.warning("Michrazim search failed: %s", exc)
            return []

        if not search_results:
            logger.info("No michrazim tenders found for the given location")
            return []

        original_count = len(search_results)
        if max_results and len(search_results) > max_results:
            search_results = search_results[:max_results]
            logger.info(
                "Limited results from %d to %d tenders (max_results limit)",
                original_count,
                len(search_results),
            )

        listings: List[Any] = []
        executor = ThreadPoolExecutor(max_workers=max_workers)
        futures = {}
        skipped_no_id = 0
        try:
            logger.info(
                "Submitting %d detail fetch requests with %d workers...",
                len(search_results),
                max_workers,
            )
            for item in search_results:
                if deadline and time.perf_counter() >= deadline:
                    logger.warning(
                        "Michrazim collection stopped after reaching overall timeout"
                    )
                    break
                michraz_id = item.get("MichrazID")
                if not michraz_id:
                    skipped_no_id += 1
                    continue
                futures[
                    executor.submit(
                        self.client.get_details, michraz_id, details_timeout
                    )
                ] = item

            if skipped_no_id > 0:
                logger.warning("Skipped %d items without MichrazID", skipped_no_id)

            if not futures:
                logger.info("No valid michraz IDs found to fetch details for")
                return listings

            logger.info("Fetching details for %d tenders...", len(futures))
            remaining = max(0.0, deadline - time.perf_counter()) if deadline else None
            completed = 0
            failed = 0
            filtered_out = 0
            try:
                for future in as_completed(futures, timeout=remaining):
                    item = futures.get(future)
                    completed += 1
                    try:
                        details = future.result()
                    except Exception as exc:
                        failed += 1
                        logger.debug(
                            "Skipping michraz %s due to details fetch error: %s",
                            item.get("MichrazID") if item else "unknown",
                            exc,
                        )
                        continue

                    if item and self._matches_asset(details, query.block, query.parcel):
                        listings.append(self._build_listing_payload(item, details))
                        if len(listings) % 10 == 0:
                            logger.info(
                                "Progress: %d/%d details fetched, %d listings created",
                                completed,
                                len(futures),
                                len(listings),
                            )
                    else:
                        filtered_out += 1
            except FuturesTimeoutError:
                logger.warning(
                    "Michrazim collection timed out after %.1fs; returning partial results (%d/%d completed)",
                    overall_timeout or 0,
                    completed,
                    len(futures),
                )
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

        elapsed = time.perf_counter() - start_time
        logger.info(
            f"📊 michrazim collector completed: {len(listings)} listings created from {original_count} tenders "
            f"(completed: {completed}, failed: {failed}, filtered: {filtered_out}) in {elapsed:.1f}s",
        )

        return listings


if __name__ == "__main__":
    collector = MichrazimCollector()
    print(collector.collect(LocationQuery(city="תל אביב יפו")))
