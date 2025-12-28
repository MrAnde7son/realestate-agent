"""Scheduler for periodically fetching Yad2 data and storing it."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional

from orchestration.alerts import Notifier
from orchestration.scheduler import create_scheduler
from yad2.api_client import Yad2APIClient

# Import Django models if available
try:
    import os
    import sys

    # Add the backend-django directory to the path
    backend_path = os.path.join(os.path.dirname(__file__), "..", "backend-django")
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    # Configure Django settings if not already configured
    import django

    if not django.conf.settings.configured:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "broker_backend.settings")
        django.setup()

    from core.models import Asset
except Exception as e:
    print(f"Failed to import Django models: {e}")

    # Create a dummy Asset class for when Django is not available
    class Asset:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)


def _store_assets(
    assets: Iterable[object],
    notifier: Optional[Notifier] = None,
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

            # Parse address to extract street, number, and city
            street = None
            number = None
            city = None

            if item.address:
                address_parts = item.address.split()
                if len(address_parts) >= 2:
                    # Try to extract street and number from address
                    # Format is typically: "Street Name Number City"
                    # Last part might be city, second-to-last might be number
                    try:
                        # Try to parse number from last numeric part
                        for i in range(len(address_parts) - 1, -1, -1):
                            if address_parts[i].isdigit():
                                number = int(address_parts[i])
                                street = " ".join(address_parts[:i])
                                if i < len(address_parts) - 1:
                                    city = " ".join(address_parts[i + 1 :])
                                break
                        # If no number found, use first part as street
                        if number is None:
                            street = address_parts[0]
                            if len(address_parts) > 1:
                                city = " ".join(address_parts[1:])
                    except (ValueError, IndexError):
                        # Fallback: use first part as street
                        street = address_parts[0] if address_parts else None
                        if len(address_parts) > 1:
                            city = " ".join(address_parts[1:])

            # Check if asset already exists using deduplication service
            try:
                from core.services.asset_deduplication import find_existing_asset
                from orchestration.location import LocationQuery

                location = LocationQuery(
                    city=city or "",
                    street=street or "",
                    house_number=number,
                )
                existing = find_existing_asset(
                    location=location,
                    scope_type="address",
                )
            except Exception as e:
                # Fallback to simple check if deduplication service unavailable
                print(f"Warning: Could not use deduplication service: {e}")
                existing = (
                    Asset.objects.filter(
                        scope_type="address", street=street, number=number, city=city
                    ).first()
                    if (street or number or city)
                    else None
                )

            if not existing:
                # Create new asset
                asset = Asset.objects.create(
                    scope_type="address",
                    city=city,
                    street=street,
                    number=number,
                    status="done",
                    # Set building_type directly from property_type
                    building_type=item.property_type,
                    meta={
                        "yad2_data": {
                            "listing_id": item.listing_id,
                            "title": item.title,
                            "price": item.price,
                            "address": item.address,
                            "rooms": item.rooms,
                            "floor": item.floor,
                            "size": item.size,
                            "property_type": item.property_type,
                            "description": item.description,
                            "images": item.images,
                            "contact_info": item.contact_info,
                            "features": item.features,
                            "url": item.url,
                            "date_posted": item.date_posted,
                            "scraped_at": scraped_at.isoformat()
                            if scraped_at
                            else None,
                        }
                    },
                )

                if notifier:
                    notifier.notify(asset)
            else:
                # Update existing asset with new listing data
                if not existing.meta:
                    existing.meta = {}
                if "yad2_data" not in existing.meta:
                    existing.meta["yad2_data"] = {}

                # Update or append listing data
                existing.meta["yad2_data"].update(
                    {
                        "listing_id": item.listing_id,
                        "title": item.title,
                        "price": item.price,
                        "address": item.address,
                        "rooms": item.rooms,
                        "floor": item.floor,
                        "size": item.size,
                        "property_type": item.property_type,
                        "description": item.description,
                        "images": item.images,
                        "contact_info": item.contact_info,
                        "features": item.features,
                        "url": item.url,
                        "date_posted": item.date_posted,
                        "scraped_at": scraped_at.isoformat() if scraped_at else None,
                    }
                )
                existing.save()
    except Exception as e:
        print(f"Error storing assets: {e}")


def fetch_and_store(
    notifier: Optional[Notifier] = None,
) -> None:
    """Fetch assets from Yad2 and store them in the database."""

    try:
        client = Yad2APIClient()
        assets = client.fetch_listings()
        _store_assets(assets, notifier=notifier)
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
