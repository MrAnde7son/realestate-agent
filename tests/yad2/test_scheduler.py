#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for Yad2 scheduler and database integration."""

from datetime import datetime

from yad2.core.models import RealEstateListing
from db import SQLAlchemyDatabase, models
from yad2 import scheduler as yad2_scheduler
from orchestration.alerts import Alert, Notifier

def test_fetch_and_store(monkeypatch):
    """fetch_and_store should persist listings to the database."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")


    db = SQLAlchemyDatabase()
    db.init_db()

    with db.get_session() as session:
        session.query(models.Listing).delete()
        session.commit()

    class DummyScraper:
        def scrape_page(self, page: int = 1):
            listing = RealEstateListing()
            listing.title = "Test Listing"
            listing.price = 123.0
            listing.listing_id = "abc123"
            listing.scraped_at = datetime.utcnow().isoformat()
            return [listing]

    monkeypatch.setattr(yad2_scheduler, "Yad2Scraper", lambda: DummyScraper())

    yad2_scheduler.fetch_and_store(database=db)

    with db.get_session() as session:
        count = session.query(models.Listing).filter_by(source="yad2").count()

    assert count == 1


def test_fetch_and_store_triggers_alert(monkeypatch):
    """fetch_and_store should trigger alerts for new matching listings."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    db = SQLAlchemyDatabase()
    db.init_db()

    with db.get_session() as session:
        session.query(models.Listing).delete()
        session.commit()

    class DummyScraper:
        def scrape_page(self, page: int = 1):
            listing = RealEstateListing()
            listing.title = "Alert"
            listing.price = 500.0
            listing.listing_id = "alert123"
            listing.property_type = "apartment"
            listing.url = "http://example.com/alert"
            listing.scraped_at = datetime.utcnow().isoformat()
            return [listing]

    monkeypatch.setattr(yad2_scheduler, "Yad2Scraper", lambda: DummyScraper())

    class DummyAlert(Alert):
        def __init__(self):
            self.message = None

        def send(self, message: str) -> None:  # pragma: no cover - simple capture
            self.message = message

    alert = DummyAlert()
    notifier = Notifier(criteria={"property_type": "apartment"}, alerts=[alert])

    yad2_scheduler.fetch_and_store(database=db, notifier=notifier)

    assert alert.message is not None


def test_start_yad2_scheduler(monkeypatch):
    """Scheduler should create a job for periodic fetching."""
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    db = SQLAlchemyDatabase()
    db.init_db()

    sched = yad2_scheduler.start_yad2_scheduler(database=db, interval_minutes=1)
    try:
        jobs = sched.get_jobs()
        assert len(jobs) == 1
    finally:
        sched.shutdown()

