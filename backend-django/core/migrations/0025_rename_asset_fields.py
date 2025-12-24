# Generated manually to rename asset fields to standardized names

from django.db import migrations


def _get_columns_and_indexes(schema_editor):
    """Return the existing column names and index names for the asset table."""
    connection = schema_editor.connection
    introspection = connection.introspection
    table_name = "core_asset"

    with connection.cursor() as cursor:
        try:
            description = introspection.get_table_description(cursor, table_name)
        except Exception:
            return [], []

        columns = [col.name for col in description]

        constraints = introspection.get_constraints(cursor, table_name)
        indexes = [name for name, info in constraints.items() if info.get("index")]

    return columns, indexes


def check_and_rename_fields(apps, schema_editor):
    """Check if old fields exist and rename them if they do."""
    connection = schema_editor.connection
    quote_name = connection.ops.quote_name

    columns, indexes = _get_columns_and_indexes(schema_editor)

    if not columns:
        return

    with connection.cursor() as cursor:
        # Only rename fields that exist
        if "gush" in columns and "block" not in columns:
            cursor.execute(
                f"ALTER TABLE {quote_name('core_asset')} RENAME COLUMN {quote_name('gush')} TO {quote_name('block')}"
            )
            columns.remove("gush")
            columns.append("block")
            print("Renamed gush to block")

        if "helka" in columns and "parcel" not in columns:
            cursor.execute(
                f"ALTER TABLE {quote_name('core_asset')} RENAME COLUMN {quote_name('helka')} TO {quote_name('parcel')}"
            )
            columns.remove("helka")
            columns.append("parcel")
            print("Renamed helka to parcel")

        if "subhelka" in columns and "subparcel" not in columns:
            cursor.execute(
                f"ALTER TABLE {quote_name('core_asset')} RENAME COLUMN {quote_name('subhelka')} TO {quote_name('subparcel')}"
            )
            columns.remove("subhelka")
            columns.append("subparcel")
            print("Renamed subhelka to subparcel")

        # Handle indexes - remove old ones if they exist, create new ones if they don't
        old_indexes = [
            "core_asset_gush_dc43e9_idx",
            "core_asset_helka_38f908_idx",
            "core_asset_subhelk_ec1101_idx",  # Note: this is the truncated name
        ]

        new_indexes = [
            ("core_asset_block_dc43e9_idx", "block"),
            ("core_asset_parcel_38f908_idx", "parcel"),
            ("core_asset_subparcel_ec1101_idx", "subparcel"),
        ]

        # Remove old indexes if they exist
        for old_idx in old_indexes:
            if old_idx in indexes:
                cursor.execute(f"DROP INDEX IF EXISTS {quote_name(old_idx)}")
                print(f"Removed old index: {old_idx}")

        # Create new indexes if they don't exist
        for new_idx_name, field_name in new_indexes:
            if new_idx_name not in indexes and field_name in columns:
                cursor.execute(
                    f"CREATE INDEX IF NOT EXISTS {quote_name(new_idx_name)} "
                    f"ON {quote_name('core_asset')} ({quote_name(field_name)})"
                )
                print(f"Created new index: {new_idx_name}")


def reverse_rename_fields(apps, schema_editor):
    """Reverse the field renaming."""
    connection = schema_editor.connection
    quote_name = connection.ops.quote_name

    columns, _ = _get_columns_and_indexes(schema_editor)

    if not columns:
        return

    with connection.cursor() as cursor:
        if "block" in columns and "gush" not in columns:
            cursor.execute(
                f"ALTER TABLE {quote_name('core_asset')} RENAME COLUMN {quote_name('block')} TO {quote_name('gush')}"
            )

        if "parcel" in columns and "helka" not in columns:
            cursor.execute(
                f"ALTER TABLE {quote_name('core_asset')} RENAME COLUMN {quote_name('parcel')} TO {quote_name('helka')}"
            )

        if "subparcel" in columns and "subhelka" not in columns:
            cursor.execute(
                f"ALTER TABLE {quote_name('core_asset')} RENAME COLUMN {quote_name('subparcel')} TO {quote_name('subhelka')}"
            )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0024_fix_demo_user_plan"),
    ]

    operations = [
        migrations.RunPython(check_and_rename_fields, reverse_rename_fields),
    ]
