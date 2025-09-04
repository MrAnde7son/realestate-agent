from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_merge_0007_onboardingprogress_0007_plan_permit'),
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
