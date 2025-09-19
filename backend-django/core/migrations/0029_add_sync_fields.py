# Generated manually for sync functionality

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_merge_0027_add_document_model_0027_auto_20250917_1102'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='last_sync_started_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='asset',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('enriching', 'Enriching'), ('syncing', 'Syncing'), ('done', 'Done'), ('failed', 'Failed')], default='pending', max_length=20),
        ),
    ]