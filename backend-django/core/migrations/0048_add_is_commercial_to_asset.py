from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0047_add_listing_ad_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="asset",
            name="is_commercial",
            field=models.BooleanField(default=False, help_text="האם הנכס מסחרי"),
        ),
    ]
