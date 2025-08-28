"""Scheduler for periodically fetching Yad2 data and storing it."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, List, Optional

from orchestration.alerts import Notifier, create_notifier_for_user
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
    
    from core.models import Asset, Alert
except Exception as e:
    print(f"Failed to import Django models: {e}")
    # Create a dummy Asset class for when Django is not available
    class Asset:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

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


def _store_assets(
    assets: Iterable[object],
    notifiers: Optional[Iterable[Notifier]] = None,
) -> None:
    """Persist assets to the database and trigger alerts if needed."""
    
    try:
        # Use Django ORM to store assets
        for item in assets:
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

                if notifiers:
                    for notifier in notifiers:
                        notifier.notify(asset)
    except Exception as e:
        print(f"Error storing assets: {e}")


def fetch_and_store() -> None:
    """Fetch assets from Yad2 and store them in the database."""

    try:
        scraper = Yad2Scraper()
        assets = scraper.scrape_page()
        notifiers = _load_user_notifiers()
        _store_assets(assets, notifiers=notifiers)
    except Exception as e:  # pragma: no cover - best effort
        print(f"Error fetching Yad2 data: {e}")


def start_yad2_scheduler(interval_minutes: int = 60):
    """Start a scheduler that periodically fetches Yad2 data."""
    scheduler = create_scheduler()
    scheduler.add_job(
        fetch_and_store,
        "interval",
        minutes=interval_minutes,
    )
    scheduler.start()
    return scheduler

