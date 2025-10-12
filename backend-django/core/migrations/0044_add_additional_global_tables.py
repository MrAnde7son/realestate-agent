# Generated manually for additional global tables

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0043_promote_existing_data_to_globals'),
    ]

    operations = [
        migrations.CreateModel(
            name='GisDataGlobal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gis_id', models.CharField(db_index=True, max_length=100, unique=True)),
                ('key_fp', models.CharField(db_index=True, help_text='Stable fingerprint from cadastral identifiers', max_length=64)),
                ('key_json', models.JSONField(default=dict, help_text='Cadastral identifiers for debugging')),
                ('x', models.FloatField(blank=True, help_text='ITM X coordinate', null=True)),
                ('y', models.FloatField(blank=True, help_text='ITM Y coordinate', null=True)),
                ('block', models.CharField(blank=True, max_length=50, null=True)),
                ('parcel', models.CharField(blank=True, max_length=50, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('blocks_data', models.JSONField(default=list, help_text='Block information')),
                ('parcels_data', models.JSONField(default=list, help_text='Parcel information')),
                ('permits_data', models.JSONField(default=list, help_text='Building permits')),
                ('rights_data', models.JSONField(default=list, help_text='Land use rights')),
                ('shelters_data', models.JSONField(default=list, help_text='Shelter information')),
                ('green_areas_data', models.JSONField(default=list, help_text='Green areas')),
                ('noise_levels_data', models.JSONField(default=list, help_text='Noise levels')),
                ('antennas_data', models.JSONField(default=list, help_text='Cell antennas')),
                ('land_use_detailed_data', models.JSONField(default=list, help_text='Detailed land use')),
                ('preservation_data', models.JSONField(default=list, help_text='Preservation data')),
                ('dangerous_buildings_data', models.JSONField(default=list, help_text='Dangerous buildings')),
                ('local_plans_data', models.JSONField(default=list, help_text='Local plans')),
                ('city_plans_data', models.JSONField(default=list, help_text='City-wide plans')),
                ('addresses_data', models.JSONField(default=list, help_text='Address information')),
                ('raw', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ttl_expires_at', models.DateTimeField(blank=True, help_text='TTL expiration for data refresh', null=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['gis_id'], name='idx_gis_id'),
                    models.Index(fields=['key_fp'], name='idx_key_fp'),
                    models.Index(fields=['ttl_expires_at'], name='idx_ttl_expires_at'),
                    models.Index(fields=['block', 'parcel'], name='idx_block_parcel'),
                ],
            },
        ),
        migrations.CreateModel(
            name='GovMapDataGlobal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('govmap_id', models.CharField(db_index=True, max_length=100, unique=True)),
                ('key_fp', models.CharField(db_index=True, help_text='Stable fingerprint from cadastral identifiers', max_length=64)),
                ('key_json', models.JSONField(default=dict, help_text='Cadastral identifiers for debugging')),
                ('address', models.CharField(blank=True, max_length=200, null=True)),
                ('x', models.FloatField(blank=True, help_text='ITM X coordinate', null=True)),
                ('y', models.FloatField(blank=True, help_text='ITM Y coordinate', null=True)),
                ('block', models.CharField(blank=True, max_length=50, null=True)),
                ('parcel', models.CharField(blank=True, max_length=50, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('autocomplete_data', models.JSONField(default=dict, help_text='Autocomplete results')),
                ('parcel_data', models.JSONField(default=dict, help_text='Parcel API data')),
                ('layers_catalog_data', models.JSONField(default=dict, help_text='Layers catalog')),
                ('search_types_data', models.JSONField(default=dict, help_text='Search types')),
                ('raw', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ttl_expires_at', models.DateTimeField(blank=True, help_text='TTL expiration for data refresh', null=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['govmap_id'], name='idx_govmap_id'),
                    models.Index(fields=['key_fp'], name='idx_key_fp'),
                    models.Index(fields=['ttl_expires_at'], name='idx_ttl_expires_at'),
                    models.Index(fields=['block', 'parcel'], name='idx_block_parcel'),
                ],
            },
        ),
        migrations.CreateModel(
            name='GovDataGlobal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gov_id', models.CharField(db_index=True, max_length=100, unique=True)),
                ('key_fp', models.CharField(db_index=True, help_text='Stable fingerprint from cadastral identifiers', max_length=64)),
                ('key_json', models.JSONField(default=dict, help_text='Cadastral identifiers for debugging')),
                ('block', models.CharField(blank=True, max_length=50, null=True)),
                ('parcel', models.CharField(blank=True, max_length=50, null=True)),
                ('transactions_data', models.JSONField(default=list, help_text='Transaction history')),
                ('decisive_data', models.JSONField(default=list, help_text='Decisive appraisals')),
                ('rami_plans_data', models.JSONField(default=list, help_text='RAMI plans')),
                ('raw', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ttl_expires_at', models.DateTimeField(blank=True, help_text='TTL expiration for data refresh', null=True)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['gov_id'], name='idx_gov_id'),
                    models.Index(fields=['key_fp'], name='idx_key_fp'),
                    models.Index(fields=['ttl_expires_at'], name='idx_ttl_expires_at'),
                    models.Index(fields=['block', 'parcel'], name='idx_block_parcel'),
                ],
            },
        ),
        migrations.CreateModel(
            name='AssetToGisData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gis_links', to='core.asset')),
                ('gis_data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asset_links', to='core.gisdataglobal')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['asset'], name='idx_asset_id'),
                    models.Index(fields=['gis_data'], name='idx_gis_data_id'),
                ],
            },
        ),
        migrations.CreateModel(
            name='AssetToGovMapData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='govmap_links', to='core.asset')),
                ('govmap_data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asset_links', to='core.govmapdataglobal')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['asset'], name='idx_asset_id'),
                    models.Index(fields=['govmap_data'], name='idx_govmap_data_id'),
                ],
            },
        ),
        migrations.CreateModel(
            name='AssetToGovData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gov_links', to='core.asset')),
                ('gov_data', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='asset_links', to='core.govdataglobal')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['asset'], name='idx_asset_id'),
                    models.Index(fields=['gov_data'], name='idx_gov_data_id'),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name='assettogisdata',
            constraint=models.UniqueConstraint(fields=('asset', 'gis_data'), name='unique_asset_gis_data'),
        ),
        migrations.AddConstraint(
            model_name='assettogovmapdata',
            constraint=models.UniqueConstraint(fields=('asset', 'govmap_data'), name='unique_asset_govmap_data'),
        ),
        migrations.AddConstraint(
            model_name='assettogovdata',
            constraint=models.UniqueConstraint(fields=('asset', 'gov_data'), name='unique_asset_gov_data'),
        ),
    ]
