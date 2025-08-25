from __future__ import annotations

"""High level data collection pipeline for real‑estate assets.

This module orchestrates calls to the various scraping/ETL services
(Yad2, Tel-Aviv GIS, gov.il datasets and RAMI plans) and stores the
results in the local database so that the UI can later display them.

The pipeline is intentionally lightweight – each external dependency is
injected which makes the class easy to test by passing stub
implementations.
"""

from typing import Any, Dict, Iterable, List, Optional

from db.database import SQLAlchemyDatabase
from db.models import Listing, SourceRecord, Transaction

# Service clients
from yad2.scrapers.yad2_scraper import Yad2Scraper, RealEstateListing
from gis.gis_client import TelAvivGS
from gov.decisive import fetch_decisive_appraisals
from gov.nadlan.scraper import NadlanDealsScraper
from rami.rami_client import RamiClient


class DataPipeline:
    """Collect data from external services and persist it to the database."""

    def __init__(
        self,
        db: Optional[SQLAlchemyDatabase] = None,
        *,
        yad2_client: Optional[Yad2Scraper] = None,
        gis_client: Optional[TelAvivGS] = None,
        deals_client: Optional[NadlanDealsScraper] = None,
        decisive_func=fetch_decisive_appraisals,
        rami_client: Optional[RamiClient] = None,
    ) -> None:
        self.db = db or SQLAlchemyDatabase()
        self.yad2 = yad2_client or Yad2Scraper()
        self.gis = gis_client or TelAvivGS()
        self.deals_client = deals_client or NadlanDealsScraper()
        self.decisive_func = decisive_func
        self.rami = rami_client or RamiClient()

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
                # coordinates may be (x, y) or (lon, lat)
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
        x, y = self.gis.get_address_coordinates(address, house_number)

        # Search Yad2 for listings near the location
        location = self.yad2.fetch_location_data(address)
        if location:
            city = location.get("cities") or []
            streets = location.get("streets") or []
            if city:
                self.yad2.set_search_parameters(city=city[0].get("id"))
            if streets:
                self.yad2.set_search_parameters(street=streets[0].get("id"))
        listings = self.yad2.scrape_all_pages(max_pages=max_pages, delay=0)

        created_ids: List[int] = []
        with self.db.get_session() as session:
            for listing in listings:
                db_listing = self._store_listing(session, listing)
                created_ids.append(db_listing.id)

                # ---------------- GIS ----------------
                gis_data = {
                    "blocks": self.gis.get_blocks(x, y),
                    "parcels": self.gis.get_parcels(x, y),
                    "permits": self.gis.get_building_permits(x, y),
                    "rights": self.gis.get_land_use_main(x, y),
                    "shelters": self.gis.get_shelters(x, y),
                    "green": self.gis.get_green_areas(x, y),
                    "noise": self.gis.get_noise_levels(x, y),
                }
                self._add_source_record(session, db_listing.id, "gis", gis_data)

                # Extract block/parcel for other services
                block = gis_data["blocks"][0].get("ms_gush") if gis_data.get("blocks") else ""
                parcel = gis_data["parcels"][0].get("ms_chelka") if gis_data.get("parcels") else ""

                # ---------------- Gov - decisive ----------------
                if block and parcel:
                    decisives = self.decisive_func(block=block, plot=parcel)
                    if decisives:
                        self._add_source_record(session, db_listing.id, "decisive", decisives)

                # ---------------- Gov - transactions ----------------
                try:
                    deals = self.deals_client.get_deals_by_address(address)
                    self._add_transactions(session, db_listing.id, deals)
                except Exception:
                    pass

                # ---------------- RAMI plans ----------------
                try:
                    plans_df = self.rami.fetch_plans({"gush": block, "helka": parcel})
                    plans = plans_df.to_dict(orient="records") if hasattr(plans_df, "to_dict") else []
                    if plans:
                        self._add_source_record(session, db_listing.id, "rami", plans)
                except Exception:
                    pass

            session.commit()

        return created_ids


__all__ = ["DataPipeline"]
