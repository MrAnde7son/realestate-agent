from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "core",
            "0048_merge_0045_rename_core_asset_block_dc43e9_idx_core_asset_block_531195_idx_and_more_0047_add_listing_ad_type",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="is_commercial",
            field=models.BooleanField(default=False, help_text="האם הנכס מסחרי"),
        ),
    ]
