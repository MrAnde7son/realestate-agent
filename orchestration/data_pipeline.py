from __future__ import annotations

"""High level data collection pipeline for real-estate assets.

This module defines a small object oriented framework that orchestrates
calls to the various data providers (Yad2, Tel-Aviv GIS, gov.il datasets
and RAMI plans) and persists the aggregated results in the local
SQLAlchemy database.
"""

from typing import Any, Dict, Iterable, List, Optional, Tuple

from db.database import SQLAlchemyDatabase
from db.models import Listing, SourceRecord, Transaction

# service client imports
from yad2.scrapers.yad2_scraper import Yad2Scraper, RealEstateListing
from gis.gis_client import TelAvivGS
from gov.decisive import fetch_decisive_appraisals
from gov.nadlan.scraper import NadlanDealsScraper
from rami.rami_client import RamiClient
from mavat.collector.mavat_collector import MavatCollector

# Import base collector from separate module
from .base_collector import BaseCollector


# ---------------------------------------------------------------------------
# Collector classes
# ---------------------------------------------------------------------------

class Yad2Collector(BaseCollector):
    """Wrapper around :class:`Yad2Scraper` implementing a simple interface."""

    def __init__(self, client: Optional[Yad2Scraper] = None) -> None:
        self.client = client or Yad2Scraper()

    def collect(self, address: str, max_pages: int = 1) -> List[RealEstateListing]:
        """Collect Yad2 listings for a given address.
        
        This method implements the base collect interface and provides
        backward compatibility with the existing fetch_listings method.
        """
        return self.fetch_listings(address, max_pages)

    def fetch_listings(self, address: str, max_pages: int) -> List[RealEstateListing]:
        """Fetch Yad2 listings for a given address."""
        location = self.client.fetch_location_data(address)
        if location:
            city = location.get("cities") or []
            streets = location.get("streets") or []
            if city:
                self.client.set_search_parameters(city=city[0].get("id"))
            if streets:
                self.client.set_search_parameters(street=streets[0].get("id"))
        return self.client.scrape_all_pages(max_pages=max_pages, delay=0)


class GISCollector(BaseCollector):
    """Collector for Tel-Aviv GIS data."""

    def __init__(self, client: Optional[TelAvivGS] = None) -> None:
        self.client = client or TelAvivGS()

    def collect(self, x: float, y: float) -> Dict[str, Any]:
        """Collect GIS data for a given coordinate pair."""
        return {
            "blocks": self.client.get_blocks(x, y),
            "parcels": self.client.get_parcels(x, y),
            "permits": self.client.get_building_permits(x, y),
            "rights": self.client.get_land_use_main(x, y),
            "shelters": self.client.get_shelters(x, y),
            "green": self.client.get_green_areas(x, y),
            "noise": self.client.get_noise_levels(x, y),
        }

    def geocode(self, address: str, house_number: int) -> Tuple[float, float]:
        """Geocode an address to coordinates."""
        return self.client.get_address_coordinates(address, house_number)

    def extract_block_parcel(self, data: Dict[str, Any]) -> Tuple[str, str]:
        """Extract block and parcel numbers from GIS data."""
        block = data.get("blocks", [{}])[0].get("ms_gush", "")
        parcel = data.get("parcels", [{}])[0].get("ms_chelka", "")
        return block, parcel


class GovCollector(BaseCollector):
    """Collector for gov.il decisive appraisals and transaction history."""

    def __init__(
        self,
        deals_client: Optional[NadlanDealsScraper] = None,
        decisive_func=fetch_decisive_appraisals,
    ) -> None:
        self.deals_client = deals_client or NadlanDealsScraper()
        self.decisive_func = decisive_func

    def collect(self, block: str, parcel: str, address: str) -> Dict[str, Any]:
        """Collect government data for a given block/parcel and address."""
        return {
            "decisive": self.collect_decisive(block, parcel),
            "transactions": list(self.collect_transactions(address))
        }

    def collect_decisive(self, block: str, parcel: str) -> List[Any]:
        """Collect decisive appraisals for a block/parcel."""
        if block and parcel:
            return self.decisive_func(block=block, plot=parcel) or []
        return []

    def collect_transactions(self, address: str) -> Iterable[Any]:
        """Collect transaction history for an address."""
        try:
            return self.deals_client.get_deals_by_address(address) or []
        except Exception:
            return []


class RamiCollector(BaseCollector):
    """Collector for RAMI plans."""

    def __init__(self, client: Optional[RamiClient] = None) -> None:
        self.client = client or RamiClient()

    def collect(self, block: str, parcel: str) -> List[Dict[str, Any]]:
        """Collect RAMI plans for a given block/parcel."""
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
        yad2: Optional[Yad2Collector] = None,
        gis: Optional[GISCollector] = None,
        gov: Optional[GovCollector] = None,
        rami: Optional[RamiCollector] = None,
        mavat: Optional[MavatCollector] = None,
    ) -> None:
        self.db = db or SQLAlchemyDatabase()
        self.yad2 = yad2 or Yad2Collector()
        self.gis = gis or GISCollector()
        self.gov = gov or GovCollector()
        self.rami = rami or RamiCollector()
        self.mavat = mavat or MavatCollector()

        # Ensure database is ready
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
    def run(self, address: str, house_number: int, max_pages: int = 1) -> List[int]:
        """Run the pipeline for a given address.

        Returns a list of database ``Listing`` IDs that were created.
        """

        # Geocode address via GIS first
        x, y = self.gis.geocode(address, house_number)

        # Search Yad2 for listings near the location
        listings = self.yad2.collect(address, max_pages)

        created_ids: List[int] = []
        with self.db.get_session() as session:
            for listing in listings:
                db_listing = self._store_listing(session, listing)
                created_ids.append(db_listing.id)

                # ---------------- GIS ----------------
                gis_data = self.gis.collect(x, y)
                self._add_source_record(session, db_listing.id, "gis", gis_data)

                block, parcel = self.gis.extract_block_parcel(gis_data)

                # ---------------- Gov - decisive and transactions ----------------
                gov_data = self.gov.collect(block, parcel, address)
                if gov_data["decisive"]:
                    self._add_source_record(session, db_listing.id, "decisive", gov_data["decisive"])
                if gov_data["transactions"]:
                    self._add_transactions(session, db_listing.id, gov_data["transactions"])

                # ---------------- RAMI plans ----------------
                rami_plans = self.rami.collect(block, parcel)
                if rami_plans:
                    self._add_source_record(session, db_listing.id, "rami", rami_plans)

                # ---------------- Mavat plans ----------------
                mavat_plans = self.mavat.collect(block, parcel)
                if mavat_plans:
                    self._add_source_record(session, db_listing.id, "mavat", mavat_plans)

            session.commit()

        return created_ids


__all__ = [
    "DataPipeline",
    "BaseCollector",
    "Yad2Collector",
    "GISCollector",
    "GovCollector",
    "RamiCollector",
    "MavatCollector",
]
