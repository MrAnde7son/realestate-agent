from __future__ import annotations

"""High level data collection pipeline for real-estate assets.

This module defines a small object oriented framework that orchestrates
calls to the various data providers (Yad2, Tel-Aviv GIS, gov.il datasets
and RAMI plans) and persists the aggregated results in the local
SQLAlchemy database.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple

from sqlalchemy.orm import Session

from db.database import SQLAlchemyDatabase
from db.models import Listing, SourceRecord, Transaction

# service client imports
from yad2.scrapers.yad2_scraper import Yad2Scraper, RealEstateListing
from gis.gis_client import TelAvivGS
from gov.decisive import fetch_decisive_appraisals
from gov.nadlan.scraper import NadlanDealsScraper
from rami.rami_client import RamiClient
from mavat.collector.mavat_collector import MavatCollector

# alert helpers
from orchestration.alerts import Notifier, create_notifier_for_user

# Import Django Alert model if available
try:  # pragma: no cover - best effort import
    import sys
    import os

    backend_path = os.path.join(os.path.dirname(__file__), "..", "backend-django")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    import django

    if not django.conf.settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
        django.setup()

    from core.models import Alert  # type: ignore
except ImportError as e:  # pragma: no cover - best effort
    print(f"Failed to import Django models: {e}")

    class Alert:  # type: ignore
        objects = []


def _load_user_notifiers() -> List[Notifier]:
    """Build notifiers for all users with active alerts."""

    notifiers: List[Notifier] = []
    try:
        alerts = Alert.objects.filter(active=True).select_related("user")  # type: ignore[attr-defined]
        for alert in alerts:
            notifier = create_notifier_for_user(alert.user, alert.criteria)
            if notifier:
                notifiers.append(notifier)
    except Exception as e:  # pragma: no cover - best effort
        print(f"Failed to create user notifiers: {e}")
    return notifiers


# ---------------------------------------------------------------------------
# Collector classes
# ---------------------------------------------------------------------------

class Yad2Collector:
    """Wrapper around :class:`Yad2Scraper` implementing a simple interface."""

    def __init__(self, client: Optional[Yad2Scraper] = None) -> None:
        self.client = client or Yad2Scraper()

    def fetch_listings(self, address: str, max_pages: int) -> List[RealEstateListing]:
        location = self.client.fetch_location_data(address)
        if location:
            city = location.get("cities") or []
            streets = location.get("streets") or []
            if city:
                self.client.set_search_parameters(city=city[0].get("id"))
            if streets:
                self.client.set_search_parameters(street=streets[0].get("id"))
        return self.client.scrape_all_pages(max_pages=max_pages, delay=0)


class GISCollector:
    """Collector for Tel-Aviv GIS data."""

    def __init__(self, client: Optional[TelAvivGS] = None) -> None:
        self.client = client or TelAvivGS()

    def geocode(self, address: str, house_number: int) -> Tuple[float, float]:
        return self.client.get_address_coordinates(address, house_number)

    def collect(self, x: float, y: float) -> Dict[str, Any]:
        return {
            "blocks": self.client.get_blocks(x, y),
            "parcels": self.client.get_parcels(x, y),
            "permits": self.client.get_building_permits(x, y),
            "rights": self.client.get_land_use_main(x, y),
            "shelters": self.client.get_shelters(x, y),
            "green": self.client.get_green_areas(x, y),
            "noise": self.client.get_noise_levels(x, y),
        }

    def extract_block_parcel(self, data: Dict[str, Any]) -> Tuple[str, str]:
        block = data.get("blocks", [{}])[0].get("ms_gush", "")
        parcel = data.get("parcels", [{}])[0].get("ms_chelka", "")
        return block, parcel


class GovCollector:
    """Collector for gov.il decisive appraisals and transaction history."""

    def __init__(
        self,
        deals_client: Optional[NadlanDealsScraper] = None,
        decisive_func=fetch_decisive_appraisals,
    ) -> None:
        self.deals_client = deals_client or NadlanDealsScraper()
        self.decisive_func = decisive_func

    def collect_decisive(self, block: str, parcel: str) -> List[Any]:
        if block and parcel:
            return self.decisive_func(block=block, plot=parcel) or []
        return []

    def collect_transactions(self, address: str) -> Iterable[Any]:
        try:
            return self.deals_client.get_deals_by_address(address) or []
        except Exception:
            return []


class RamiCollector:
    """Collector for RAMI plans."""

    def __init__(self, client: Optional[RamiClient] = None) -> None:
        self.client = client or RamiClient()

    def collect(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        try:
            df = self.client.fetch_plans({"gush": block, "helka": parcel})
            return df.to_dict(orient="records") if hasattr(df, "to_dict") else []
        except Exception:
            return []


# ---------------------------------------------------------------------------
# Data pipeline orchestrator
# ---------------------------------------------------------------------------

class DataPipeline:
    """Collect data from external services and persist it to the database."""

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

        # Ensure database is ready when we manage it ourselves.
        if self.db is not None:
            self.db.init_db()
            try:
                self.db.create_tables()
            except Exception:
                # Tables might already exist – ignore
                pass

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
    def run(self, address: str, house_number: int, max_pages: int = 1) -> List[Any]:
        """Run the pipeline for a given address.

        The function still persists results to the database but also returns a
        list of raw objects/dictionaries representing the collected data.  This
        makes the pipeline easier to test in isolation.
        """

        # Geocode address via GIS first
        x, y = self.gis.geocode(address, house_number)

        # Search Yad2 for listings near the location
        listings = self.yad2.fetch_listings(address, max_pages)

        # Load user notifiers once per run
        notifiers = _load_user_notifiers()

        # Decide which session to use
        session_provided = self.session is not None
        session = self.session or (self.db.get_session() if self.db else None)
        if session is None:
            raise RuntimeError("No database session available")

        results: List[Any] = []
        try:
            for listing in listings:
                # Store listing in DB and add to return list
                db_listing = self._store_listing(session, listing)
                results.append(listing)

                # ---------------- GIS ----------------
                gis_data = self.gis.collect(x, y)
                self._add_source_record(session, db_listing.id, "gis", gis_data)
                results.append({"source": "gis", "data": gis_data})

                block, parcel = self.gis.extract_block_parcel(gis_data)

                # ---------------- Gov - decisive ----------------
                decisives = self.gov.collect_decisive(block, parcel)
                if decisives:
                    self._add_source_record(session, db_listing.id, "decisive", decisives)
                    results.append({"source": "decisive", "data": decisives})

                # ---------------- Gov - transactions ----------------
                deals = list(self.gov.collect_transactions(address))
                self._add_transactions(session, db_listing.id, deals)
                if deals:
                    deal_dicts = [d.to_dict() if hasattr(d, "to_dict") else dict(d) for d in deals]
                    results.append({"source": "transactions", "data": deal_dicts})

                # ---------------- RAMI plans ----------------
                plans = self.rami.collect(block, parcel)
                if plans:
                    self._add_source_record(session, db_listing.id, "rami", plans)
                    results.append({"source": "rami", "data": plans})

                # ---------------- Alerts ----------------
                for notifier in notifiers:
                    notifier.notify(db_listing)

            session.commit()
        finally:
            if not session_provided:
                session.close()

        return results


__all__ = [
    "DataPipeline",
    "Yad2Collector",
    "GISCollector",
    "GovCollector",
    "RamiCollector",
    "MavatCollector",
]