from __future__ import annotations

from typing import Any, Iterable, List, Optional, Dict, Tuple
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from types import SimpleNamespace
from contextlib import contextmanager  # added import

from sqlalchemy.orm import Session

from db.database import SQLAlchemyDatabase
from db.models import Listing, SourceRecord, Transaction
from utils.helpers import _first_nonempty, _safe_get
from yad2.scrapers.yad2_scraper import RealEstateListing

# collector imports
from orchestration.collectors.yad2_collector import Yad2Collector
from orchestration.collectors.gis_collector import GISCollector
from orchestration.collectors.gov_collector import GovCollector
from orchestration.collectors.govmap_collector import GovMapCollector
from orchestration.collectors.rami_collector import RamiCollector
from orchestration.collectors.mavat_collector import MavatCollector
from orchestration.location import LocationQuery
from govmap.api_client import itm_to_wgs84
from orchestration.observability import (
    COLLECTOR_FAILURE,
    COLLECTOR_LATENCY,
    COLLECTOR_SUCCESS,
    start_metrics_server,
    tracer,
)

from django.contrib.auth import get_user_model
from datetime import datetime

try:  # pragma: no cover - best effort import
    from core.analytics import track  # type: ignore
except Exception:  # pragma: no cover - fallback when Django not configured
    def track(*args, **kwargs):
        pass

# alert helpers
from orchestration.alerts import Notifier

logger = logging.getLogger(__name__)

"""High level data collection pipeline for real-estate assets.

This module defines a small object oriented framework that orchestrates
calls to the various data providers (Yad2, Tel-Aviv GIS, gov.il datasets
and RAMI plans) and persists the aggregated results in the local
SQLAlchemy database.
"""

# Import Django models if available
try:  # pragma: no cover - best effort import
    import sys

    backend_path = os.path.join(os.path.dirname(__file__), "..", "backend-django")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    import django
    from django.conf import settings

    if not settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
        django.setup()

    from core.models import AlertRule, Document, Plan  # type: ignore
except ImportError as e:  # pragma: no cover - best effort
    print(f"Failed to import Django models: {e}")

    class AlertRule:  # type: ignore
        objects = []


def _load_user_notifiers() -> List[Notifier]:
    """Build notifiers for all users with active alert rules."""

    notifiers: List[Notifier] = []
    try:
        from orchestration.alerts import create_notifier_for_alert_rule
        
        alert_rules = AlertRule.objects.filter(active=True).select_related("user")  # type: ignore[attr-defined]
        for alert_rule in alert_rules:
            notifier = create_notifier_for_alert_rule(alert_rule)
            if notifier:
                notifiers.append(notifier)
    except Exception as e:  # pragma: no cover - best effort
        print(f"Failed to create user notifiers: {e}")
    return notifiers


def _object_to_payload(obj: Any) -> Dict[str, Any]:
    """Convert arbitrary objects into plain dictionaries for serialization."""

    if obj is None:
        return {}

    if isinstance(obj, dict):
        return {k: v for k, v in obj.items() if not k.startswith("_")}

    data: Dict[str, Any] = {}
    try:
        for key, value in vars(obj).items():
            if key.startswith("_"):
                continue
            data[key] = value
    except TypeError:
        # ``vars`` might fail for certain built-in types – fall back to repr
        pass
    return data


def _build_listing_snapshot(raw_listing: Any, db_listing: Listing) -> SimpleNamespace:
    """Create an immutable snapshot of the listing for async notifications."""

    payload: Dict[str, Any] = {}
    payload.update(_object_to_payload(raw_listing))
    payload.update(_object_to_payload(db_listing))
    payload.setdefault("id", getattr(db_listing, "id", None))
    return SimpleNamespace(**payload)


def _listing_to_dict(listing: Any) -> Dict[str, Any]:
    """Convert Yad2 listings into plain dictionaries for downstream processing."""

    if isinstance(listing, dict):
        data = dict(listing)
    elif hasattr(listing, "to_dict"):
        data = listing.to_dict()
    else:
        keys = (
            "title",
            "price",
            "address",
            "rooms",
            "floor",
            "size",
            "property_type",
            "description",
            "images",
            "documents",
            "contact_info",
            "features",
            "url",
            "listing_id",
            "date_posted",
            "coordinates",
            "scraped_at",
            "meta",
        )
        data = {key: getattr(listing, key, None) for key in keys}

    if "area" not in data or data.get("area") in (None, ""):
        size_value = data.get("size")
        if size_value in (None, "") and hasattr(listing, "size"):
            size_value = getattr(listing, "size")
        if size_value not in (None, ""):
            data["area"] = size_value

    return data


def _normalize_listings(listings: Iterable[Any]) -> List[Dict[str, Any]]:
    """Return a list of dictionaries regardless of the original listing type."""

    normalized: List[Dict[str, Any]] = []
    if not listings:
        return normalized

    for listing in listings:
        if listing is None:
            continue
        try:
            normalized.append(_listing_to_dict(listing))
        except Exception as exc:  # pragma: no cover - extremely defensive
            logger.debug("Skipping listing that cannot be normalized: %s", exc)
    return normalized


def _dispatch_notifications(pending: List[Tuple[Notifier, Any]]) -> None:
    """Send notifications outside of the main persistence loop."""

    if not pending:
        return

    logger.info("📣 Dispatching %d queued notifications", len(pending))

    def _execute(notifier: Notifier, listing: Any) -> None:
        try:
            notifier.notify(listing)
            track("alert_send", source=notifier.__class__.__name__)
        except Exception as exc:  # pragma: no cover - best effort logging
            track(
                "alert_fail",
                source=notifier.__class__.__name__,
                error_code=str(exc),
            )
            logger.warning("⚠️ Notification failed: %s", exc)

    if len(pending) == 1:
        notifier, listing = pending[0]
        _execute(notifier, listing)
        return

    max_workers = min(4, len(pending))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_execute, notifier, listing) for notifier, listing in pending]
        for future in futures:
            future.result()






# ---------------------------------------------------------------------------
# Data pipeline orchestrator
# ---------------------------------------------------------------------------

class DataPipeline:
    """Collect data from external services and persist it to the database."""

    # Per-collector configuration for timeouts and retry counts. These can
    # be overridden via environment variables if needed.
    TIMEOUTS = {
        "yad2": float(os.getenv("YAD2_TIMEOUT", "30")),
        "gis": float(os.getenv("GIS_TIMEOUT", "30")),
        "gov": float(os.getenv("GOV_TIMEOUT", "60")),
        "govmap": float(os.getenv("GOVMAP_TIMEOUT", "60")),
        "gov_rami": float(os.getenv("GOV_RAMI_TIMEOUT", "60")),
        "mavat": float(os.getenv("MAVAT_TIMEOUT", "60")),
    }
    RETRIES = {
        "yad2": int(os.getenv("YAD2_RETRIES", "0")),
        "gis": int(os.getenv("GIS_RETRIES", "0")),
        "gov": int(os.getenv("GOV_RETRIES", "0")),
        "govmap": int(os.getenv("GOVMAP_RETRIES", "0")),
        "gov_rami": int(os.getenv("GOV_RAMI_RETRIES", "0")),
        "mavat": int(os.getenv("MAVAT_RETRIES", "0")),
    }

    def __init__(
        self,
        db: Optional[SQLAlchemyDatabase] = None,
        *,
        db_session: Optional["Session"] = None,
        yad2: Optional[Yad2Collector] = None,
        gis: Optional[GISCollector] = None,
        gov: Optional[GovCollector] = None,
        govmap: Optional[GovMapCollector] = None,
        rami: Optional[RamiCollector] = None,
        mavat: Optional[MavatCollector] = None,
    ) -> None:
        """Create a new :class:`DataPipeline` instance.

        Parameters
        ----------
        db:
            Optional database helper.  If omitted a new ``SQLAlchemyDatabase``
            instance is created.  When ``db_session`` is provided this argument
            may be ``None``.
        db_session:
            Optional SQLAlchemy :class:`Session` object to use instead of
            creating a new one via ``db.get_session``.  This makes the pipeline
            easier to unit test where an in-memory session is often supplied.
        """

        self.db = db
        self.session = db_session
        if self.db is None and self.session is None:
            # Fallback to default database when nothing is supplied.
            self.db = SQLAlchemyDatabase()

        self.yad2 = yad2 or Yad2Collector()
        self.gis = gis or GISCollector()
        self.gov = gov or GovCollector()
        self.govmap = govmap or GovMapCollector()
        self.rami = rami or RamiCollector()
        self.mavat = mavat or MavatCollector()
        
        # Note: GovMap client is now accessed through the collector

        # Expose Prometheus metrics endpoint
        start_metrics_server(int(os.getenv("METRICS_PORT", "8000")))

        # Ensure database is ready when we manage it ourselves.
        if self.db is not None:
            self.db.init_db()
            try:
                self.db.create_tables()
            except Exception as e:
                # Tables might already exist – ignore
                logger.debug(f"Tables might already exist: {e}")
                pass

    def _collect_with_observability(
        self,
        source: str,
        func,
        *args,
        timeout: Optional[float] = None,
        retries: int = 0,
        retry_delay: float = 0,
        asset_id: Optional[int] = None,
        **kwargs,
    ):
        """Wrap collector calls with metrics, tracing, timeouts and retries."""
        with tracer.start_as_current_span(source):
            start_time = time.perf_counter()
            last_exc: Optional[Exception] = None
            result: Any = None
            items_count = 0
            try:
                for attempt in range(retries + 1):
                    try:
                        with ThreadPoolExecutor(max_workers=1) as executor:
                            future = executor.submit(func, *args, **kwargs)
                            result = future.result(timeout=timeout)
                        items_count = self._count_items(result)
                        COLLECTOR_SUCCESS.labels(source=source).inc()
                        return result
                    except FuturesTimeoutError:
                        last_exc = TimeoutError(
                            f"{source} collector timed out after {timeout}s"
                        )
                    except Exception as e:  # pragma: no cover - propagate
                        last_exc = e
                    if attempt < retries:
                        if retry_delay:
                            time.sleep(retry_delay)
                COLLECTOR_FAILURE.labels(source=source).inc()
                if last_exc:
                    raise last_exc
                raise RuntimeError(f"{source} collector failed")
            finally:
                duration = time.perf_counter() - start_time
                COLLECTOR_LATENCY.labels(source=source).observe(duration)
                logger.info(
                    f"📊 {source.upper()} collector completed",
                    extra={
                        "asset_id": asset_id,
                        "collector": source,
                        "duration_ms": int(duration * 1000),
                        "items_count": items_count,
                        "status": "success" if items_count > 0 else "empty"
                    },
                )

    def _count_items(self, data: Any) -> int:
        """Best-effort count of items returned by a collector."""
        try:
            if isinstance(data, dict):
                return sum(
                    len(v) for v in data.values() if hasattr(v, "__len__")
                )
            if hasattr(data, "__len__"):
                return len(data)
            return 1 if data is not None else 0
        except Exception:
            return 0

    # ------------------------------------------------------------------
    def _store_listing(self, session, listing: RealEstateListing) -> Listing:
        obj = Listing(
            title=listing.title,
            price=listing.price,
            address=listing.address,
            rooms=listing.rooms,
            floor=listing.floor,
            size=listing.size,
            property_type=listing.property_type,
            description=listing.description,
            url=listing.url,
            listing_id=listing.listing_id,
        )
        if listing.coordinates:
            try:
                obj.longitude = listing.coordinates[0]
                obj.latitude = listing.coordinates[1]
            except Exception:
                pass
        session.add(obj)
        session.flush()  # populate id
        return obj

    def _add_source_record(self, session, listing_id: int, source: str, data: Any) -> None:
        session.add(SourceRecord(listing_id=listing_id, source=source, data=data))

    def _add_transactions(self, session, listing_id: int, deals: Iterable[Any]) -> None:
        def _to_number(v):
            if v is None:
                return None
            if isinstance(v, (int, float)):
                return v
            try:
                # Remove thousands separators / currency symbols
                cleaned = str(v).replace(',', '').replace('₪', '').strip()
                return float(cleaned) if cleaned else None
            except Exception:
                return None
        for d in deals:
            raw = d.to_dict() if hasattr(d, "to_dict") else dict(d)
            session.add(
                Transaction(
                    listing_id=listing_id,
                    deal_date=raw.get("deal_date"),
                    deal_amount=_to_number(raw.get("deal_amount")),
                    rooms=raw.get("rooms"),
                    floor=raw.get("floor"),
                    asset_type=raw.get("asset_type"),
                    year_built=raw.get("year_built"),
                    area=_to_number(raw.get("area")),
                    raw=raw,
                )
            )

    # ------------------------------------------------------------------
    def run(
        self,
        city: str,
        street: str,
        house_number: int,
        max_pages: int = 1,
        asset_id: Optional[int] = None,
    ) -> List[Any]:
        """Run the pipeline for a given location.

        Parameters
        ----------
        city: str
            City name associated with the asset.
        street: str
            Street name associated with the asset.
        house_number: int
            Street number for the asset. ``0`` or ``None`` is treated as missing.

        The function still persists results to the database but also returns a
        list of raw objects/dictionaries representing the collected data.  This
        makes the pipeline easier to test in isolation.
        """

        location = LocationQuery(city=city, street=street, house_number=house_number)
        street_with_number = location.street_with_number
        full_address = location.formatted

        logger.info(
            "🚀 Starting data pipeline for %s (max_pages=%s)",
            full_address or street_with_number or location.city,
            max_pages,
        )
        start_time = time.perf_counter()

        with tracer.start_as_current_span(
            "data_pipeline.run",
            attributes={
                "city": location.city,
                "street": location.street,
                "house_number": location.house_number,
                "full_address": full_address,
                "max_pages": max_pages,
            },
        ):
            # Search Yad2 for listings
            try:
                listings = self._collect_with_observability(
                    "yad2",
                    self.yad2.collect,
                    location,
                    max_pages=max_pages,
                    timeout=self.TIMEOUTS.get("yad2"),
                    retries=self.RETRIES.get("yad2", 0),
                    asset_id=asset_id,
                )
                track("collector_success", source="yad2")
                logger.info(f"📊 Found {len(listings)} Yad2 listings")
            except Exception as e:
                track("collector_fail", source="yad2", error_code=str(e))
                logger.error(f"❌ Yad2 collection failed: {e}")
                listings = []

            # Load user notifiers once per run
            notifiers = _load_user_notifiers()

            # Decide which session to use
            session_provided = self.session is not None
            session = self.session or (self.db.get_session() if self.db else None)
            if session is None:
                raise RuntimeError("No database session available")

            results: List[Any] = []
            pending_notifications: List[Tuple[Notifier, Any]] = []
            
            # Get address coordinates using GovMap autocomplete
            x_itm = None
            y_itm = None
            lon_wgs84 = None
            lat_wgs84 = None
            block = ""
            parcel = ""
            
            # Use GovMap collector to get coordinates and parcel data
            try:
                logger.info("🗺️ Getting address coordinates and parcel data from GovMap...")
                govmap_data = self._collect_with_observability(
                    "govmap",
                    self.govmap.collect,
                    location,
                    timeout=self.TIMEOUTS.get("govmap"),
                    retries=self.RETRIES.get("govmap", 0),
                    asset_id=asset_id,
                )
                track("collector_success", source="govmap")
                
                # Extract coordinates from GovMap result
                if "x" in govmap_data and "y" in govmap_data:
                    x_itm = govmap_data["x"]
                    y_itm = govmap_data["y"]
                    # Convert ITM to WGS84
                    lon_wgs84, lat_wgs84 = itm_to_wgs84(x_itm, y_itm)
                    logger.info(f"📍 Coordinates extracted: ITM({x_itm}, {y_itm}) -> WGS84({lon_wgs84:.6f}, {lat_wgs84:.6f})")
                else:
                    logger.warning("⚠️ No coordinates found in GovMap response")
                    
            except Exception as e:
                govmap_data = {}
                track("collector_fail", source="govmap", error_code=str(e))
                logger.warning(f"⚠️ GovMap collection failed: {e}")
                logger.info("🔄 Falling back to GIS collector for coordinates...")
            
            # Extract block and parcel from GovMap data
            if govmap_data.get("api_data", {}).get("parcel"):
                parcel_props = govmap_data.get("api_data", {}).get("parcel", {}).get('properties', {})
                block = parcel_props.get("gushnumber", "")
                parcel = parcel_props.get("parcelnumber", "")

            logger.info(f"🏛️ GovMap data collected: block={block}, parcel={parcel}")

                # Note: Additional GovMap data (parcel API, layers catalog, search types) 
                # is now collected by the enhanced GovMap collector above
            
            # Get GIS data (supplementary or fallback for coordinates)
            gis_data = {}
            try:
                logger.info("🗺️ Collecting GIS data...")
                gis_data = self._collect_with_observability(
                    "gis",
                    self.gis.collect,
                    location,
                    timeout=self.TIMEOUTS.get("gis"),
                    retries=self.RETRIES.get("gis", 0),
                    asset_id=asset_id,
                )
                track("collector_success", source="gis")
                
                # Extract block and parcel from successful GIS collection
                if gis_data.get('block') and gis_data.get('parcel'):
                    block = gis_data.get('block', '')
                    parcel = gis_data.get('parcel', '')
                    logger.info(f"✅ GIS data collected successfully: block={block}, parcel={parcel}")
            except Exception as e:
                gis_data = {}
                track("collector_fail", source="gis", error_code=str(e))
                logger.warning(f"⚠️ GIS collection failed: {e}")

            # Get government data once for the address
            gov_data = {"decisive": [], "transactions": []}
            if block and parcel:
                try:
                    logger.info("🏛️ Collecting government data...")
                    gov_data = self._collect_with_observability(
                        "gov",
                        self.gov.collect,
                        block,
                        parcel,
                        location,
                        timeout=self.TIMEOUTS.get("gov"),
                        retries=self.RETRIES.get("gov", 0),
                        asset_id=asset_id,
                    )
                    track("collector_success", source="gov")
                    logger.info(f"📊 Government data collected: {len(gov_data.get('decisive', []))} decisives, {len(gov_data.get('transactions', []))} transactions")
                except Exception as e:
                    gov_data = {"decisive": [], "transactions": []}
                    track("collector_fail", source="gov", error_code=str(e))
                    logger.warning(f"⚠️ Government data collection failed: {e}")
            
            # Get RAMI plans once for the address
            plans = []
            if block and parcel:
                try:
                    logger.info("📋 Collecting RAMI plans...")
                    plans = self._collect_with_observability(
                        "gov_rami",
                        self.rami.collect,
                        block=block,
                        parcel=parcel,
                        timeout=self.TIMEOUTS.get("gov_rami"),
                        retries=self.RETRIES.get("gov_rami", 0),
                        asset_id=asset_id,
                    )
                    track("collector_success", source="gov_rami")
                    logger.info(f"📋 RAMI plans collected: {len(plans)} plans")
                except Exception as e:
                    plans = []
                    track("collector_fail", source="gov_rami", error_code=str(e))
                    logger.warning(f"⚠️ RAMI collection failed: {e}")
            
            # Get Mavat plans once for the address
            mavat_plans = []
            if block and parcel:
                try:
                    logger.info("🏗️ Collecting Mavat plans...")
                    mavat_plans = self._collect_with_observability(
                        "mavat",
                        self.mavat.collect,
                        block=block,
                        parcel=parcel,
                        city=location.city,
                        timeout=self.TIMEOUTS.get("mavat"),
                        retries=self.RETRIES.get("mavat", 0),
                        asset_id=asset_id,
                    )
                    track("collector_success", source="mavat")
                    logger.info(f"🏗️ Mavat plans collected: {len(mavat_plans)} plans")
                except Exception as e:
                    mavat_plans = []
                    track("collector_fail", source="mavat", error_code=str(e))
                    logger.warning(f"⚠️ Mavat collection failed: {e}")
            
            try:
                # Process listings if any exist
                for i, listing in enumerate(listings, 1):
                    logger.info(f"🏠 Processing listing {i}/{len(listings)}: {listing.title}")
                    # Store listing in DB and add to return list
                    db_listing = self._store_listing(session, listing)
                    results.append(listing)

                    listing_snapshot = _build_listing_snapshot(listing, db_listing)

                    # ---------------- GovMap Autocomplete (already collected above) ----------------
                    if govmap_data.get("api_data", {}).get("autocomplete"):
                        autocomplete_data = govmap_data["api_data"]["autocomplete"]
                        self._add_source_record(session, db_listing.id, "govmap_autocomplete", autocomplete_data)
                        results.append({"source": "govmap_autocomplete", "data": autocomplete_data})

                    # ---------------- GovMap Parcel Data (already collected above) ----------------
                    if govmap_data:
                        self._add_source_record(session, db_listing.id, "govmap", govmap_data)
                        results.append({"source": "govmap", "data": govmap_data})

                    # ---------------- GIS (supplementary data) ----------------
                    if gis_data:
                        self._add_source_record(session, db_listing.id, "gis", gis_data)
                        results.append({"source": "gis", "data": gis_data})

                    # ---------------- Gov data (collected once above) ----------------
                    self._add_source_record(session, db_listing.id, "gov", gov_data)
                    
                    decisives = gov_data.get("decisive") or []
                    if decisives:
                        self._add_source_record(
                            session, db_listing.id, "decisive", decisives
                        )
                        results.append({"source": "decisive", "data": decisives})

                    deals = gov_data.get("transactions") or []
                    self._add_transactions(session, db_listing.id, deals)
                    if deals:
                        results.append({"source": "transactions", "data": deals})

                    # ---------------- RAMI plans (collected once above) ----------------
                    if plans:
                        self._add_source_record(session, db_listing.id, "gov_rami", plans)
                        results.append({"source": "gov_rami", "data": plans})

                    # ---------------- Mavat plans (collected once above) ----------------
                    if mavat_plans:
                        self._add_source_record(
                            session, db_listing.id, "mavat", mavat_plans
                        )
                        results.append({"source": "mavat", "data": mavat_plans})

                    # ---------------- Alerts ----------------
                    for notifier in notifiers:
                        if notifier.matches(listing_snapshot):
                            pending_notifications.append((notifier, listing_snapshot))
                
                # If no listings, still add collected data to results
                if not listings:
                    logger.info("📊 No Yad2 listings found, but adding collected data to results")
                    
                    # Add GovMap autocomplete data to results
                    if govmap_data.get("api_data", {}).get("autocomplete"):
                        autocomplete_data = govmap_data["api_data"]["autocomplete"]
                        results.append({"source": "govmap_autocomplete", "data": autocomplete_data})

                    # Add GovMap parcel data to results
                    if govmap_data:
                        results.append({"source": "govmap", "data": govmap_data})
                    
                    # Add GIS data to results (supplementary)
                    if gis_data:
                        results.append({"source": "gis", "data": gis_data})
                    
                    # Add government data to results
                    if gov_data.get("decisive"):
                        results.append({"source": "decisive", "data": gov_data["decisive"]})
                    if gov_data.get("transactions"):
                        results.append({"source": "transactions", "data": gov_data["transactions"]})
                    
                    # Add RAMI plans to results
                    if plans:
                        results.append({"source": "gov_rami", "data": plans})
                    
                    # Add Mavat plans to results
                    if mavat_plans:
                        results.append({"source": "mavat", "data": mavat_plans})

                session.commit()

                _dispatch_notifications(pending_notifications)

                listing_payloads = _normalize_listings(listings)

                # Update Asset model with collected data
                if asset_id:
                    _update_asset_with_collected_data(
                        asset_id,
                        block,
                        parcel,
                        govmap_data.get("api_data", {}).get("autocomplete", {}),
                        govmap_data,
                        gis_data,
                        gov_data,
                        plans,
                        mavat_plans,
                        listing_payloads,
                        x_itm,
                        y_itm,
                        lon_wgs84,
                        lat_wgs84,
                    )

                    # Create snapshot for alert evaluation
                    _create_asset_snapshot(asset_id, results)

                    # Trigger alert evaluation
                    try:
                        from core.tasks import evaluate_alerts_for_asset
                        evaluate_alerts_for_asset.delay(asset_id)
                    except Exception as e:
                        logger.error("Failed to trigger alert evaluation for asset %s: %s", asset_id, e)
            finally:
                if not session_provided:
                    session.close()

            # Log completion summary
            execution_time = time.perf_counter() - start_time
            logger.info(f"✅ Pipeline completed successfully in {execution_time:.2f}s")
            logger.info(f"📊 Processed {len(listings)} listings with data from {len(set(r.get('source', 'yad2') if isinstance(r, dict) else 'yad2' for r in results))} sources")
            
            return results


def _update_asset_with_collected_data(asset_id: int, block: str, parcel: str, govmap_autocomplete_data: Dict[str, Any], govmap_data: Dict[str, Any], gis_data: Dict[str, Any], gov_data: Dict[str, Any], plans: List[Dict[str, Any]], mavat_plans: List[Dict[str, Any]], listings: Iterable[Any], x_itm: Optional[float] = None, y_itm: Optional[float] = None, lon_wgs84: Optional[float] = None, lat_wgs84: Optional[float] = None) -> None:
    """Update the Asset with collected enrichment data.

    Improvements:
    - Granular phase logging (use env ASSET_UPDATE_DEBUG=1 to raise on first failure)
    - Smaller try blocks: a failure in one enrichment source no longer hides stack traces
    - Structured debug logs with timing per phase
    """
    # Defensive: ensure all dicts/lists are not None
    govmap_autocomplete_data = govmap_autocomplete_data or {}
    govmap_data = govmap_data or {}
    gis_data = gis_data or {}
    gov_data = gov_data or {}
    plans = plans or []
    mavat_plans = mavat_plans or []
    listings = listings or []

    # Lazy Django setup (kept inside function so unit tests without Django still work)
    with asset_update_phase("django_setup", asset_id):
        import os as _os
        import sys as _sys
        backend_path = _os.path.join(_os.path.dirname(__file__), "..", "backend-django")
        if backend_path not in _sys.path:
            _sys.path.insert(0, backend_path)
        import django  # type: ignore
        from django.conf import settings as _settings  # type: ignore
        if not _settings.configured:
            _os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
            django.setup()
        from core.models import Asset  # type: ignore

    # Load asset
    try:
        asset = Asset.objects.get(id=asset_id)
    except Exception as e:  # noqa: BLE001
        logger.exception("[ASSET_UPDATE] Failed to load Asset id=%s: %s", asset_id, e)
        return

    # Basic identifiers & coordinates -------------------------------------------------
    with asset_update_phase("basic_fields", asset_id):
        if block:
            asset.block = block
        if parcel:
            asset.parcel = parcel
        # Prefer GovMap coordinates
        if lon_wgs84 is not None and lat_wgs84 is not None:
            asset.lat = lat_wgs84
            asset.lon = lon_wgs84
            logger.debug("Asset %s coordinates set from GovMap WGS84 (lat=%s lon=%s)", asset_id, lat_wgs84, lon_wgs84)
        elif gis_data.get('x') and gis_data.get('y'):
            try:
                lon_wgs84_gis, lat_wgs84_gis = itm_to_wgs84(gis_data.get('x'), gis_data.get('y'))
                asset.lat = lat_wgs84_gis
                asset.lon = lon_wgs84_gis
                logger.debug("Asset %s coordinates converted from GIS ITM -> WGS84", asset_id)
            except Exception:
                logger.exception("Failed to convert GIS coordinates for asset %s; storing raw ITM", asset_id)
                asset.lat = gis_data.get('x')
                asset.lon = gis_data.get('y')
        if getattr(asset, 'street', None) and getattr(asset, 'number', None):
            asset.normalized_address = f"{asset.street} {asset.number}" + (f" דירה {asset.apartment}" if getattr(asset, 'apartment', None) else '') + (f" {asset.city}" if getattr(asset, 'city', None) else '')
        if not asset.meta:
            asset.meta = {}

    # GIS processing ------------------------------------------------------------------
    with asset_update_phase("process_gis", asset_id):
        if gis_data:
            asset.meta['gis_data'] = {
                'building_permits': gis_data.get('permits', []),
                'land_use_rights': gis_data.get('rights', []),
                'shelters': gis_data.get('shelters', []),
                'green_areas': gis_data.get('green', []),
                'noise_levels': gis_data.get('noise', []),
                'cell_antennas': gis_data.get('antennas', []),
                'blocks': gis_data.get('blocks', []),
                'parcels': gis_data.get('parcels', []),
                'coordinates': {'x': gis_data.get('x'), 'y': gis_data.get('y')},
            }
            # Privilege page attempt + parse
            try:
                from gis.gis_client import TelAvivGS  # type: ignore
                from gis.parse_zchuyot import parse_zchuyot  # type: ignore
                x = gis_data.get('x'); y = gis_data.get('y')
                if x and y:
                    gis_client = TelAvivGS()
                    privilege_data = gis_client.get_building_privilege_page(x, y, save_dir="privilege_pages")
                    if privilege_data and isinstance(privilege_data, dict) and privilege_data.get('content_type') == 'pdf':
                        pdf_path = privilege_data.get('file_path')
                        if pdf_path:
                            asset.meta['privilege_page_data'] = parse_zchuyot(pdf_path)
            except Exception:
                logger.debug("Privilege page acquisition failed for asset %s", asset_id, exc_info=True)
            _process_gis_data(asset, gis_data)

    # GovMap autocomplete --------------------------------------------------------------
    with asset_update_phase("process_govmap_autocomplete", asset_id):
        if govmap_autocomplete_data:
            asset.meta['govmap_autocomplete_data'] = {
                'autocomplete_result': govmap_autocomplete_data,
                'coordinates': {
                    'x_itm': x_itm,
                    'y_itm': y_itm,
                    'lon_wgs84': lon_wgs84,
                    'lat_wgs84': lat_wgs84,
                },
            }
            _process_govmap_autocomplete_data(asset, govmap_autocomplete_data)

    # GovMap parcel -------------------------------------------------------------------
    with asset_update_phase("process_govmap_parcel", asset_id):
        if govmap_data:
            asset.meta['govmap_data'] = {
                'parcel': govmap_data.get('api_data', {}).get('parcel', {}),
                'nearby_layers': govmap_data.get('nearby', {}),
                'coordinates': {'x': govmap_data.get('x'), 'y': govmap_data.get('y')},
                'api_data': govmap_data.get('api_data', {}),
            }
            _process_govmap_data(asset, govmap_data)

    # Government data -----------------------------------------------------------------
    with asset_update_phase("process_government", asset_id):
        if gov_data:
            asset.meta['government_data'] = {
                'decisive_appraisals': gov_data.get('decisive', []),
                'transaction_history': gov_data.get('transactions', []),
            }
            _process_government_data(asset, gov_data)

    # RAMI plans ----------------------------------------------------------------------
    with asset_update_phase("process_rami", asset_id):
        if plans:
            asset.meta['rami_plans'] = plans
            _process_rami_plans(asset, plans)

    # Mavat plans ---------------------------------------------------------------------
    with asset_update_phase("process_mavat", asset_id):
        if mavat_plans:
            asset.meta['mavat_plans'] = mavat_plans
            _process_mavat_plans(asset, mavat_plans)

    # Yad2 listings -------------------------------------------------------------------
    normalized_listings = []
    with asset_update_phase("normalize_listings", asset_id):
        normalized_listings = _normalize_listings(listings or [])
        if listings and not normalized_listings:
            logger.debug("All listings dropped while normalizing Yad2 data for asset %s", asset_id)
        if normalized_listings:
            asset.meta['yad2_listings'] = normalized_listings
            prices = [l.get('price') for l in normalized_listings if l.get('price')]
            areas = [l.get('area') for l in normalized_listings if l.get('area')]
            market_data = asset.meta.setdefault('market_data', {})
            if prices:
                market_data.update({
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'avg_price': sum(prices) / len(prices),
                    'price_count': len(prices),
                })
            if areas:
                market_data.update({
                    'min_area': min(areas),
                    'max_area': max(areas),
                    'avg_area': sum(areas) / len(areas),
                    'area_count': len(areas),
                })
            if not market_data:
                asset.meta.pop('market_data', None)

    # Timestamp -----------------------------------------------------------------------
    with asset_update_phase("timestamp_and_save", asset_id):
        from django.utils import timezone  # type: ignore
        asset.meta['last_enrichment'] = timezone.now().isoformat()
        asset.save()

    # Django records ------------------------------------------------------------------
    with asset_update_phase("create_django_records", asset_id):
        _create_django_records_from_collected_data(
            asset,
            govmap_autocomplete_data,
            govmap_data,
            gis_data,
            gov_data,
            plans,
            mavat_plans,
            normalized_listings,
        )

    # Documents & plans ---------------------------------------------------------------
    with asset_update_phase("create_documents_and_plans", asset_id):
        _create_documents_and_plans(asset, gis_data, gov_data, plans, mavat_plans)

    # Market metrics ------------------------------------------------------------------
    with asset_update_phase("calculate_market_metrics", asset_id):
        _calculate_market_metrics(asset, normalized_listings, gov_data)

    logger.info("Updated asset %s with block=%s, parcel=%s", asset_id, block, parcel)


def _create_asset_snapshot(asset_id: int, results: List[Any]) -> None:
    """Create a snapshot of asset data for alert evaluation."""
    try:
        import os
        import sys
        
        # Add Django backend to path
        backend_path = os.path.join(os.path.dirname(__file__), "..", "backend-django")
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        import django
        if not django.conf.settings.configured:
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
            django.setup()
        
        from core.models import Asset, Snapshot
        
        asset = Asset.objects.get(id=asset_id)
        
        # Extract relevant data from results
        payload = {
            'price': asset.price,
            'price_per_sqm': asset.price_per_sqm,
            'area': asset.area,
            'rooms': asset.rooms,
            'permit_status': asset.permit_status,
            'permit_date': asset.permit_date.isoformat() if asset.permit_date else None,
            'documents': [],  # This would be populated from source records
            'gov_transactions': [],  # This would be populated from gov data
            'listing_id': None,  # This would be populated from Yad2 data
        }
        
        # Add data from results
        for result in results:
            if isinstance(result, dict):
                if result.get('source') == 'yad2':
                    # Extract Yad2 data
                    yad2_data = result.get('data', {})
                    if hasattr(yad2_data, 'listing_id'):
                        payload['listing_id'] = yad2_data.listing_id
                elif result.get('source') == 'transactions':
                    # Extract transaction data
                    payload['gov_transactions'] = result.get('data', [])
                elif result.get('source') == 'gis':
                    # Extract GIS data
                    gis_data = result.get('data', {})
                    if gis_data:
                        payload.update({
                            'blocks': gis_data.get('blocks', []),
                            'parcels': gis_data.get('parcels', []),
                            'permits': gis_data.get('permits', []),
                            'rights': gis_data.get('rights', []),
                            'shelters': gis_data.get('shelters', []),
                            'green': gis_data.get('green', []),
                            'noise': gis_data.get('noise', []),
                            'antennas': gis_data.get('antennas', []),
                            'block': gis_data.get('block', ''),
                            'parcel': gis_data.get('parcel', ''),
                            'x': gis_data.get('x'),
                            'y': gis_data.get('y')
                        })
                elif result.get('source') == 'gov_rami':
                    # Extract RAMI plans data
                    payload['rami_plans'] = result.get('data', [])
                elif result.get('source') == 'mavat':
                    # Extract Mavat plans data
                    payload['mavat_plans'] = result.get('data', [])
            elif hasattr(result, 'listing_id'):
                # Direct Yad2 listing object
                payload['listing_id'] = result.listing_id
                if hasattr(result, 'price'):
                    payload['price'] = result.price
                if hasattr(result, 'rooms'):
                    payload['rooms'] = result.rooms
                if hasattr(result, 'size'):
                    payload['area'] = result.size
        
        # Create snapshot
        Snapshot.objects.create(
            asset=asset,
            payload=payload,
            ppsqm=asset.price_per_sqm
        )
        
        logger.info("Created snapshot for asset %s", asset_id)
        
    except Exception as e:
        logger.error("Failed to create snapshot for asset %s: %s", asset_id, e)


def _process_gis_data(asset, gis_data):
    """Process GIS data and store using unified metadata structure."""
    # Noise levels
    if gis_data.get('noise'):
        noise_levels = gis_data.get('noise', [])
        if noise_levels:
            max_noise = max([n.get('isov3', 0) for n in noise_levels if isinstance(n, dict)])
            asset.set_property('noiseLevel', max_noise, source='GIS', url='https://www.govmap.gov.il/')
    
    # Land use rights and zoning
    if gis_data.get('rights'):
        rights = gis_data.get('rights', [])
        if rights:
            main_rights = rights[0] if rights else {}
            asset.set_property('zoning', main_rights.get('land_use', ''), source='GIS', url='https://www.govmap.gov.il/')
            asset.set_property('program', main_rights.get('plan_name', ''), source='GIS', url='https://www.govmap.gov.il/')
            
            # Building rights estimation - try to get real data from privilege pages
            area_for_calculation = asset.area or 80  # Default to 80 sqm if no area
            
            # Try to get real building rights data
            remaining_rights_sqm = None
            source = 'GIS (calculated)'
            
            # Check if we have privilege page data
            privilege_data = asset.get_property_value('privilege_page_data')
            if privilege_data:
                try:
                    from gis.rights_calculator import get_remaining_rights_sqm
                    remaining_rights_sqm = get_remaining_rights_sqm(
                        privilege_data, 
                        area_for_calculation
                    )
                    if remaining_rights_sqm:
                        source = 'GIS (privilege page)'
                except Exception as e:
                    logger.warning(f"Failed to calculate rights from privilege page: {e}")
            
            asset.set_property('remainingRightsSqm', remaining_rights_sqm, source=source, url='https://www.govmap.gov.il/')
            asset.set_property('mainRightsSqm', int(area_for_calculation), source='GIS (calculated)', url='https://www.govmap.gov.il/')
            # Only calculate service rights if remaining_rights_sqm is not None
            service_rights_sqm = int(remaining_rights_sqm * 0.1) if remaining_rights_sqm is not None else None
            asset.set_property('serviceRightsSqm', service_rights_sqm, source='GIS (calculated)', url='https://www.govmap.gov.il/')

    # Building permits
    if gis_data.get('permits'):
        permits = gis_data.get('permits', [])
        if permits:
            recent_permit = permits[0] if permits else {}
            asset.set_property('permitStatus', recent_permit.get('building_stage', ''), source='GIS', url='https://www.govmap.gov.il/')
            if recent_permit.get('permission_date'):
                try:
                    from datetime import datetime
                    permit_date = datetime.fromtimestamp(recent_permit['permission_date'] / 1000)
                    asset.set_property('permitDate', permit_date.date(), source='GIS', url='https://www.govmap.gov.il/')
                except Exception as e:
                    logger.debug(f"Failed to parse permit date: {e}")
                    pass
            
            # Create documents from permits
            _create_documents_from_permits(asset, permits)
    
    # Green areas
    if gis_data.get('green'):
        green_areas = gis_data.get('green', [])
        asset.set_property('greenWithin300m', len(green_areas) > 0, source='GIS', url='https://www.govmap.gov.il/')
    
    # Shelters
    if gis_data.get('shelters'):
        shelters = gis_data.get('shelters', [])
        if shelters:
            min_distance = min([s.get('distance', 999) for s in shelters if isinstance(s, dict)])
            asset.set_property('shelterDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # Cell antennas
    if gis_data.get('antennas'):
        antennas = gis_data.get('antennas', [])
        if antennas:
            min_distance = min([a.get('distance', 999) for a in antennas if isinstance(a, dict)])
            asset.set_property('antennaDistanceM', min_distance, source='GIS', url='https://www.govmap.gov.il/')
    
    # Environmental fields
    asset.set_property('publicTransport', 'קרוב לתחבורה ציבורית', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Get greenWithin300m value for conditional logic
    green_within_300m = asset.get_property_value('greenWithin300m')
    asset.set_property('openSpacesNearby', 'פארקים ושטחים פתוחים בקרבת מקום' if green_within_300m else 'אין שטחים פתוחים קרובים', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    asset.set_property('publicBuildings', 'מבני ציבור בקרבת מקום', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    asset.set_property('parking', 'חניה זמינה', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    asset.set_property('nearbyProjects', 'פרויקטים חדשים באזור', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Additional planning fields
    asset.set_property('additionalPlanRights', 'אין זכויות נוספות', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    asset.set_property('publicObligations', 'אין חובות ציבוריות', source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
    # Permit quarter (extract from permit data)
    if gis_data.get('permits'):
        permits = gis_data.get('permits', [])
        if permits:
            recent_permit = permits[0] if permits else {}
            if recent_permit.get('permission_date'):
                try:
                    from datetime import datetime
                    permit_date = datetime.fromtimestamp(recent_permit['permission_date'] / 1000)
                    quarter = f"Q{(permit_date.month - 1) // 3 + 1}/{permit_date.year}"
                    asset.set_property('lastPermitQ', quarter, source='GIS', url='https://www.govmap.gov.il/')
                except Exception as e:
                    logger.debug(f"Failed to parse permit date: {e}")
                    pass
    
    # Risk flags - use get_property_value for unified access
    risk_flags = []
    noise_level = asset.get_property_value('noiseLevel') or 0
    if noise_level > 3:
        risk_flags.append('רעש גבוה')
    if not green_within_300m:
        risk_flags.append('אין שטחים פתוחים קרובים')
    shelter_distance = asset.get_property_value('shelterDistanceM') or 999
    if shelter_distance > 200:
        risk_flags.append('מרחק גדול ממקלט')
    antenna_distance = asset.get_property_value('antennaDistanceM') or 999
    if antenna_distance < 50:
        risk_flags.append('קרוב מדי לאנטנה')
    asset.set_property('riskFlags', risk_flags, source='GIS (calculated)', url='https://www.govmap.gov.il/')


def _process_government_data(asset, gov_data):
    """Process government data using unified metadata structure."""
    # Transaction data
    if gov_data.get('transactions'):
        transactions = gov_data.get('transactions', [])
        asset.set_property('competition1km', len(transactions), source='Nadlan', url='https://nadlan.gov.il/')
    
    # Decisive appraisals
    if gov_data.get('decisive'):
        decisive = gov_data.get('decisive', [])
        if decisive:
            latest_appraisal = decisive[0] if decisive else {}
            asset.set_property('appraisalValue', latest_appraisal.get('appraised_value'), source='מנהל התכנון', url='https://www.gov.il/')
            asset.set_property('appraisalDate', latest_appraisal.get('appraisal_date'), source='מנהל התכנון', url='https://www.gov.il/')
            
            # Create documents from appraisals
            _create_documents_from_appraisals(asset, decisive)


def _process_rami_plans(asset, plans):
    """Process RAMI plans using unified metadata structure."""
    if plans:
        # Look for active plans
        active_plans = [p for p in plans if p.get('status') and 'פעיל' in p.get('status', '')]
        if active_plans:
            latest_plan = active_plans[0]
            asset.set_property('planStatus', latest_plan.get('status', ''), source='RAMI', url='https://rami.gov.il/')
            asset.set_property('planActive', True, source='RAMI', url='https://rami.gov.il/')
        else:
            asset.set_property('planActive', False, source='RAMI', url='https://rami.gov.il/')

        # Create documents from RAMI plans
        _create_documents_from_rami_plans(asset, plans)


def _process_mavat_plans(asset, mavat_plans):
    """Process Mavat plans using unified metadata structure."""
    if mavat_plans:
        asset.set_property('mavatPlanCount', len(mavat_plans), source='Mavat', url='https://mavat.gov.il/')
        if mavat_plans:
            latest_plan = mavat_plans[0]
            asset.set_property('mavatPlanStatus', latest_plan.get('status', ''), source='Mavat', url='https://mavat.gov.il/')


def _process_govmap_autocomplete_data(asset, govmap_autocomplete_data):
    """Process GovMap autocomplete data using unified metadata structure."""
    try:
        res = govmap_autocomplete_data.get("res", {})
        
        # Extract address information from different categories
        for category in ["BUILDING", "STREET", "NEIGHBORHOOD", "POI_MID_POINT", "SETTLEMENT"]:
            items = res.get(category, [])
            if items:
                # Use the first item from the highest priority category
                first_item = items[0]
                if first_item.get("Value"):
                    asset.set_property(f'govmap_{category.lower()}_name', first_item.get("Value"), source='GovMap Autocomplete', url='https://www.govmap.gov.il/')
                if first_item.get("Text"):
                    asset.set_property(f'govmap_{category.lower()}_text', first_item.get("Text"), source='GovMap Autocomplete', url='https://www.govmap.gov.il/')
                break  # Use only the first matching category
        
        # Set primary address source
        asset.set_property('addressSource', 'GovMap Autocomplete', source='GovMap', url='https://www.govmap.gov.il/')
        
    except Exception as e:
        logger.warning(f"Failed to process GovMap autocomplete data: {e}")


def _process_govmap_data(asset, govmap_data):
    """Process GovMap parcel data using unified metadata structure."""
    # Process parcel data from api_data
    if govmap_data.get('api_data', {}).get('parcel'):
        parcel = govmap_data.get('api_data', {}).get('parcel', {})
        # Extract parcel information
        if parcel.get('gush'):
            asset.set_property('govmapGush', parcel.get('gush'), source='GovMap', url='https://www.govmap.gov.il/')
        if parcel.get('helka'):
            asset.set_property('govmapHelka', parcel.get('helka'), source='GovMap', url='https://www.govmap.gov.il/')
        if parcel.get('land_use'):
            asset.set_property('govmapLandUse', parcel.get('land_use'), source='GovMap', url='https://www.govmap.gov.il/')

    # Process nearby layers data (if available in the future)
    if govmap_data.get('nearby'):
        nearby = govmap_data.get('nearby', {})
        for layer_name, features in nearby.items():
            if features:
                asset.set_property(f'govmap_{layer_name}_count', len(features), source='GovMap', url='https://www.govmap.gov.il/')


def _create_django_records_from_collected_data(asset, govmap_autocomplete_data, govmap_data, gis_data, gov_data, plans, mavat_plans, listings):
    """Create Django model records (SourceRecord, RealEstateTransaction) from collected data.

    Handles potential IntegrityError when UNIQUE(source, external_id) already exists for another asset by
    safely retrieving the existing record and skipping creation instead of failing the whole enrichment.
    """
    from core.models import SourceRecord, RealEstateTransaction
    from django.db import IntegrityError

    def _safe_source_record_create(source: str, external_id: str, defaults: dict):
        """Create a SourceRecord guarding against UNIQUE(source, external_id) conflicts.

        If a record with the same (source, external_id) exists for another asset, we log and skip.
        """
        if not external_id:
            return None
        try:
            obj, created = SourceRecord.objects.get_or_create(
                source=source,  # use only the unique fields in the lookup
                external_id=str(external_id),
                defaults={**defaults, 'asset': asset},
            )
            # If the record exists but belongs to a different asset, do not reassociate (one-to-one style ownership)
            if not created and obj.asset_id != asset.id:
                logger.debug(
                    "SourceRecord (%s,%s) already linked to asset %s; skipping for asset %s",
                    source, external_id, obj.asset_id, asset.id,
                )
            return obj
        except IntegrityError:
            # Rare race condition: object created concurrently after the initial existence check
            existing = SourceRecord.objects.filter(source=source, external_id=str(external_id)).first()
            if existing:
                if existing.asset_id != asset.id:
                    logger.debug(
                        "(race) SourceRecord (%s,%s) already linked to asset %s; skipping for asset %s",
                        source, external_id, existing.asset_id, asset.id,
                    )
                return existing
            logger.warning(
                "IntegrityError creating SourceRecord (%s,%s) for asset %s; record not created",
                source, external_id, asset.id,
            )
            return None

    normalized_listings = _normalize_listings(listings or [])

    # Create SourceRecord for Yad2 listings
    if listings and not normalized_listings:
        logger.debug("All listings dropped while normalizing listings for Django source records on asset %s", asset.id)

    if normalized_listings:
        for listing in normalized_listings:
            if listing.get('listing_id'):
                _safe_source_record_create(
                    source='yad2',
                    external_id=str(listing.get('listing_id')),
                    defaults={
                        'title': listing.get('title', ''),
                        'url': listing.get('url', ''),
                        'raw': listing,
                    },
                )

    # Create SourceRecord for RAMI plans
    if plans:
        for plan in plans:
            plan_number = plan.get('planNumber') or plan.get('plan_number', '')
            if plan_number:
                _safe_source_record_create(
                    source='rami_plan',
                    external_id=str(plan_number),
                    defaults={
                        'title': plan.get('title', f'תכנית רמ״י {plan_number}'),
                        'url': plan.get('url', ''),
                        'raw': plan,
                    },
                )

    # Create SourceRecord for Mavat plans
    if mavat_plans:
        for plan in mavat_plans:
            plan_id = plan.get('plan_id') or plan.get('id', '')
            if plan_id:
                _safe_source_record_create(
                    source='tabu',  # Using 'tabu' as closest match for Mavat
                    external_id=str(plan_id),
                    defaults={
                        'title': plan.get('title', f'תכנית מבת {plan_id}'),
                        'url': plan.get('url', ''),
                        'raw': plan,
                    },
                )

    # Create SourceRecord for GIS data
    if gis_data:
        if gis_data.get('permits'):
            _safe_source_record_create(
                source='gis_permit',
                external_id=f"permits_{asset.id}",  # keep asset-specific external id
                defaults={
                    'title': 'היתרי בנייה',
                    'raw': gis_data,
                },
            )

        if gis_data.get('rights'):
            _safe_source_record_create(
                source='gis_rights',
                external_id=f"rights_{asset.id}",
                defaults={
                    'title': 'זכויות בנייה',
                    'raw': gis_data,
                },
            )

    # Create RealEstateTransaction records from government data
    if gov_data and gov_data.get('transactions'):
        for transaction in gov_data.get('transactions', []):
            if transaction.get('deal_id'):
                # deal_id expected unique globally; safe to lookup by it only
                try:
                    RealEstateTransaction.objects.get_or_create(
                        deal_id=str(transaction.get('deal_id')),
                        defaults={
                            'asset': asset,
                            'date': transaction.get('date'),
                            'price': transaction.get('price'),
                            'rooms': transaction.get('rooms'),
                            'area': transaction.get('area'),
                            'floor': transaction.get('floor'),
                            'address': transaction.get('address'),
                            'raw': transaction,
                        },
                    )
                except IntegrityError:
                    # If exists, we do not re-link to a different asset
                    pass

def _calculate_market_metrics(asset, listings, gov_data):
    """Calculate and persist market metrics.

    - Computes metrics from Yad2 listings (prices, areas)
    - Derives confidence, competition, rent estimate, cap rate, DOM percentile
    - Generates risk flags heuristically
    - Stores camelCase metrics in asset.meta['market_metrics'] for backward compatibility
    - Maps a subset to snake_case Asset fields
    """
    try:
        listing_dicts = _normalize_listings(listings or []) if listings else []
        metrics: Dict[str, Any] = {}

        # --- Price / Area derived metrics ---
        if listing_dicts:
            prices = [l.get('price') for l in listing_dicts if l.get('price')]
            areas = [l.get('area') for l in listing_dicts if l.get('area')]

            if prices:
                avg_price = sum(prices) / len(prices)
                metrics['modelPrice'] = int(avg_price)
                metrics['expectedPriceRange'] = f"{min(prices):,} - {max(prices):,}"
                if asset.price and avg_price > 0:
                    metrics['priceGapPct'] = round(((asset.price - avg_price) / avg_price) * 100, 2)
                # Confidence: 20% per comp up to 100
                metrics['confidencePct'] = min(100, len(prices) * 20)
            else:
                metrics['confidencePct'] = 0

            if areas and asset.area:
                avg_area = sum(areas) / len(areas)
                if avg_area > 0:
                    metrics['deltaVsAreaPct'] = round(((asset.area - avg_area) / avg_area) * 100, 2)

            # Competition heuristic based on number of listings
            n = len(listing_dicts)
            if n > 10:
                metrics['competition1km'] = 'גבוהה'
            elif n > 5:
                metrics['competition1km'] = 'בינונית'
            else:
                metrics['competition1km'] = 'נמוכה'

            # DOM percentile heuristic (coarse)
            metrics['domPercentile'] = min(90, n * 10)
        else:
            # No comps -> low confidence baseline
            metrics['confidencePct'] = 0

        # --- Rent & Cap Rate ---
        if asset.area and asset.price:  # need both for cap rate
            rent_estimate = asset.area * 65  # simple heuristic (NIS / sqm)
            metrics['rentEstimate'] = int(rent_estimate)
            annual_rent = rent_estimate * 12
            if asset.price > 0:
                metrics['capRatePct'] = round((annual_rent / asset.price) * 100, 2)

        # --- Risk Flags ---
        risk_flags = []
        if abs(metrics.get('priceGapPct', 0)) > 20:
            risk_flags.append('פער מחיר גבוה')
        if abs(metrics.get('deltaVsAreaPct', 0)) > 30:
            risk_flags.append('פער שטח גבוה')
        if metrics.get('confidencePct', 0) < 40:
            risk_flags.append('ביטחון נמוך')
        metrics['riskFlags'] = risk_flags

        # --- Persist to meta (camelCase retained) ---
        if not asset.meta:
            asset.meta = {}
        asset.meta['market_metrics'] = metrics

        # --- Map camelCase to snake_case model fields ---
        field_map = {
            'priceGapPct': 'price_gap_pct',
            'expectedPriceRange': 'expected_price_range',
            'modelPrice': 'model_price',
            'confidencePct': 'confidence_pct',
            'deltaVsAreaPct': 'delta_vs_area_pct',
            'capRatePct': 'cap_rate_pct',
            'competition1km': 'competition_1km',
            'riskFlags': 'risk_flags',
            'domPercentile': 'dom_percentile',
            'rentEstimate': 'rent_estimate',
        }
        update_fields = {'meta'}
        for camel, snake in field_map.items():
            if camel in metrics and hasattr(asset, snake):
                setattr(asset, snake, metrics[camel])
                update_fields.add(snake)

        asset.save(update_fields=list(update_fields))
        logger.debug('[MARKET_METRICS] asset=%s metrics=%s', asset.id, metrics)
    except Exception as e:  # pragma: no cover - defensive
        logger.error('Failed to calculate market metrics for asset %s: %s', getattr(asset, 'id', '?'), e)


def _create_documents_and_plans(asset, gis_data, gov_data, plans, mavat_plans):
    """Create Document and Plan records from collected data."""
    try:
        User = get_user_model()
        
        # Get or create a system user for automated documents
        system_user, created = User.objects.get_or_create(
            email='system@nadlaner.com',
            defaults={
                'first_name': 'System',
                'last_name': 'User',
                'is_active': False
            }
        )
        
        # Create Document records from GIS permits
        if gis_data and gis_data.get('permits'):
            for permit in gis_data.get('permits', []):
                if permit.get('permit_number'):
                    Document.objects.get_or_create(
                        asset=asset,
                        external_id=permit.get('permit_number'),
                        defaults={
                            'user': system_user,
                            'title': f"היתר בנייה {permit.get('permit_number')}",
                            'description': f"היתר בנייה מספר {permit.get('permit_number')}",
                            'document_type': 'permit',
                            'status': 'approved',
                            'external_url': permit.get('url', ''),
                            'source': 'gis',
                            'document_date': permit.get('date'),
                            'meta': permit
                        }
                    )
        
        # Create Document records from government appraisals
        if gov_data and gov_data.get('decisive'):
            for appraisal in gov_data.get('decisive', []):
                if appraisal.get('id'):
                    Document.objects.get_or_create(
                        asset=asset,
                        external_id=appraisal.get('id'),
                        defaults={
                            'user': system_user,
                            'title': f"שומה החלטית {appraisal.get('id')}",
                            'description': f"שומה החלטית מספר {appraisal.get('id')}",
                            'document_type': 'appraisal_decisive',
                            'status': 'approved',
                            'external_url': appraisal.get('url', ''),
                            'source': 'gov',
                            'document_date': appraisal.get('date'),
                            'meta': appraisal
                        }
                    )
        
        # Create Plan records from RAMI plans
        if plans:
            for plan in plans:
                plan_number = plan.get('planNumber') or plan.get('plan_number', '')
                if plan_number:
                    Plan.objects.get_or_create(
                        asset=asset,
                        plan_number=plan_number,
                        defaults={
                            'description': plan.get('title', f'תכנית רמ״י {plan_number}'),
                            'status': plan.get('status', ''),
                            'file_url': plan.get('url', ''),
                            'raw': plan
                        }
                    )
        
        # Create Plan records from Mavat plans
        if mavat_plans:
            for plan in mavat_plans:
                plan_id = plan.get('plan_id') or plan.get('id', '')
                if plan_id:
                    Plan.objects.get_or_create(
                        asset=asset,
                        plan_number=f"mavat_{plan_id}",
                        defaults={
                            'description': plan.get('title', f'תכנית מבת {plan_id}'),
                            'status': plan.get('status', ''),
                            'file_url': plan.get('url', ''),
                            'raw': plan
                        }
                    )
        
        logger.info(f"Created documents and plans for asset {asset.id}")
        
    except Exception as e:
        logger.error(f"Failed to create documents and plans for asset {asset.id}: {e}")


def _create_documents_from_permits(asset, permits):
    """Create documents from GIS permits data."""
    print("Permits:" + str(permits))
    if not permits:
        return
    # Get a system user or create one for automated processes
    User = get_user_model()
    system_user, _ = User.objects.get_or_create(
        username='system',
        defaults={
            'email': 'system@realestate.com',
            'first_name': 'System',
            'last_name': 'Pipeline'
        }
    )

    # Create documents for each permit
    created_count = 0
    for permit in permits:
        if not permit:
            continue
            
        # Extract permit information
        permit_id = permit.get('request_num', permit.get('permission_num', ''))
        permit_number = permit.get('permission_num', '')
        request_number = permit.get('request_num', '')
        description = permit.get('building_stage', '')
        status = permit.get('building_stage', '')
        address = permit.get('addresses', '')
        url = permit.get('url_hadmaya', '')
        
        # Convert timestamp to date
        permit_date = None
        if permit.get('permission_date'):
            try:
                permit_date = datetime.fromtimestamp(permit['permission_date'] / 1000).date()
            except Exception as e:
                logger.debug(f"Failed to parse permit date: {e}")
                pass
        
        # Check if document already exists to avoid duplicates
        existing_doc = Document.objects.filter(
            asset=asset,
            document_type='permit',
            external_id=permit_id
        ).first()

        if existing_doc:
            # Update existing document
            existing_doc.title = f"היתר בניה - {description}" if description else "היתר בניה"
            existing_doc.description = description
            existing_doc.status = status
            existing_doc.document_date = permit_date
            existing_doc.external_url = url
            existing_doc.source = 'GIS'
            existing_doc.meta = {
                'permit_number': permit_number,
                'request_number': request_number,
                'address': address,
                'building_stage': description,
                'url_hadmaya': url,
                'permission_date': permit.get('permission_date'),
                'issued_date': permit.get('issued_date'),
                'addresses': address
            }
            existing_doc.save()
            logger.debug(f"Updated existing permit document {existing_doc.id} for asset {asset.id}")
        else:
            # Create new document
            document = Document.objects.create(
                asset=asset,
                user=system_user,
                title=f"היתר בניה - {description}" if description else "היתר בניה",
                description=description,
                document_type='permit',
                status='approved' if status else 'pending',
                filename=f"permit_{permit_id}.pdf" if permit_id else f"permit_{created_count + 1}.pdf",
                file_path='',  # No physical file for GIS permits
                file_size=0,
                mime_type='application/pdf',
                external_id=permit_id,
                external_url=url,
                source='GIS',
                document_date=permit_date,
                meta={
                    'permit_number': permit_number,
                    'request_number': request_number,
                    'address': address,
                    'building_stage': description,
                    'url_hadmaya': url,
                    'permission_date': permit.get('permission_date'),
                    'issued_date': permit.get('issued_date'),
                    'addresses': address
                }
            )
            created_count += 1
            logger.debug(f"Created permit document {document.id} for asset {asset.id}")

    logger.info(f"Processed {len(permits)} permits for asset {asset.id} ({created_count} new, {len(permits) - created_count} updated)")


def _create_documents_from_appraisals(asset, appraisals):
    """Create documents from government appraisals data."""
    if not appraisals:
        return
    
    # Initialize documents array if it doesn't exist
    if 'documents' not in asset.meta:
        asset.meta['documents'] = []
    
    # Create documents for each appraisal
    for appraisal in appraisals:
        if not appraisal:
            continue
            
        # Extract appraisal information
        appraiser = appraisal.get('appraiser', 'לא זמין')
        appraised_value = appraisal.get('appraised_value', appraisal.get('value'))
        appraisal_date = appraisal.get('appraisal_date', appraisal.get('date'))
        url = appraisal.get('url', '')
        
        # Validate and clean URL
        if url and not url.startswith(('http://', 'https://')):
            if url.startswith('/'):
                url = f"https://www.gov.il{url}"
            else:
                url = f"https://www.gov.il/{url}"
        
        # Create document entry
        document = {
            'id': f"appraisal_{len(asset.meta['documents']) + 1}",
            'type': 'appraisal',
            'title': f"שומה מכריעה - {appraiser}",
            'description': f"שומה מכריעה על ידי {appraiser}",
            'status': 'מאושר',
            'date': appraisal_date,
            'url': url,
            'source': 'מנהל התכנון',
            'appraiser': appraiser,
            'appraised_value': appraised_value,
            'downloadable': bool(url and url.startswith(('http://', 'https://')))
        }
        
        asset.meta['documents'].append(document)
    
    logger.info(f"Created {len(appraisals)} appraisal documents for asset {asset.id}")


def _create_documents_from_rami_plans(asset, plans):
    """Create documents from RAMI plans data (robust to missing/None sub-keys)."""
    if not plans:
        return

    # Initialize documents array if it doesn't exist
    if 'documents' not in asset.meta:
        asset.meta['documents'] = []

    created = 0
    for plan in plans or []:
        if not isinstance(plan, dict):
            continue

        plan_number = _first_nonempty(
            plan.get('planNumber'),
            plan.get('plan_number'),
            plan.get('number'),
        )
        plan_name = _first_nonempty(
            plan.get('title'),
            plan.get('plan_name'),
            plan.get('name'),
        )
        status = plan.get('status', '')

        # documentsSet can be {}, None, or missing entirely — handle all
        raw = plan.get('raw') or {}
        documents_set = raw.get('documentsSet') or {}

        # child entries can be dicts or None — guard each before reading 'path'
        map_entry     = _safe_get(documents_set, 'map')
        takanon_entry = _safe_get(documents_set, 'takanon')
        mmg_entry     = _safe_get(documents_set, 'mmg')

        url = _first_nonempty(
            _safe_get(map_entry, 'path'),
            _safe_get(takanon_entry, 'path'),
            _safe_get(mmg_entry, 'path'),
            plan.get('url'),  # last resort if provided on the plan itself
        ) or ''

        # Normalize RAMI relative URLs
        if url and not url.startswith(('http://', 'https://')):
            if url.startswith('/'):
                url = f"https://rami.gov.il{url}"
            else:
                url = f"https://rami.gov.il/{url}"

        document = {
            'id': f"rami_plan_{plan_number}" if plan_number else f"rami_plan_{len(asset.meta['documents']) + 1}",
            'type': 'plan',
            'title': f"תכנית רמ״י - {plan_name}" if plan_name else (f"תכנית רמ״י {plan_number}" if plan_number else "תכנית רמ״י"),
            'description': f"תכנית רמ״י {plan_number}" if plan_number else "תכנית רמ״י",
            'status': status,
            'date': plan.get('statusDate', plan.get('date', '')),
            'url': url,
            'source': 'RAMI',
            'plan_number': plan_number,
            'plan_name': plan_name,
            'downloadable': bool(url and url.startswith(('http://', 'https://')))
        }

        asset.meta['documents'].append(document)
        created += 1

    logger.info("Created %d RAMI plan documents for asset %s", created, asset.id)

# ---------------------------------------------------------------------------
# Improved debugging helpers
# ---------------------------------------------------------------------------

@contextmanager
def asset_update_phase(phase: str, asset_id: int | None = None):
    """Context manager to add granular logging & exception tracing to asset update.

    Each logical phase in ``_update_asset_with_collected_data`` is wrapped in this
    context so that if one phase fails we still continue (best‑effort enrichment)
    while having a clear stack trace & phase name in the logs.
    """
    t0 = time.perf_counter()
    logger.debug("[ASSET_UPDATE] ▶ phase=%s asset_id=%s", phase, asset_id)
    try:
        yield
        dt = (time.perf_counter() - t0) * 1000
        logger.debug("[ASSET_UPDATE] ✔ phase=%s asset_id=%s duration_ms=%d", phase, asset_id, dt)
    except Exception as exc:  # noqa: BLE001 - we purposefully capture & log all
        dt = (time.perf_counter() - t0) * 1000
        logger.exception(
            "[ASSET_UPDATE] ✖ phase=%s asset_id=%s duration_ms=%d error=%s", phase, asset_id, dt, exc
        )
        debug = os.getenv("ASSET_UPDATE_DEBUG", "0").lower() in {"1", "true", "yes"}
        if debug:
            raise
