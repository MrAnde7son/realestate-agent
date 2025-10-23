from __future__ import annotations

from typing import Any, Iterable, List, Optional, Dict, Tuple
import os
import time
import re
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from sqlalchemy.orm import Session

from db.database import SQLAlchemyDatabase
from db.models import Listing as DBListing, SourceRecord, Transaction
from yad2.scrapers.yad2_scraper import RealEstateListing

# collector imports
from orchestration.collectors import Yad2Collector, GISCollector, GovCollector, GovMapCollector, RamiCollector, MavatCollector, HandasaCollector
from orchestration.location import LocationQuery, ensure_location_query
from orchestration.pipeline import auto_expand_related_assets, create_asset_snapshot, update_asset_with_collected_data
from orchestration.pipeline.listings import _build_listing_snapshot, _normalize_listings

from orchestration.pipeline.documents import AlertRule
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
        logging.getLogger(__name__).warning(f"Failed to create user notifiers: {e}")
    return notifiers



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
        "gis": float(os.getenv("GIS_TIMEOUT", "60")),
        "gov": float(os.getenv("GOV_TIMEOUT", "60")),
        "govmap": float(os.getenv("GOVMAP_TIMEOUT", "60")),
        "gov_rami": float(os.getenv("GOV_RAMI_TIMEOUT", "60")),
        "mavat": float(os.getenv("MAVAT_TIMEOUT", "60")),
        "handasa": float(os.getenv("HANDASA_TIMEOUT", "90")),
    }
    RETRIES = {
        "yad2": int(os.getenv("YAD2_RETRIES", "0")),
        "gis": int(os.getenv("GIS_RETRIES", "0")),
        "gov": int(os.getenv("GOV_RETRIES", "0")),
        "govmap": int(os.getenv("GOVMAP_RETRIES", "0")),
        "gov_rami": int(os.getenv("GOV_RAMI_RETRIES", "0")),
        "mavat": int(os.getenv("MAVAT_RETRIES", "0")),
        "handasa": int(os.getenv("HANDASA_RETRIES", "0")),
    }

    def __init__(
        self,
        db: Optional[SQLAlchemyDatabase] = None,
        db_session: Optional["Session"] = None,
        yad2: Optional[Yad2Collector] = None,
        gis: Optional[GISCollector] = None,
        gov: Optional[GovCollector] = None,
        govmap: Optional[GovMapCollector] = None,
        rami: Optional[RamiCollector] = None,
        mavat: Optional[MavatCollector] = None,
        handasa: Optional[HandasaCollector] = None,
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
        self.handasa = handasa or HandasaCollector()
        
        # Note: GovMap client is now accessed through the collector

        # Expose Prometheus metrics endpoint
        start_metrics_server(int(os.getenv("METRICS_PORT", "9000")))

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
                    f"📊 {source} collector completed",
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
    def _store_listing(self, session, listing: RealEstateListing) -> DBListing:
        obj = DBListing(
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
        location: Optional[LocationQuery] = None,
        asset_id: Optional[int] = None,
    ) -> List[Any]:
        """Run the pipeline for a given location.

        Parameters
        ----------
        location: Optional[LocationQuery]
            Structured location query. When ``None`` an empty query is assumed.
        asset_id: Optional[int]
            Existing asset identifier being enriched (if any).

        The function still persists results to the database but also returns a
        list of raw objects/dictionaries representing the collected data.  This
        makes the pipeline easier to test in isolation.
        """

        location = ensure_location_query(location)
        initial_block = location.block
        initial_parcel = location.parcel
        initial_subparcel = location.subparcel
        street_with_number = location.street_with_number
        full_address = location.formatted

        logger.info(f"🚀 Starting data pipeline for {location.formatted}")
        start_time = time.perf_counter()

        # Prepare attributes for OpenTelemetry (only include non-None values)
        span_attributes = {
            "location": location,
        }
        # Only add house_number if it's not None
        if location.house_number is not None:
            span_attributes["house_number"] = location.house_number
            
        with tracer.start_as_current_span(
            "data_pipeline.run",
            attributes=span_attributes,
        ):
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
            block = initial_block
            parcel = initial_parcel
            subparcel = initial_subparcel
            
            # Use GovMap collector to get coordinates and parcel data
            try:
                logger.info("🗺️ Getting address coordinates and parcel data from GovMap...")
                govmap_data = self._collect_with_observability(
                    "govmap",
                    self.govmap.collect,
                    location=location,
                    timeout=self.TIMEOUTS.get("govmap"),
                    retries=self.RETRIES.get("govmap", 0),
                    asset_id=asset_id,
                    block=block,
                    parcel=parcel,
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
                location = LocationQuery(
                    city=location.city,
                    street=location.street,
                    house_number=location.house_number,
                    block=block,
                    parcel=parcel,
                    subparcel=subparcel,
                )

            logger.info(f"🏛️ GovMap data collected: block={block}, parcel={parcel}")

                # Note: Additional GovMap data (parcel API, layers catalog, search types) 
                # is now collected by the enhanced GovMap collector above
            
            # Update location with corrected address from GovMap if available
            if govmap_data.get("address") and govmap_data.get("address") != location.formatted:
                # GovMap provided a corrected address, update the location object
                corrected_address = govmap_data["address"]
                logger.info(f"🔄 Using corrected address from GovMap: {corrected_address}")
                
                # Parse the corrected address to update the location object
                try:
                    # Try to extract street, house number, and city from the corrected address
                    # Pattern to match Hebrew addresses like "רחוב שם 123, עיר"
                    address_pattern = r'^(.+?)\s+(\d+)(?:\s*,\s*(.+))?$'
                    match = re.match(address_pattern, corrected_address.strip())
                    
                    if match:
                        street_part = match.group(1).strip()
                        house_number = int(match.group(2))
                        city_part = match.group(3).strip() if match.group(3) else location.city
                        
                        # Update the location object with corrected address components
                        location = LocationQuery(
                            street=street_part,
                            house_number=house_number,
                            city=city_part,
                            block=block,
                            parcel=parcel,
                            subparcel=subparcel,
                        )
                        logger.info(f"📍 Updated location: street='{street_part}', number={house_number}, city='{city_part}'")
                    else:
                        # If parsing fails, try to extract just the street name
                        # Split by space and take the first part as street, rest as city
                        parts = corrected_address.split(',')
                        if len(parts) >= 2:
                            street_part = parts[0].strip()
                            city_part = parts[1].strip()
                            location = LocationQuery(
                                street=street_part,
                                house_number=location.house_number,
                                city=city_part,
                                block=block,
                                parcel=parcel,
                                subparcel=subparcel,
                            )
                            logger.info(f"📍 Updated location (simple parse): street='{street_part}', city='{city_part}'")
                        else:
                            logger.info("📍 Could not parse corrected address, keeping original location")
                except Exception as e:
                    logger.warning(f"Failed to parse corrected address '{corrected_address}': {e}")
                    logger.info("📍 Keeping original location due to parsing error")
            
            # Get GIS data (supplementary or fallback for coordinates)
            gis_data = {}
            try:
                logger.info("🗺️ Collecting GIS data...")
                gis_data = self._collect_with_observability(
                    "gis",
                    self.gis.collect,
                    location=location,
                    timeout=self.TIMEOUTS.get("gis"),
                    retries=self.RETRIES.get("gis", 0),
                    asset_id=asset_id,
                )
                track("collector_success", source="gis")
                
                # Extract block and parcel from successful GIS collection
                if gis_data.get('block') and gis_data.get('parcel'):
                    block = gis_data.get('block', '')
                    parcel = gis_data.get('parcel', '')
                    location = LocationQuery(
                        city=location.city,
                        street=location.street,
                        house_number=location.house_number,
                        block=block,
                        parcel=parcel,
                        subparcel=subparcel,
                    )
                    logger.info(f"✅ GIS data collected successfully: block={block}, parcel={parcel}")
            except Exception as e:
                gis_data = {}
                track("collector_fail", source="gis", error_code=str(e))
                logger.warning(f"⚠️ GIS collection failed: {e}")

            # Collect Handasa archive
            handasa_archive: List[Dict[str, Any]] = []
            if block:
                try:
                    logger.info("🏗️ Collecting Handasa permits...")
                    handasa_archive = self._collect_with_observability(
                        "handasa",
                        self.handasa.collect,
                        location=location,
                        timeout=self.TIMEOUTS.get("handasa"),
                        retries=self.RETRIES.get("handasa", 0),
                        asset_id=asset_id,
                    )
                    track("collector_success", source="handasa")
                    logger.info("🏗️ Handasa documents collected: %d", len(handasa_archive))
                except Exception as e:
                    handasa_archive = []
                    track("collector_fail", source="handasa", error_code=str(e))
                    logger.warning(f"⚠️ Handasa collection failed: {e}")

            # Get government data once for the address
            gov_data = {"decisive": [], "transactions": []}
            if block and parcel:
                try:
                    logger.info("🏛️ Collecting government data...")
                    gov_data = self._collect_with_observability(
                        "gov",
                        self.gov.collect,
                        location=location,
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
                        location=location,
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
                        location=location,
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
            
            # Search Yad2 for listings
            try:
                logger.info("🏠 Searching Yad2 for listings...")
                
                # Update location with address information from GovMap if location is not properly provided
                if govmap_data.get('addresses') and govmap_data['addresses'] and not (location.street and location.city):
                    first_address = govmap_data['addresses'][0]
                    if first_address.get('street') and first_address.get('city'):
                        # Create new location with the detailed address
                        location = LocationQuery(
                            street=first_address.get('street', ''),
                            city=first_address.get('city', ''),
                            house_number=first_address.get('house_number'),
                            block=block,
                            parcel=parcel,
                            subparcel=subparcel,
                        )
                        logger.info(f"Updated location for Yad2 search: {location.street} {location.house_number}, {location.city}")
                
                listings = self._collect_with_observability(
                    "yad2",
                    self.yad2.collect,
                    location,
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

                    if handasa_archive:
                        self._add_source_record(session, db_listing.id, "handasa", handasa_archive)
                        results.append({"source": "handasa", "data": handasa_archive})

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

                    if handasa_archive:
                        results.append({"source": "handasa", "data": handasa_archive})
                    
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
                    update_asset_with_collected_data(
                        asset_id,
                        block,
                        parcel,
                        govmap_data.get("api_data", {}).get("autocomplete", {}),
                        govmap_data,
                        gis_data,
                        gov_data,
                        plans,
                        mavat_plans,
                        handasa_archive,
                        listing_payloads,
                        x_itm,
                        y_itm,
                        lon_wgs84,
                        lat_wgs84,
                    )

                    # Create snapshot for alert evaluation
                    create_asset_snapshot(asset_id, results)

                    # Auto-expand to additional assets discovered in collected data
                    try:
                        auto_created_assets = auto_expand_related_assets(
                            asset_id,
                            listings=listing_payloads,
                            govmap_data=govmap_data,
                            gis_data=gis_data,
                            gov_data=gov_data,
                            plans=plans,
                            mavat_plans=mavat_plans,
                            handasa_archive=handasa_archive,
                        )
                        if auto_created_assets:
                            logger.info(
                                "Auto-created %d related assets from asset %s run",
                                len(auto_created_assets),
                                asset_id,
                            )
                    except Exception as exc:
                        logger.warning(
                            "Auto asset expansion failed for asset %s: %s",
                            asset_id,
                            exc,
                        )

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
