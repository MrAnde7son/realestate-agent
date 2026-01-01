from django.db import migrations, models


def backfill_primary_photo_url(apps, schema_editor):
    Asset = apps.get_model("core", "Asset")
    Listing = apps.get_model("core", "Listing")
    AssetListing = apps.get_model("core", "AssetListing")

    assets = Asset.objects.filter(primary_photo_url__isnull=True).only("id")
    for asset in assets.iterator():
        listing_ids = AssetListing.objects.filter(asset_id=asset.id).values_list(
            "listing_id", flat=True
        )
        if not listing_ids:
            continue
        listings = Listing.objects.filter(id__in=list(listing_ids)).only("id", "photos", "raw")
        primary_photo = None
        for listing in listings:
            photos = listing.photos or []
            if isinstance(photos, list) and photos:
                primary_photo = photos[0]
                break
            raw = listing.raw or {}
            for key in ("photos", "images"):
                raw_photos = raw.get(key) or []
                if isinstance(raw_photos, list) and raw_photos:
                    primary_photo = raw_photos[0]
                    break
            if primary_photo:
                break
        if primary_photo:
            Asset.objects.filter(id=asset.id).update(primary_photo_url=primary_photo)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0073_asset_stats"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="primary_photo_url",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
        migrations.RunPython(backfill_primary_photo_url, migrations.RunPython.noop),
    ]
