"""Scheduler for periodically fetching Yad2 data and storing it."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from orchestration.alerts import Notifier
from orchestration.scheduler import create_scheduler
from yad2.scrapers.yad2_scraper import Yad2Scraper
# Import Django models if available
try:
    import sys
    import os
    # Add the backend-django directory to the path
    backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend-django')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    # Configure Django settings if not already configured
    import django
    if not django.conf.settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')
        django.setup()
    
    from core.models import Asset
    DJANGO_AVAILABLE = True
except Exception as e:
    DJANGO_AVAILABLE = False
    # Create a dummy Asset class for when Django is not available
    class Asset:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


def _store_listings(
    listings: Iterable[object],
    notifier: Optional[Notifier] = None,
) -> None:
    """Persist listings to the database and trigger alerts if needed."""
    if not DJANGO_AVAILABLE:
        # Skip if Django is not available
        return
    
    try:
        # Use Django ORM to store listings
        for item in listings:
            scraped_at = item.scraped_at
            if isinstance(scraped_at, str):
                try:
                    scraped_at = datetime.fromisoformat(scraped_at)
                except ValueError:
                    scraped_at = datetime.utcnow()

            # Check if asset already exists
            existing = Asset.objects.filter(
                scope_type='address',
                street=item.address.split()[0] if item.address else None,
                number=item.address.split()[-1] if item.address else None
            ).first()

            if not existing:
                # Create new asset
                asset = Asset.objects.create(
                    scope_type='address',
                    street=item.address.split()[0] if item.address else None,
                    number=item.address.split()[-1] if item.address else None,
                    status='ready',
                    meta={
                        'yad2_data': {
                            'listing_id': item.listing_id,
                            'title': item.title,
                            'price': item.price,
                            'address': item.address,
                            'rooms': item.rooms,
                            'floor': item.floor,
                            'size': item.size,
                            'property_type': item.property_type,
                            'description': item.description,
                            'images': item.images,
                            'contact_info': item.contact_info,
                            'features': item.features,
                            'url': item.url,
                            'date_posted': item.date_posted,
                            'scraped_at': scraped_at.isoformat() if scraped_at else None,
                        }
                    }
                )

                if notifier:
                    notifier.notify(asset)
    except Exception as e:
        print(f"Error storing listings: {e}")


def fetch_and_store(
    notifier: Optional[Notifier] = None,
) -> None:
    """Fetch listings from Yad2 and store them in the database."""
    if not DJANGO_AVAILABLE:
        print("Django not available, skipping Yad2 data storage")
        return
    
    try:
        scraper = Yad2Scraper()
        listings = scraper.scrape_page()
        _store_listings(listings, notifier=notifier)
    except Exception as e:
        print(f"Error fetching Yad2 data: {e}")


def start_yad2_scheduler(
    interval_minutes: int = 60,
    notifier: Optional[Notifier] = None,
):
    """Start a scheduler that periodically fetches Yad2 data."""
    scheduler = create_scheduler()
    scheduler.add_job(
        fetch_and_store,
        "interval",
        minutes=interval_minutes,
        kwargs={"notifier": notifier},
    )
    scheduler.start()
    return scheduler

