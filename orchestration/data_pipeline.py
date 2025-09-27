from __future__ import annotations

from typing import Any, Iterable, List, Optional, Dict, Tuple
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from types import SimpleNamespace

from sqlalchemy.orm import Session

from db.database import SQLAlchemyDatabase
from db.models import Listing, SourceRecord, Transaction
from yad2.scrapers.yad2_scraper import RealEstateListing

# collector imports
from orchestration.collectors.yad2_collector import Yad2Collector
from orchestration.collectors.gis_collector import GISCollector
from orchestration.collectors.gov_collector import GovCollector
from orchestration.collectors.govmap_collector import GovMapCollector
from orchestration.collectors.rami_collector import RamiCollector
from orchestration.collectors.mavat_collector import MavatCollector
from govmap.api_client import itm_to_wgs84
from orchestration.observability import (
    COLLECTOR_FAILURE,
    COLLECTOR_LATENCY,
    COLLECTOR_SUCCESS,
    start_metrics_server,
    tracer,
)

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

    from core.models import AlertRule  # type: ignore
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
        normalized.append(_listing_to_dict(listing))
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
        for d in deals:
            raw = d.to_dict() if hasattr(d, "to_dict") else dict(d)
            session.add(
                Transaction(
                    listing_id=listing_id,
                    deal_date=raw.get("deal_date"),
                    deal_amount=raw.get("deal_amount"),
                    rooms=raw.get("rooms"),
                    floor=raw.get("floor"),
                    asset_type=raw.get("asset_type"),
                    year_built=raw.get("year_built"),
                    area=raw.get("area"),
                    raw=raw,
                )
            )

    # ------------------------------------------------------------------
    def run(
        self, address: str, house_number: int, max_pages: int = 1, asset_id: Optional[int] = None
    ) -> List[Any]:
        """Run the pipeline for a given address.

        The function still persists results to the database but also returns a
        list of raw objects/dictionaries representing the collected data.  This
        makes the pipeline easier to test in isolation.
        """
        
        logger.info(f"🚀 Starting data pipeline for {address} {house_number} (max_pages={max_pages})")
        start_time = time.perf_counter()

        with tracer.start_as_current_span(
            "data_pipeline.run",
            attributes={"address": address, "house_number": house_number, "max_pages": max_pages},
        ):
            # Search Yad2 for listings
            try:
                listings = self._collect_with_observability(
                    "yad2",
                    self.yad2.collect,
                    address=address,
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
                full_address = f"{address} {house_number}" if house_number else address
                govmap_data = self._collect_with_observability(
                    "govmap",
                    self.govmap.collect,
                    address=full_address,
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
                parcel_info = govmap_data.get("api_data", {}).get("parcel", {})
                block = parcel_info.get("gush", "")
                parcel = parcel_info.get("helka", "")
            
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
                    address=address,
                    house_number=house_number,
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
                # If GIS geocoding failed but we have coordinates from GovMap, try using those
                if x_itm is not None and y_itm is not None:
                    logger.info(f"🔄 GIS geocoding failed, trying with GovMap coordinates: ITM({x_itm}, {y_itm})")
                    try:
                        # Use GovMap coordinates directly for GIS data collection
                        gis_data = {
                            "blocks": self.gis.client.get_blocks(x_itm, y_itm),
                            "parcels": self.gis.client.get_parcels(x_itm, y_itm),
                            "permits": self.gis.client.get_building_permits(x_itm, y_itm),
                            "rights": self.gis.client.get_land_use_main(x_itm, y_itm),
                            "shelters": self.gis.client.get_shelters(x_itm, y_itm),
                            "green": self.gis.client.get_green_areas(x_itm, y_itm),
                            "noise": self.gis.client.get_noise_levels(x_itm, y_itm),
                            "antennas": self.gis.client.get_cell_antennas(x_itm, y_itm),
                        }
                        block_gis, parcel_gis = self.gis._extract_block_parcel(gis_data)
                        gis_data.update({"block": block_gis, "parcel": parcel_gis, "x": x_itm, "y": y_itm})
                        track("collector_success", source="gis")
                        logger.info(f"✅ GIS data collected using GovMap coordinates: block={block_gis}, parcel={parcel_gis}")
                    except Exception as coord_e:
                        logger.warning(f"⚠️ Failed to collect GIS data with GovMap coordinates: {coord_e}")
                        gis_data = {}
                        track("collector_fail", source="gis", error_code=str(coord_e))
                else:
                    gis_data = {}
                    track("collector_fail", source="gis", error_code=str(e))
                    logger.warning(f"⚠️ GIS collection failed: {e}")
                
                # Use GIS coordinates as fallback if GovMap autocomplete failed
                if x_itm is None and y_itm is None and gis_data.get('x') and gis_data.get('y'):
                    try:
                        x_itm = gis_data.get('x')
                        y_itm = gis_data.get('y')
                        lon_wgs84, lat_wgs84 = itm_to_wgs84(x_itm, y_itm)
                        logger.info(f"📍 Using GIS coordinates as fallback: ITM({x_itm}, {y_itm}) -> WGS84({lon_wgs84:.6f}, {lat_wgs84:.6f})")
                    except Exception as coord_e:
                        logger.warning(f"⚠️ Failed to convert GIS coordinates: {coord_e}")
                
                # Use GIS block/parcel as fallback if GovMap failed
                if not block and gis_data.get('block'):
                    block = gis_data.get('block', '')
                if not parcel and gis_data.get('parcel'):
                    parcel = gis_data.get('parcel', '')
                
                logger.info(f"📍 GIS data collected: block={gis_data.get('block', 'N/A')}, parcel={gis_data.get('parcel', 'N/A')}")
            
            # Get government data once for the address
            gov_data = {"decisive": [], "transactions": []}
            if block and parcel:
                try:
                    logger.info("🏛️ Collecting government data...")
                    # Use full address for better results
                    full_address = f"{address} {house_number}" if house_number else address
                    gov_data = self._collect_with_observability(
                        "gov",
                        self.gov.collect,
                        block=block,
                        parcel=parcel,
                        address=full_address,
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


def _update_asset_with_collected_data(asset_id: int, block: str, parcel: str, govmap_autocomplete_data: Dict[str, Any], govmap_data: Dict[str, Any], gis_data: Dict[str, Any], gov_data: Dict[str, Any], plans: List[Dict[str, Any]], mavat_plans: List[Dict[str, Any]], listings: List[Dict[str, Any]], x_itm: Optional[float] = None, y_itm: Optional[float] = None, lon_wgs84: Optional[float] = None, lat_wgs84: Optional[float] = None) -> None:
    """Update the Asset model with all collected data from GIS, Gov, Mavat, and Yad2."""
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
        
        from core.models import Asset
        
        asset = Asset.objects.get(id=asset_id)
        
        # Update basic asset information
        if block:
            asset.block = block
        if parcel:
            asset.parcel = parcel
            
        # Update coordinates if available (prioritize GovMap coordinates)
        if lon_wgs84 is not None and lat_wgs84 is not None:
            # Use coordinates from GovMap autocomplete (already converted to WGS84)
            asset.lat = lat_wgs84
            asset.lon = lon_wgs84
            logger.info("Updated asset coordinates from GovMap autocomplete", extra={
                "wgs84_lat": lat_wgs84, "wgs84_lon": lon_wgs84,
                "itm_x": x_itm, "itm_y": y_itm
            })
        elif gis_data.get('x') and gis_data.get('y'):
            # Fallback to GIS coordinates if GovMap coordinates not available
            try:
                x_itm_gis = gis_data.get('x')
                y_itm_gis = gis_data.get('y')
                lon_wgs84_gis, lat_wgs84_gis = itm_to_wgs84(x_itm_gis, y_itm_gis)
                asset.lat = lat_wgs84_gis
                asset.lon = lon_wgs84_gis
                logger.info("Updated asset coordinates from GIS (fallback)", extra={
                    "itm_x": x_itm_gis, "itm_y": y_itm_gis, 
                    "wgs84_lat": lat_wgs84_gis, "wgs84_lon": lon_wgs84_gis
                })
            except Exception as e:
                logger.warning("Failed to convert GIS ITM coordinates to WGS84", extra={
                    "error": str(e), "x": gis_data.get('x'), "y": gis_data.get('y')
                })
                # Fallback: store as-is (will be handled by frontend conversion)
                asset.lat = gis_data.get('x')
                asset.lon = gis_data.get('y')
            
        # Update normalized address
        if asset.street and asset.number:
            asset.normalized_address = f"{asset.street} {asset.number}"
            if asset.apartment:
                asset.normalized_address += f" דירה {asset.apartment}"
            if asset.city:
                asset.normalized_address += f" {asset.city}"
        
        # Initialize meta field if it doesn't exist
        if not asset.meta:
            asset.meta = {}
        
        # Update with GIS data
        if gis_data:
            # Store raw GIS data in meta
            asset.meta['gis_data'] = {
                'building_permits': gis_data.get('permits', []),
                'land_use_rights': gis_data.get('rights', []),
                'shelters': gis_data.get('shelters', []),
                'green_areas': gis_data.get('green', []),
                'noise_levels': gis_data.get('noise', []),
                'cell_antennas': gis_data.get('antennas', []),
                'blocks': gis_data.get('blocks', []),
                'parcels': gis_data.get('parcels', []),
                'coordinates': {
                    'x': gis_data.get('x'),
                    'y': gis_data.get('y')
                }
            }
            
            # Try to get building privilege page data for real rights calculation
            try:
                from gis.gis_client import TelAvivGS
                gis_client = TelAvivGS()
                x = gis_data.get('x')
                y = gis_data.get('y')
                
                if x and y:
                    logger.info(f"Attempting to download building privilege page for coordinates ({x}, {y})")
                    privilege_data = gis_client.get_building_privilege_page(x, y, save_dir="privilege_pages")
                    
                    if privilege_data and privilege_data.get('content_type') == 'pdf':
                        # Parse the privilege page
                        from gis.parse_zchuyot import parse_zchuyot
                        pdf_path = privilege_data['file_path']
                        parsed_privilege_data = parse_zchuyot(pdf_path)
                        asset.meta['privilege_page_data'] = parsed_privilege_data
                        logger.info(f"Successfully parsed privilege page: {pdf_path}")
                    elif privilege_data:
                        logger.info(f"Downloaded privilege page but content type is {privilege_data.get('content_type')}, not PDF")
                    else:
                        logger.info("No privilege page data available")
                        
            except Exception as e:
                logger.warning(f"Failed to download/parse building privilege page: {e}")
            
            # Process and store GIS data in both meta and direct fields
            _process_gis_data(asset, gis_data)
        
        # Update with GovMap autocomplete data
        if govmap_autocomplete_data:
            asset.meta['govmap_autocomplete_data'] = {
                'autocomplete_result': govmap_autocomplete_data,
                'coordinates': {
                    'x_itm': x_itm,
                    'y_itm': y_itm,
                    'lon_wgs84': lon_wgs84,
                    'lat_wgs84': lat_wgs84
                }
            }
            _process_govmap_autocomplete_data(asset, govmap_autocomplete_data)
        
        # Update with GovMap parcel data
        if govmap_data:
            asset.meta['govmap_data'] = {
                'parcel': govmap_data.get('api_data', {}).get('parcel', {}),
                'nearby_layers': govmap_data.get('nearby', {}),
                'coordinates': {
                    'x': govmap_data.get('x'),
                    'y': govmap_data.get('y')
                },
                'api_data': govmap_data.get('api_data', {})
            }
            _process_govmap_data(asset, govmap_data)
        
        # Update with government data
        if gov_data:
            asset.meta['government_data'] = {
                'decisive_appraisals': gov_data.get('decisive', []),
                'transaction_history': gov_data.get('transactions', [])
            }
            _process_government_data(asset, gov_data)
        
        # Update with RAMI plans
        if plans:
            asset.meta['rami_plans'] = plans
            _process_rami_plans(asset, plans)
        
        # Update with Mavat plans
        if mavat_plans:
            asset.meta['mavat_plans'] = mavat_plans
            _process_mavat_plans(asset, mavat_plans)
        
        # Update with Yad2 listings
        if listings:
            asset.meta['yad2_listings'] = listings

            prices = [listing.get('price') for listing in listings if listing.get('price')]
            areas = [listing.get('area') for listing in listings if listing.get('area')]

            market_data = asset.meta.setdefault('market_data', {})

            if prices:
                market_data.update(
                    {
                        'min_price': min(prices),
                        'max_price': max(prices),
                        'avg_price': sum(prices) / len(prices),
                        'price_count': len(prices),
                    }
                )

            if areas:
                market_data.update(
                    {
                        'min_area': min(areas),
                        'max_area': max(areas),
                        'avg_area': sum(areas) / len(areas),
                        'area_count': len(areas),
                    }
                )

            if not market_data:
                asset.meta.pop('market_data', None)

        # Update last enrichment timestamp
        from django.utils import timezone
        asset.meta['last_enrichment'] = timezone.now().isoformat()

        asset.save()

        # Create Django model records from collected data
        _create_django_records_from_collected_data(
            asset,
            govmap_autocomplete_data,
            govmap_data,
            gis_data,
            gov_data,
            plans,
            mavat_plans,
            listings,
        )

        # Create Document and Plan records
        _create_documents_and_plans(asset, gis_data, gov_data, plans, mavat_plans)

        # Calculate market metrics
        _calculate_market_metrics(asset, listings, gov_data)
        
        logger.info("Updated asset %s with block=%s, parcel=%s", asset_id, block, parcel)
        
    except Exception as e:
        logger.error("Failed to update asset %s with collected data: %s", asset_id, e)


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
            
            # Fallback to estimated calculation if no real data
            if remaining_rights_sqm is None:
                remaining_rights_sqm = int(area_for_calculation * 0.2)  # 20% additional rights
                source = 'GIS (estimated)'
            
            asset.set_property('remainingRightsSqm', remaining_rights_sqm, source=source, url='https://www.govmap.gov.il/')
            asset.set_property('mainRightsSqm', int(area_for_calculation), source='GIS (calculated)', url='https://www.govmap.gov.il/')
            asset.set_property('serviceRightsSqm', int(remaining_rights_sqm * 0.1), source='GIS (calculated)', url='https://www.govmap.gov.il/')
    
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
    """Create Django model records (SourceRecord, RealEstateTransaction) from collected data."""
    try:
        from core.models import SourceRecord, RealEstateTransaction
        
        # Create SourceRecord for Yad2 listings
        if listings:
            for listing in listings:
                if listing.get('listing_id'):
                    SourceRecord.objects.get_or_create(
                        asset=asset,
                        source='yad2',
                        external_id=str(listing.get('listing_id')),
                        defaults={
                            'title': listing.get('title', ''),
                            'url': listing.get('url', ''),
                            'raw': listing
                        }
                    )
        
        # Create SourceRecord for RAMI plans
        if plans:
            for plan in plans:
                plan_number = plan.get('planNumber') or plan.get('plan_number', '')
                if plan_number:
                    SourceRecord.objects.get_or_create(
                        asset=asset,
                        source='rami_plan',
                        external_id=str(plan_number),
                        defaults={
                            'title': plan.get('title', f'תכנית רמ״י {plan_number}'),
                            'url': plan.get('url', ''),
                            'raw': plan
                        }
                    )
        
        # Create SourceRecord for Mavat plans
        if mavat_plans:
            for plan in mavat_plans:
                plan_id = plan.get('plan_id') or plan.get('id', '')
                if plan_id:
                    SourceRecord.objects.get_or_create(
                        asset=asset,
                        source='tabu',  # Using 'tabu' as closest match for Mavat
                        external_id=str(plan_id),
                        defaults={
                            'title': plan.get('title', f'תכנית מבת {plan_id}'),
                            'url': plan.get('url', ''),
                            'raw': plan
                        }
                    )
        
        # Create SourceRecord for GIS data
        if gis_data:
            if gis_data.get('permits'):
                SourceRecord.objects.get_or_create(
                    asset=asset,
                    source='gis_permit',
                    external_id=f"permits_{asset.id}",
                    defaults={
                        'title': 'היתרי בנייה',
                        'raw': gis_data
                    }
                )
            
            if gis_data.get('rights'):
                SourceRecord.objects.get_or_create(
                    asset=asset,
                    source='gis_rights',
                    external_id=f"rights_{asset.id}",
                    defaults={
                        'title': 'זכויות בנייה',
                        'raw': gis_data
                    }
                )
        
        # Create RealEstateTransaction records from government data
        if gov_data and gov_data.get('transactions'):
            for transaction in gov_data.get('transactions', []):
                if transaction.get('deal_id'):
                    RealEstateTransaction.objects.get_or_create(
                        asset=asset,
                        deal_id=str(transaction.get('deal_id')),
                        defaults={
                            'date': transaction.get('date'),
                            'price': transaction.get('price'),
                            'rooms': transaction.get('rooms'),
                            'area': transaction.get('area'),
                            'floor': transaction.get('floor'),
                            'address': transaction.get('address'),
                            'raw': transaction
                        }
                    )
        
        logger.info(f"Created Django records for asset {asset.id}")
        
    except Exception as e:
        logger.error(f"Failed to create Django records for asset {asset.id}: {e}")


def _calculate_market_metrics(asset, listings, gov_data):
    """Calculate market metrics for the asset based on collected data."""
    try:
        # Initialize market metrics
        market_metrics = {}
        
        # Calculate price metrics from Yad2 listings
        if listings:
            prices = [listing.get('price') for listing in listings if listing.get('price')]
            areas = [listing.get('area') for listing in listings if listing.get('area')]
            
            if prices:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                
                # Price gap percentage (if asset has a price)
                if asset.price:
                    price_gap_pct = ((asset.price - avg_price) / avg_price) * 100
                    market_metrics['priceGapPct'] = round(price_gap_pct, 2)
                
                # Expected price range
                market_metrics['expectedPriceRange'] = f"{min_price:,} - {max_price:,}"
                
                # Model price (average of similar properties)
                market_metrics['modelPrice'] = int(avg_price)
                
                # Confidence percentage (based on number of comparable properties)
                confidence_pct = min(100, len(prices) * 20)  # 20% per comparable property, max 100%
                market_metrics['confidencePct'] = confidence_pct
            
            if areas:
                avg_area = sum(areas) / len(areas)
                if asset.area and avg_area:
                    # Delta vs area percentage
                    delta_vs_area_pct = ((asset.area - avg_area) / avg_area) * 100
                    market_metrics['deltaVsAreaPct'] = round(delta_vs_area_pct, 2)
        
        # Calculate cap rate from rent estimate
        if asset.price and asset.area:
            # Estimate rent based on area (rough calculation: 50-80 NIS per sqm)
            estimated_rent = asset.area * 65  # Average of 65 NIS per sqm
            annual_rent = estimated_rent * 12
            cap_rate = (annual_rent / asset.price) * 100
            market_metrics['capRatePct'] = round(cap_rate, 2)
            market_metrics['rentEstimate'] = int(estimated_rent)
        
        # Calculate competition metrics
        if listings:
            # Competition within 1km (simplified - based on number of listings)
            competition_level = "נמוכה"
            if len(listings) > 10:
                competition_level = "גבוהה"
            elif len(listings) > 5:
                competition_level = "בינונית"
            market_metrics['competition1km'] = competition_level
        
        # Calculate risk flags
        risk_flags = []
        
        # Price risk
        if market_metrics.get('priceGapPct'):
            if abs(market_metrics['priceGapPct']) > 20:
                risk_flags.append("פער מחיר גבוה")
        
        # Area risk
        if market_metrics.get('deltaVsAreaPct'):
            if abs(market_metrics['deltaVsAreaPct']) > 30:
                risk_flags.append("פער שטח גבוה")
        
        # Low confidence
        if market_metrics.get('confidencePct', 0) < 40:
            risk_flags.append("ביטחון נמוך")
        
        market_metrics['riskFlags'] = risk_flags
        
        # Calculate DOM percentile (simplified)
        if listings:
            # Simulate DOM based on number of listings (more listings = higher DOM)
            dom_percentile = min(90, len(listings) * 10)
            market_metrics['domPercentile'] = dom_percentile
        
        # Store market metrics in asset meta
        if not asset.meta:
            asset.meta = {}
        
        asset.meta['market_metrics'] = market_metrics
        
        # Update asset fields with calculated metrics
        for key, value in market_metrics.items():
            if hasattr(asset, key):
                setattr(asset, key, value)
        
        asset.save()
        
        logger.info(f"Calculated market metrics for asset {asset.id}: {market_metrics}")
        
    except Exception as e:
        logger.error(f"Failed to calculate market metrics for asset {asset.id}: {e}")


def _create_documents_and_plans(asset, gis_data, gov_data, plans, mavat_plans):
    """Create Document and Plan records from collected data."""
    try:
        from core.models import Document, Plan
        from django.contrib.auth import get_user_model
        
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
    if not permits:
        return
    
    # Initialize documents array if it doesn't exist
    if 'documents' not in asset.meta:
        asset.meta['documents'] = []
    
    # Create documents for each permit
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
                from datetime import datetime
                permit_date = datetime.fromtimestamp(permit['permission_date'] / 1000).strftime('%Y-%m-%d')
            except Exception as e:
                logger.debug(f"Failed to parse permit date: {e}")
                pass
        
        # Create document entry
        document = {
            'id': f"permit_{permit_id}" if permit_id else f"permit_{len(asset.meta['documents']) + 1}",
            'type': 'permit',
            'title': f"היתר בניה - {description}" if description else "היתר בניה",
            'description': description,
            'status': status,
            'date': permit_date,
            'url': url,
            'source': 'GIS',
            'permit_number': permit_number,
            'request_number': request_number,
            'address': address,
            'downloadable': bool(url),
            'external_url': url, 
            'name': description
        }
        
        asset.meta['documents'].append(document)
    
    logger.info(f"Created {len(permits)} permit documents for asset {asset.id}")


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
    """Create documents from RAMI plans data."""
    if not plans:
        return
    
    # Initialize documents array if it doesn't exist
    if 'documents' not in asset.meta:
        asset.meta['documents'] = []
    
    # Create documents for each plan
    for plan in plans:
        if not plan:
            continue
            
        # Extract plan information
        plan_number = plan.get('planNumber', plan.get('plan_number', plan.get('number', '')))
        plan_name = plan.get('title', plan.get('plan_name', plan.get('name', '')))
        status = plan.get('status', '')
        
        # Extract URL from documentsSet structure
        url = ''
        documents_set = plan.get('raw', {}).get('documentsSet', {})
        
        # Try to get URL from various sources in documentsSet
        if documents_set.get('map', {}).get('path'):
            url = documents_set['map']['path']
        elif documents_set.get('takanon', {}).get('path'):
            url = documents_set['takanon']['path']
        elif documents_set.get('mmg', {}).get('path'):
            url = documents_set['mmg']['path']
        
        # Validate and clean URL
        if url and not url.startswith(('http://', 'https://')):
            if url.startswith('/'):
                url = f"https://rami.gov.il{url}"
            else:
                url = f"https://rami.gov.il/{url}"
        
        # Create document entry
        document = {
            'id': f"rami_plan_{plan_number}" if plan_number else f"rami_plan_{len(asset.meta['documents']) + 1}",
            'type': 'plan',
            'title': f"תכנית רמ״י - {plan_name}" if plan_name else f"תכנית רמ״י {plan_number}",
            'description': f"תכנית רמ״י {plan_number}",
            'status': status,
            'date': plan.get('statusDate', plan.get('date', '')),
            'url': url,
            'source': 'RAMI',
            'plan_number': plan_number,
            'plan_name': plan_name,
            'downloadable': bool(url and url.startswith(('http://', 'https://')))
        }
        
        asset.meta['documents'].append(document)
    
    logger.info(f"Created {len(plans)} RAMI plan documents for asset {asset.id}")




__all__ = [
    "DataPipeline",
    "Yad2Collector",
    "GISCollector",
    "GovCollector",
    "GovMapCollector",
    "RamiCollector",
    "MavatCollector",
]