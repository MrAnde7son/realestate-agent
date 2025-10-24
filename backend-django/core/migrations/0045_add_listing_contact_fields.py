from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0044_add_plan_title"),
    ]

    operations = [
        migrations.AddField(
            model_name="listing",
            name="contact_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="listing",
            name="contact_phone",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name="listing",
            name="listing_type",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AddField(
            model_name="listing",
            name="recent_deal",
            field=models.BooleanField(default=False),
        ),
    ]
