from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_update_user_roles'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='equity',
            field=models.DecimalField(
                max_digits=12,
                decimal_places=2,
                blank=True,
                null=True,
                help_text='Equity amount saved for default mortgage calculations',
            ),
        ),
    ]
