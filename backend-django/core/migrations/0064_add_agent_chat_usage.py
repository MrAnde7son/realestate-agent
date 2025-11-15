# Generated migration for AgentChatUsage model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0063_rename_core_apitok_token_idx_core_apitok_token_8d7878_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AgentChatUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('questions_count', models.IntegerField(default=0, help_text='Number of questions asked in the current period')),
                ('last_reset_at', models.DateTimeField(auto_now_add=True, help_text='When the counter was last reset')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='agent_chat_usage', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name='agentchatusage',
            index=models.Index(fields=['user'], name='core_agentc_user_idx'),
        ),
        migrations.AddIndex(
            model_name='agentchatusage',
            index=models.Index(fields=['questions_count'], name='core_agentc_questio_idx'),
        ),
    ]

