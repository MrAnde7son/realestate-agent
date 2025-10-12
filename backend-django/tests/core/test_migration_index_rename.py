import importlib
from dataclasses import dataclass

import pytest


migration_module = importlib.import_module(
    "core.migrations.0042_add_global_source_tables"
)

MUTATING_PREFIXES = ("ALTER INDEX", "DROP INDEX")


class DummyCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        self.connection.commands.append((sql, params))

        normalized = sql.strip().upper()
        if normalized.startswith("ALTER INDEX") and "RENAME TO" in normalized:
            parts = sql.strip().split()
            old_name = parts[2]
            new_name = parts[-1]
            self.connection.existing_indexes.discard(old_name)
            self.connection.existing_indexes.add(new_name)
        elif normalized.startswith("DROP INDEX"):
            parts = sql.strip().split()
            if len(parts) >= 3:
                index_name = parts[2]
                self.connection.existing_indexes.discard(index_name)
        elif normalized.startswith("CREATE INDEX"):
            parts = sql.strip().split()
            if len(parts) >= 3:
                index_name = parts[2]
                self.connection.existing_indexes.add(index_name)

    def fetchall(self):
        return [
            (index_name,)
            for index_name in sorted(self.connection.existing_indexes)
        ]


@dataclass
class DummyConnection:
    vendor: str
    existing_indexes: set

    def __post_init__(self):
        self.commands = []

    def cursor(self):
        return DummyCursor(self)


class DummySchemaEditor:
    def __init__(self, vendor, existing_indexes):
        self.connection = DummyConnection(vendor, set(existing_indexes))

    def quote_name(self, name):
        return name


@pytest.mark.parametrize("vendor", ["postgresql", "sqlite"])
def test_rename_skips_when_old_indexes_absent(vendor):
    existing = {
        "core_asset_block_531195_idx",
        "core_asset_parcel_ebd705_idx",
        "core_asset_subparc_d57846_idx",
    }
    schema_editor = DummySchemaEditor(vendor, existing)

    migration_module.rename_asset_indexes_if_present(None, schema_editor)

    assert schema_editor.connection.existing_indexes == existing
    normalized_commands = [
        sql.strip().upper()
        for sql, _ in schema_editor.connection.commands
    ]
    assert not any(
        command.startswith(MUTATING_PREFIXES)
        for command in normalized_commands
    )


@pytest.mark.parametrize("vendor", ["postgresql", "sqlite"])
def test_rename_and_reverse_cycle_updates_indexes(vendor):
    original = {
        "core_asset_block_dc43e9_idx",
        "core_asset_parcel_38f908_idx",
        "core_asset_subhelk_ec1101_idx",
    }
    schema_editor = DummySchemaEditor(vendor, original)

    migration_module.rename_asset_indexes_if_present(None, schema_editor)

    expected_new = {
        "core_asset_block_531195_idx",
        "core_asset_parcel_ebd705_idx",
        "core_asset_subparc_d57846_idx",
    }
    assert schema_editor.connection.existing_indexes == expected_new

    migration_module.reverse_asset_index_renames_if_present(
        None, schema_editor
    )

    assert schema_editor.connection.existing_indexes == original
