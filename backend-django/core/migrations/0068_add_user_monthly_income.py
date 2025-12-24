from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "core",
            "0067_rename_core_asset_total_p_41022b_idx_core_asset_permit__0fa22a_idx",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="monthly_income",
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                blank=True,
                null=True,
                help_text="Monthly income for mortgage affordability calculations",
            ),
        ),
    ]
