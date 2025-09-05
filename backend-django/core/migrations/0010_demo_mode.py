from django.db import migrations, models


def add_demo_columns(apps, schema_editor):
    vendor = schema_editor.connection.vendor
    if vendor == "postgresql":
        schema_editor.execute(
            "ALTER TABLE core_user ADD COLUMN IF NOT EXISTS is_demo boolean NOT NULL DEFAULT false"
        )
        schema_editor.execute(
            "ALTER TABLE core_asset ADD COLUMN IF NOT EXISTS is_demo boolean NOT NULL DEFAULT false"
        )
    else:
        schema_editor.execute(
            "ALTER TABLE core_user ADD COLUMN is_demo boolean NOT NULL DEFAULT false"
        )
        schema_editor.execute(
            "ALTER TABLE core_asset ADD COLUMN is_demo boolean NOT NULL DEFAULT false"
        )


def drop_demo_columns(apps, schema_editor):
    schema_editor.execute(
        "ALTER TABLE core_user DROP COLUMN IF EXISTS is_demo"
    )
    schema_editor.execute(
        "ALTER TABLE core_asset DROP COLUMN IF EXISTS is_demo"
    )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_sharetoken"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(add_demo_columns, drop_demo_columns),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="user",
                    name="is_demo",
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name="asset",
                    name="is_demo",
                    field=models.BooleanField(default=False),
                ),
            ],
        ),
    ]

