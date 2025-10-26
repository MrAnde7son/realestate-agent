from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0046_add_listing_media_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="ad_type",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
    ]
