# Generated migration for APIToken model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0051_assetwatchlistentry_asset_watchers_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='APIToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="A descriptive name for this token (e.g., 'MCP Server', 'LangChain Agent')", max_length=100)),
                ('token', models.CharField(db_index=True, max_length=64, unique=True)),
                ('last_used_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='api_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='apitoken',
            index=models.Index(fields=['token'], name='core_apitok_token_idx'),
        ),
        migrations.AddIndex(
            model_name='apitoken',
            index=models.Index(fields=['user', 'is_active'], name='core_apitok_user_id_idx'),
        ),
    ]

