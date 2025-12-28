# Generated manually to fix RealEstateTransaction.raw field data format

import json
from django.db import migrations


def fix_raw_field_data(apps, schema_editor):
    """
    Fix RealEstateTransaction records where raw field is a JSONB string instead of an object.
    Converts string values to proper JSON objects with data_source field.
    """
    RealEstateTransaction = apps.get_model("core", "RealEstateTransaction")

    # Get all transactions with non-null raw field
    transactions = RealEstateTransaction.objects.filter(raw__isnull=False)

    fixed_count = 0
    for transaction in transactions:
        raw_value = transaction.raw

        # Check if raw is a string (not a dict/object)
        # This handles both SQLite (where JSON is stored as text) and PostgreSQL (JSONB)
        if isinstance(raw_value, str):
            try:
                # Try to parse as JSON - if it's already a JSON string like '"government"'
                parsed = json.loads(raw_value)
                if isinstance(parsed, str):
                    # It's a JSON string value, convert to object
                    if parsed == "government":
                        transaction.raw = {"data_source": "government"}
                    else:
                        transaction.raw = {"data_source": parsed}
                    transaction.save(update_fields=["raw"])
                    fixed_count += 1
            except (json.JSONDecodeError, TypeError):
                # It's a plain string, not JSON - convert to object
                if raw_value == "government":
                    transaction.raw = {"data_source": "government"}
                else:
                    transaction.raw = {"data_source": raw_value}
                transaction.save(update_fields=["raw"])
                fixed_count += 1
        elif not isinstance(raw_value, dict):
            # If it's not a dict and not a string, convert to dict
            transaction.raw = {"data_source": "government"}
            transaction.save(update_fields=["raw"])
            fixed_count += 1

    if fixed_count > 0:
        print(
            f"Fixed {fixed_count} RealEstateTransaction records with invalid raw field format"
        )


def reverse_fix_raw_field_data(apps, schema_editor):
    """
    Reverse migration - convert back to string format if needed.
    This is a one-way migration in practice, but included for completeness.
    """
    # This migration is not easily reversible without losing data
    # In practice, we don't want to reverse this
    pass


class Migration(migrations.Migration):
    dependencies = [
        (
            "core",
            "0071_rename_core_asset_permit__0fa22a_idx_core_asset_total_p_41022b_idx_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(fix_raw_field_data, reverse_fix_raw_field_data),
    ]
