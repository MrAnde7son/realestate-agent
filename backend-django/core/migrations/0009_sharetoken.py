from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_merge_0007_onboardingprogress_0007_plan_permit'),
    ]

    operations = [
        migrations.CreateModel(
            name='ShareToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('asset', models.ForeignKey(on_delete=models.CASCADE, related_name='share_tokens', to='core.asset')),
            ],
        ),
        migrations.AddIndex(
            model_name='sharetoken',
            index=models.Index(fields=['token'], name='core_sharet_token_idx'),
        ),
        migrations.AddIndex(
            model_name='sharetoken',
            index=models.Index(fields=['expires_at'], name='core_sharet_expires_idx'),
        ),
    ]
