from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0045_add_listing_contact_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="photos",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="listing",
            name="video_url",
            field=models.URLField(blank=True, max_length=500, null=True),
        ),
    ]
