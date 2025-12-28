"""Safe index renames for Postgres deployments."""

from django.db import migrations


INDEX_RENAMES = (
    (
        "core_apitoken",
        "core_apitok_token_idx",
        "core_apitok_token_8d7878_idx",
    ),
    (
        "core_apitoken",
        "core_apitok_user_id_idx",
        "core_apitok_user_id_210ba8_idx",
    ),
    (
        "core_asset",
        "core_asset_block_dc43e9_idx",
        "core_asset_block_531195_idx",
    ),
    (
        "core_asset",
        "core_asset_parcel_38f908_idx",
        "core_asset_parcel_ebd705_idx",
    ),
    (
        "core_asset",
        "core_asset_subhelk_ec1101_idx",
        "core_asset_subparc_d57846_idx",
    ),
)


def rename_index_if_exists(
    apps,
    schema_editor,
    table_name,
    old_name,
    new_name,
):
    """Rename an index only when the expected source index is present."""
    if schema_editor.connection.vendor == "sqlite":
        # SQLite lacks ALTER INDEX RENAME support; skip silently.
        return

    try:
        with schema_editor.connection.cursor() as cursor:
            introspection = schema_editor.connection.introspection
            constraints = introspection.get_constraints(
                cursor,
                table_name,
            )
    except Exception:
        # If we can't get constraints, skip this rename.
        # This can happen when the table is missing or the connection fails.
        return

    # Skip if old index doesn't exist or new index already exists
    if old_name not in constraints or new_name in constraints:
        return

    try:
        schema_editor.execute(
            "ALTER INDEX IF EXISTS {} RENAME TO {}".format(
                schema_editor.quote_name(old_name),
                schema_editor.quote_name(new_name),
            )
        )
    except Exception:
        # Catch all exceptions (ProgrammingError, OperationalError, etc.).
        # If the index is missing or already renamed, we can safely ignore it.
        return


def rename_indexes(apps, schema_editor):
    """Safely rename indexes, skipping missing or already renamed ones."""
    for table_name, old_name, new_name in INDEX_RENAMES:
        try:
            rename_index_if_exists(
                apps,
                schema_editor,
                table_name,
                old_name,
                new_name,
            )
        except Exception:
            # If anything goes wrong, continue with the next index
            # This migration is idempotent and safe to run multiple times
            pass


def revert_indexes(apps, schema_editor):
    for table_name, old_name, new_name in INDEX_RENAMES:
        rename_index_if_exists(
            apps,
            schema_editor,
            table_name,
            new_name,
            old_name,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0053_add_user_llm_api_keys"),
    ]

    operations = [
        migrations.RunPython(rename_indexes, revert_indexes),
    ]
