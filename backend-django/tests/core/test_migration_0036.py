import importlib

import pytest
from django.db import connection


migration = importlib.import_module("core.migrations.0036_add_ppm_metrics")


pytestmark = pytest.mark.django_db(transaction=True)


def test_ensure_asset_ppm_index_names_handles_missing_legacy_indexes():
    canonical_indexes = {
        "core_asset_block_531195_idx",
        "core_asset_parcel_ebd705_idx",
        "core_asset_subparc_d57846_idx",
    }

    legacy_indexes = {
        "core_asset_block_dc43e9_idx",
        "core_asset_parcel_38f908_idx",
        "core_asset_subhelk_ec1101_idx",
        "core_asset_subparcel_ec1101_idx",
    }

    index_names = canonical_indexes | legacy_indexes

    with connection.schema_editor() as schema_editor:
        with connection.cursor() as cursor:
            for index_name in index_names:
                migration._drop_index_if_exists(
                    cursor,
                    schema_editor,
                    index_name,
                )

    with connection.schema_editor() as schema_editor:
        migration.ensure_asset_ppm_index_names(
            None,
            schema_editor,
        )

    with connection.schema_editor() as schema_editor:
        existing = migration._fetch_existing_indexes(
            schema_editor,
            "core_asset",
        )

    for index_name in canonical_indexes:
        assert index_name in existing
