from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_demo_mode'),
    ]

    operations = [
        migrations.CreateModel(
            name='AnalyticsEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.CharField(max_length=100)),
                ('asset_id', models.IntegerField(blank=True, null=True)),
                ('source', models.CharField(blank=True, max_length=100, null=True)),
                ('error_code', models.CharField(blank=True, max_length=100, null=True)),
                ('meta', models.JSONField(blank=True, default=dict)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='analytics_events', to='core.user')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['created_at'], name='core_analy_created_1a634f_idx'),
                    models.Index(fields=['event'], name='core_analy_event_8d3b50_idx'),
                    models.Index(fields=['source'], name='core_analy_source_12d921_idx'),
                    models.Index(fields=['error_code'], name='core_analy_error_c_1b9f5f_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='AnalyticsDaily',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('users', models.IntegerField(default=0)),
                ('assets', models.IntegerField(default=0)),
                ('reports', models.IntegerField(default=0)),
                ('alerts', models.IntegerField(default=0)),
                ('errors', models.IntegerField(default=0)),
            ],
            options={
                'indexes': [models.Index(fields=['date'], name='core_analy_date_4b2427_idx')],
            },
        ),
    ]
