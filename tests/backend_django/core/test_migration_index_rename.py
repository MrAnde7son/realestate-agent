"""Tests for the safe index rename helper used in migrations."""

import importlib

from django.db import ProgrammingError

migration_module = importlib.import_module(
    "core.migrations.0054_rename_core_apitok_token_idx_core_apitok_token_8d7878_idx_and_more"
)


class DummyCursor:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class DummyIntrospection:
    def __init__(self, constraints):
        self._constraints = constraints

    def get_constraints(self, cursor, table_name):
        return self._constraints


class DummyConnection:
    vendor = "postgresql"

    def __init__(self, constraints):
        self.introspection = DummyIntrospection(constraints)

    def cursor(self):
        return DummyCursor()


class DummySchemaEditor:
    def __init__(self, constraints, *, exception=None):
        self.connection = DummyConnection(constraints)
        self._exception = exception
        self.executed = []

    def quote_name(self, value):
        return f'"{value}"'

    def execute(self, sql):
        if self._exception is not None:
            raise self._exception
        self.executed.append(sql)


def call_helper(*args, **kwargs):
    return migration_module.rename_index_if_exists(*args, **kwargs)


def test_rename_skips_when_index_missing():
    schema_editor = DummySchemaEditor(constraints={})

    call_helper(None, schema_editor, "core_apitoken", "old_idx", "new_idx")

    assert schema_editor.executed == []


def test_rename_executes_when_index_present():
    schema_editor = DummySchemaEditor(constraints={"old_idx": {}})

    call_helper(None, schema_editor, "core_apitoken", "old_idx", "new_idx")

    assert schema_editor.executed == ['ALTER INDEX "old_idx" RENAME TO "new_idx"']


def test_rename_ignores_programming_error_when_index_missing():
    schema_editor = DummySchemaEditor(
        constraints={"old_idx": {}}, exception=ProgrammingError("missing")
    )

    call_helper(None, schema_editor, "core_apitoken", "old_idx", "new_idx")

    # The ProgrammingError is swallowed by the helper and no SQL is recorded.
    assert schema_editor.executed == []
