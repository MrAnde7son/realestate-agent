from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0034_remove_permit_core_permit_request_num_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='price_gap_pct',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='expected_price_range',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='model_price',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='confidence_pct',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='delta_vs_area_pct',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='cap_rate_pct',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='competition_1km',
            field=models.CharField(max_length=20, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='risk_flags',
            field=models.JSONField(blank=True, null=True, default=list),
        ),
        migrations.AddField(
            model_name='asset',
            name='dom_percentile',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]

