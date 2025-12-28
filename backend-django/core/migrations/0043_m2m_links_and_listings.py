from django.db import migrations


def backfill_docs(apps, schema_editor):
    Document = apps.get_model("core", "Document")
    AssetDocument = apps.get_model("core", "AssetDocument")
    for document in Document.objects.exclude(asset=None).only("id", "asset_id"):
        AssetDocument.objects.get_or_create(
            document_id=document.id, asset_id=document.asset_id
        )


def backfill_transactions(apps, schema_editor):
    transaction_model = apps.get_model("core", "RealEstateTransaction")
    AssetTransaction = apps.get_model("core", "AssetTransaction")
    for transaction in transaction_model.objects.exclude(asset=None).only(
        "id", "asset_id"
    ):
        AssetTransaction.objects.get_or_create(
            transaction_id=transaction.id, asset_id=transaction.asset_id
        )


def backfill_permits(apps, schema_editor):
    Permit = apps.get_model("core", "Permit")
    AssetPermit = apps.get_model("core", "AssetPermit")
    for permit in Permit.objects.exclude(asset=None).only("id", "asset_id"):
        AssetPermit.objects.get_or_create(permit_id=permit.id, asset_id=permit.asset_id)


def backfill_plans(apps, schema_editor):
    Plan = apps.get_model("core", "Plan")
    AssetPlan = apps.get_model("core", "AssetPlan")
    for plan in Plan.objects.exclude(asset=None).only("id", "asset_id"):
        AssetPlan.objects.get_or_create(plan_id=plan.id, asset_id=plan.asset_id)


def dedupe_yad2_to_listing(apps, schema_editor):
    SourceRecord = apps.get_model("core", "SourceRecord")
    Listing = apps.get_model("core", "Listing")
    AssetListing = apps.get_model("core", "AssetListing")

    qs = (
        SourceRecord.objects.filter(source="yad2")
        .exclude(external_id__isnull=True)
        .only("id", "external_id", "title", "url", "raw", "asset_id")
    )
    for source_record in qs.iterator():
        listing, _ = Listing.objects.get_or_create(
            source="yad2",
            external_id=source_record.external_id,
            defaults={
                "title": source_record.title or (source_record.raw or {}).get("title"),
                "url": source_record.url or (source_record.raw or {}).get("url"),
                "raw": source_record.raw or {},
                "status": (source_record.raw or {}).get("status") or "active",
                "price": (source_record.raw or {}).get("price"),
                "rooms": (source_record.raw or {}).get("rooms"),
                "area": (source_record.raw or {}).get("area"),
                "address": (source_record.raw or {}).get("address"),
            },
        )
        if source_record.asset_id:
            AssetListing.objects.get_or_create(
                listing_id=listing.id, asset_id=source_record.asset_id
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0042_assetdocument_assetlisting_assetpermit_assetplan_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_docs, migrations.RunPython.noop),
        migrations.RunPython(backfill_transactions, migrations.RunPython.noop),
        migrations.RunPython(backfill_permits, migrations.RunPython.noop),
        migrations.RunPython(backfill_plans, migrations.RunPython.noop),
        migrations.RunPython(dedupe_yad2_to_listing, migrations.RunPython.noop),
    ]
