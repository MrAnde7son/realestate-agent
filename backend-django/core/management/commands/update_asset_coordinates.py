"""
Django management command to update coordinates for all assets.

This command:
1. Finds all assets with invalid or missing coordinates
2. Geocodes addresses using GovMap/GIS
3. Updates asset coordinates with valid values
"""

from django.core.management.base import BaseCommand
from django.db import models
from core.models import Asset
from orchestration.collectors.govmap_collector import GovMapCollector
from orchestration.collectors.gis_collector import GISCollector
from orchestration.location import LocationQuery
from govmap.api_client import itm_to_wgs84
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Update coordinates for all assets using GovMap/GIS geocoding"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without making changes",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Update all assets, even if coordinates appear valid",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Limit number of assets to process",
        )

    def is_valid_israel_coords(self, lat, lon):
        """Check if coordinates are within Israel bounds."""
        if lat is None or lon is None:
            return False
        # Israel bounds: lat 29-34.8, lon 33-36.5
        return 29 <= lat <= 34.8 and 33 <= lon <= 36.5

    def geocode_asset(self, asset, govmap_collector, gis_collector):
        """Geocode an asset and return WGS84 coordinates."""
        # Build location query
        location = LocationQuery(
            street=asset.street or "",
            house_number=asset.number,
            city=asset.city or "",
            block=asset.block,
            parcel=asset.parcel,
        )

        # Try GovMap first
        try:
            govmap_data = govmap_collector.collect(location=location)
            if "x" in govmap_data and "y" in govmap_data:
                x_itm = govmap_data["x"]
                y_itm = govmap_data["y"]

                # Validate these are ITM coordinates (x: 100k-400k, y: 500k-1000k)
                # GovMap shape coordinates can sometimes be in wrong CRS
                if 100_000 <= x_itm <= 400_000 and 500_000 <= y_itm <= 1_000_000:
                    lon_wgs84, lat_wgs84 = itm_to_wgs84(x_itm, y_itm)
                    if self.is_valid_israel_coords(lat_wgs84, lon_wgs84):
                        return lat_wgs84, lon_wgs84, "GovMap"
                    else:
                        logger.warning(
                            f"GovMap coordinates {x_itm}, {y_itm} converted to invalid WGS84: {lat_wgs84}, {lon_wgs84}"
                        )
                else:
                    logger.warning(
                        f"GovMap coordinates {x_itm}, {y_itm} don't look like ITM (expected x: 100k-400k, y: 500k-1000k)"
                    )
        except Exception as e:
            logger.debug(f"GovMap geocoding failed for asset {asset.id}: {e}")

        # Fallback to GIS (Tel Aviv only)
        if asset.city and ("תל אביב" in asset.city or "tel aviv" in asset.city.lower()):
            try:
                if asset.street and asset.number:
                    x_itm, y_itm = gis_collector._geocode(
                        asset.street, asset.number, asset.city or ""
                    )
                    lon_wgs84, lat_wgs84 = itm_to_wgs84(x_itm, y_itm)
                    return lat_wgs84, lon_wgs84, "GIS"
            except Exception as e:
                logger.debug(f"GIS geocoding failed for asset {asset.id}: {e}")

        return None, None, None

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]
        limit = options["limit"]

        govmap_collector = GovMapCollector()
        gis_collector = GISCollector()

        # Get assets to update
        if force:
            assets = Asset.objects.all().order_by("id")
        else:
            # Only update assets with invalid or missing coordinates
            assets = Asset.objects.filter(
                models.Q(lat__isnull=True)
                | models.Q(lon__isnull=True)
                | models.Q(lat__lt=29)
                | models.Q(lat__gt=34.8)
                | models.Q(lon__lt=33)
                | models.Q(lon__gt=36.5)
            ).order_by("id")

        if limit:
            assets = assets[:limit]

        total = assets.count()
        self.stdout.write(self.style.SUCCESS(f"Found {total} assets to process"))

        updated = 0
        skipped = 0
        failed = 0

        for i, asset in enumerate(assets, 1):
            try:
                # Check if update is needed
                if not force and self.is_valid_israel_coords(asset.lat, asset.lon):
                    skipped += 1
                    if i % 100 == 0:
                        self.stdout.write(
                            f"Progress: {i}/{total} (updated: {updated}, skipped: {skipped}, failed: {failed})"
                        )
                    continue

                # Check if we have enough info to geocode
                if not asset.street or not asset.number:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Asset {asset.id}: Missing street or number, skipping"
                        )
                    )
                    skipped += 1
                    continue

                # Geocode
                self.stdout.write(
                    f"Processing asset {asset.id} ({i}/{total}): {asset.street} {asset.number}, {asset.city}"
                )
                lat, lon, source = self.geocode_asset(
                    asset, govmap_collector, gis_collector
                )

                if lat is None or lon is None:
                    self.stdout.write(
                        self.style.ERROR(f"Asset {asset.id}: Failed to geocode")
                    )
                    failed += 1
                    continue

                # Validate coordinates
                if not self.is_valid_israel_coords(lat, lon):
                    self.stdout.write(
                        self.style.ERROR(
                            f"Asset {asset.id}: Geocoded coordinates out of bounds: {lat}, {lon}"
                        )
                    )
                    failed += 1
                    continue

                # Update asset
                old_lat = asset.lat
                old_lon = asset.lon
                if not dry_run:
                    asset.lat = lat
                    asset.lon = lon
                    asset.save(update_fields=["lat", "lon"])

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Asset {asset.id}: Updated coordinates from ({old_lat}, {old_lon}) to ({lat:.8f}, {lon:.8f}) via {source}"
                    )
                )
                updated += 1

                if i % 100 == 0:
                    self.stdout.write(
                        f"Progress: {i}/{total} (updated: {updated}, skipped: {skipped}, failed: {failed})"
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Asset {asset.id}: Error - {e}"))
                failed += 1
                logger.exception(f"Error processing asset {asset.id}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted: {updated} updated, {skipped} skipped, {failed} failed"
            )
        )
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No changes were made"))
