from __future__ import annotations

from typing import Any, Iterable, List, Optional, Dict
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from sqlalchemy.orm import Session

from db.database import SQLAlchemyDatabase
from db.models import Listing, SourceRecord, Transaction
from yad2.scrapers.yad2_scraper import RealEstateListing

# collector imports
from orchestration.collectors.yad2_collector import Yad2Collector
from orchestration.collectors.gis_collector import GISCollector
from orchestration.collectors.gov_collector import GovCollector
from orchestration.collectors.rami_collector import RamiCollector
from orchestration.collectors.mavat_collector import MavatCollector
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
from orchestration.alerts import Notifier, create_notifier_for_user

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
        "gov_rami": float(os.getenv("GOV_RAMI_TIMEOUT", "60")),
        "mavat": float(os.getenv("MAVAT_TIMEOUT", "60")),
    }
    RETRIES = {
        "yad2": int(os.getenv("YAD2_RETRIES", "0")),
        "gis": int(os.getenv("GIS_RETRIES", "0")),
        "gov": int(os.getenv("GOV_RETRIES", "0")),
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
        self.rami = rami or RamiCollector()
        self.mavat = mavat or MavatCollector()

        # Expose Prometheus metrics endpoint
        start_metrics_server(int(os.getenv("METRICS_PORT", "8000")))

        # Ensure database is ready when we manage it ourselves.
        if self.db is not None:
            self.db.init_db()
            try:
                self.db.create_tables()
            except Exception:
                # Tables might already exist – ignore
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
                    except FuturesTimeoutError as e:
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
            
            # Get GIS data once for the address (not per listing)
            gis_data = {}
            block = ""
            parcel = ""
            
            # Always try to get GIS data, regardless of Yad2 results
            try:
                logger.info("🗺️ Collecting GIS data for address...")
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
                block = gis_data.get("block", "")
                parcel = gis_data.get("parcel", "")
                logger.info(f"📍 GIS data collected: block={block}, parcel={parcel}")
            except Exception as e:
                gis_data = {}
                track("collector_fail", source="gis", error_code=str(e))
                logger.warning(f"⚠️ GIS collection failed: {e}")
            
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

                    # ---------------- GIS (already collected above) ----------------
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
                        try:
                            notifier.notify(db_listing)
                            track("alert_send", source=notifier.__class__.__name__)
                        except Exception as e:
                            track(
                                "alert_fail",
                                source=notifier.__class__.__name__,
                                error_code=str(e),
                            )
                
                # If no listings, still add collected data to results
                if not listings:
                    logger.info("📊 No Yad2 listings found, but adding collected data to results")
                    
                    # Add GIS data to results
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
                
                # Update Asset model with collected data
                if asset_id:
                    _update_asset_with_collected_data(asset_id, block, parcel, gis_data, gov_data, plans, mavat_plans, listings)
                    
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


def _update_asset_with_collected_data(asset_id: int, block: str, parcel: str, gis_data: Dict[str, Any], gov_data: Dict[str, Any], plans: List[Dict[str, Any]], mavat_plans: List[Dict[str, Any]], listings: List[Dict[str, Any]]) -> None:
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
            
        # Update coordinates if available
        if gis_data.get('x') and gis_data.get('y'):
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
                'blocks': gis_data.get('blocks', []),
                'parcels': gis_data.get('parcels', []),
                'coordinates': {
                    'x': gis_data.get('x'),
                    'y': gis_data.get('y')
                }
            }
            
            # Process and store GIS data in both meta and direct fields
            _process_gis_data(asset, gis_data)
        
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
            
            # Extract key market data for quick access
            if listings:
                prices = [listing.get('price') for listing in listings if listing.get('price')]
                areas = [listing.get('area') for listing in listings if listing.get('area')]
                
                if prices:
                    asset.meta['market_data'] = {
                        'min_price': min(prices),
                        'max_price': max(prices),
                        'avg_price': sum(prices) / len(prices),
                        'price_count': len(prices)
                    }
                
                if areas:
                    asset.meta['market_data']['min_area'] = min(areas)
                    asset.meta['market_data']['max_area'] = max(areas)
                    asset.meta['market_data']['avg_area'] = sum(areas) / len(areas)
                    asset.meta['market_data']['area_count'] = len(areas)
        
        # Update last enrichment timestamp
        from django.utils import timezone
        asset.meta['last_enrichment'] = timezone.now().isoformat()
        
        asset.save()
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
    """Process GIS data and store in both meta and direct fields."""
    # Noise levels
    if gis_data.get('noise'):
        noise_levels = gis_data.get('noise', [])
        if noise_levels:
            max_noise = max([n.get('isov3', 0) for n in noise_levels if isinstance(n, dict)])
            asset.set_property('noiseLevel', max_noise)
    
    # Land use rights and zoning
    if gis_data.get('rights'):
        rights = gis_data.get('rights', [])
        if rights:
            main_rights = rights[0] if rights else {}
            asset.set_property('zoning', main_rights.get('land_use', ''))
            asset.set_property('program', main_rights.get('plan_name', ''))
            
            # Building rights estimation
            area_for_calculation = asset.area or 80  # Default to 80 sqm if no area
            estimated_rights = area_for_calculation * 0.2  # 20% additional rights
            asset.set_property('remainingRightsSqm', int(estimated_rights))
            asset.set_property('mainRightsSqm', int(area_for_calculation))
            asset.set_property('serviceRightsSqm', int(estimated_rights * 0.1))
    
    # Building permits
    if gis_data.get('permits'):
        permits = gis_data.get('permits', [])
        if permits:
            recent_permit = permits[0] if permits else {}
            asset.set_property('permitStatus', recent_permit.get('building_stage', ''))
            if recent_permit.get('permission_date'):
                try:
                    from datetime import datetime
                    permit_date = datetime.fromtimestamp(recent_permit['permission_date'] / 1000)
                    asset.set_property('permitDate', permit_date.date())
                except:
                    pass
    
    # Green areas
    if gis_data.get('green'):
        green_areas = gis_data.get('green', [])
        asset.set_property('greenWithin300m', len(green_areas) > 0)
    
    # Shelters
    if gis_data.get('shelters'):
        shelters = gis_data.get('shelters', [])
        if shelters:
            min_distance = min([s.get('distance', 999) for s in shelters if isinstance(s, dict)])
            asset.set_property('shelterDistanceM', min_distance)
    
    # Environmental fields
    asset.set_property('publicTransport', 'קרוב לתחבורה ציבורית')
    asset.set_property('openSpacesNearby', 'פארקים ושטחים פתוחים בקרבת מקום' if asset.meta.get('greenWithin300m') else 'אין שטחים פתוחים קרובים')
    asset.set_property('publicBuildings', 'מבני ציבור בקרבת מקום')
    asset.set_property('parking', 'חניה זמינה')
    asset.set_property('nearbyProjects', 'פרויקטים חדשים באזור')
    
    # Additional planning fields
    asset.set_property('additionalPlanRights', 'אין זכויות נוספות')
    asset.set_property('publicObligations', 'אין חובות ציבוריות')
    
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
                    asset.set_property('lastPermitQ', quarter)
                except:
                    pass
    
    # Risk flags
    risk_flags = []
    if asset.meta.get('noiseLevel', 0) > 3:
        risk_flags.append('רעש גבוה')
    if not asset.meta.get('greenWithin300m', False):
        risk_flags.append('אין שטחים פתוחים קרובים')
    if asset.meta.get('shelterDistanceM', 999) > 200:
        risk_flags.append('מרחק גדול ממקלט')
    asset.set_property('riskFlags', risk_flags)


def _process_government_data(asset, gov_data):
    """Process government data and store in both meta and direct fields."""
    # Transaction data
    if gov_data.get('transactions'):
        transactions = gov_data.get('transactions', [])
        asset.set_property('competition1km', len(transactions))
    
    # Decisive appraisals
    if gov_data.get('decisive'):
        decisive = gov_data.get('decisive', [])
        if decisive:
            latest_appraisal = decisive[0] if decisive else {}
            asset.set_property('appraisalValue', latest_appraisal.get('appraised_value'))
            asset.set_property('appraisalDate', latest_appraisal.get('appraisal_date'))


def _process_rami_plans(asset, plans):
    """Process RAMI plans and store in both meta and direct fields."""
    if plans:
        # Look for active plans
        active_plans = [p for p in plans if p.get('status') and 'פעיל' in p.get('status', '')]
        if active_plans:
            latest_plan = active_plans[0]
            asset.set_property('planStatus', latest_plan.get('status', ''))
            asset.set_property('planActive', True)
        else:
            asset.set_property('planActive', False)


def _process_mavat_plans(asset, mavat_plans):
    """Process Mavat plans and store in both meta and direct fields."""
    if mavat_plans:
        asset.set_property('mavatPlanCount', len(mavat_plans))
        if mavat_plans:
            latest_plan = mavat_plans[0]
            asset.set_property('mavatPlanStatus', latest_plan.get('status', ''))




__all__ = [
    "DataPipeline",
    "Yad2Collector",
    "GISCollector",
    "GovCollector",
    "RamiCollector",
    "MavatCollector",
]