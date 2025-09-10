# Generated manually to rename apartment_number to apartment

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_add_apartment_number'),
    ]

    operations = [
        migrations.RenameField(
            model_name='asset',
            old_name='apartment_number',
            new_name='apartment',
        ),
    ]
