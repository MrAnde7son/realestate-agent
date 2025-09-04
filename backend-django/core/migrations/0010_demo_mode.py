from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_sharetoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_demo',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='asset',
            name='is_demo',
            field=models.BooleanField(default=False),
        ),
    ]
