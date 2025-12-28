# Generated migration for OAuthAuthorizationCode model

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        (
            "core",
            "0055_rename_core_apitok_token_idx_core_apitok_token_8d7878_idx_and_more",
        ),
    ]

    operations = [
        migrations.CreateModel(
            name="OAuthAuthorizationCode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("code", models.CharField(db_index=True, max_length=128, unique=True)),
                ("client_id", models.CharField(db_index=True, max_length=255)),
                ("redirect_uri", models.URLField()),
                (
                    "code_challenge",
                    models.CharField(blank=True, max_length=128, null=True),
                ),
                (
                    "code_challenge_method",
                    models.CharField(default="plain", max_length=10),
                ),
                ("scope", models.TextField(default="")),
                ("expires_at", models.DateTimeField(db_index=True)),
                ("used", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="oauthauthorizationcode",
            index=models.Index(fields=["code"], name="core_oauth_code_idx"),
        ),
        migrations.AddIndex(
            model_name="oauthauthorizationcode",
            index=models.Index(
                fields=["client_id", "used"], name="core_oauth_client_used_idx"
            ),
        ),
    ]
