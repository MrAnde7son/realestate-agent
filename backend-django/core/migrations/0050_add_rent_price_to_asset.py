from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0049_rename_core_asset_block_dc43e9_idx_core_asset_block_531195_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="rent_price",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
