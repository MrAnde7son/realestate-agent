from django.db import migrations, models


def seed_asset_stats(apps, schema_editor):
    Asset = apps.get_model("core", "Asset")
    AssetStats = apps.get_model("core", "AssetStats")
    total = Asset.objects.count()
    AssetStats.objects.update_or_create(id=1, defaults={"total_assets": total})


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0072_fix_transaction_raw_field"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssetStats",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("total_assets", models.IntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RunPython(seed_asset_stats, migrations.RunPython.noop),
    ]
