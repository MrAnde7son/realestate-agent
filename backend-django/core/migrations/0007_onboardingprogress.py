from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_asset_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='OnboardingProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('connect_payment', models.BooleanField(default=False)),
                ('add_first_asset', models.BooleanField(default=False)),
                ('generate_first_report', models.BooleanField(default=False)),
                ('set_one_alert', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=models.CASCADE, related_name='onboarding_progress', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
