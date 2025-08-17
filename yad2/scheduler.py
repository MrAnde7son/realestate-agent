"""Scheduler for periodically fetching Yad2 data and storing it."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from orchestration.alerts import Notifier
from db import Database, models
from orchestration.scheduler import create_scheduler
from yad2.scrapers.yad2_scraper import Yad2Scraper


def _store_listings(
    listings: Iterable[object],
    database: Database,
    notifier: Optional[Notifier] = None,
) -> None:
    """Persist listings to the database and trigger alerts if needed."""
    with database.get_session() as session:
        for item in listings:
            scraped_at = item.scraped_at
            if isinstance(scraped_at, str):
                try:
                    scraped_at = datetime.fromisoformat(scraped_at)
                except ValueError:
                    scraped_at = datetime.utcnow()

            existing = (
                session.query(models.Listing)
                .filter_by(source="yad2", external_id=item.listing_id)
                .first()
            )

            db_listing = models.Listing(
                source="yad2",
                external_id=item.listing_id,
                title=item.title,
                price=item.price,
                address=item.address,
                rooms=item.rooms,
                floor=item.floor,
                size=item.size,
                property_type=item.property_type,
                description=item.description,
                images=item.images,
                contact_info=item.contact_info,
                features=item.features,
                url=item.url,
                date_posted=item.date_posted,
                scraped_at=scraped_at,
            )
            session.merge(db_listing)

            if existing is None and notifier:
                notifier.notify(db_listing)

        session.commit()


def fetch_and_store(
    database: Database,
    notifier: Optional[Notifier] = None,
) -> None:
    """Fetch listings from Yad2 and store them in the database."""
    database.init_db()
    scraper = Yad2Scraper()
    listings = scraper.scrape_page()
    _store_listings(listings, database=database, notifier=notifier)


def start_yad2_scheduler(
    database: Database,
    interval_minutes: int = 60,
    notifier: Optional[Notifier] = None,
):
    """Start a scheduler that periodically fetches Yad2 data."""
    scheduler = create_scheduler()
    scheduler.add_job(
        fetch_and_store,
        "interval",
        minutes=interval_minutes,
        kwargs={"database": database, "notifier": notifier},
    )
    scheduler.start()
    return scheduler

