from django.db import migrations, models


def forwards(apps, schema_editor):
    Asset = apps.get_model('core', 'Asset')
    Asset.objects.filter(status='ready').update(status='done')
    Asset.objects.filter(status='error').update(status='failed')


def backwards(apps, schema_editor):
    Asset = apps.get_model('core', 'Asset')
    Asset.objects.filter(status='done').update(status='ready')
    Asset.objects.filter(status='failed').update(status='error')


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0015_merge_20250905_0933'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='last_enriched_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='last_enrich_error',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(forwards, backwards),
        migrations.AlterField(
            model_name='asset',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending'),
                    ('enriching', 'Enriching'),
                    ('done', 'Done'),
                    ('failed', 'Failed'),
                ],
                default='pending',
                max_length=20,
            ),
        ),
    ]
