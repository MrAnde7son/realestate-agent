# Generated manually
# flake8: noqa

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deal_workspace", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="deal",
            name="closing_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]

