# Generated manually to rename asset fields to standardized names

from django.db import migrations, connection


def check_and_rename_fields(apps, schema_editor):
    """Check if old fields exist and rename them if they do."""
    with connection.cursor() as cursor:
        # Check if old fields exist
        cursor.execute("PRAGMA table_info(core_asset);")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Check current indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = 'core_asset'")
        indexes = [idx[0] for idx in cursor.fetchall()]
        
        # Only rename fields that exist
        if 'gush' in columns and 'block' not in columns:
            cursor.execute("ALTER TABLE core_asset RENAME COLUMN gush TO block;")
            print("Renamed gush to block")
        
        if 'helka' in columns and 'parcel' not in columns:
            cursor.execute("ALTER TABLE core_asset RENAME COLUMN helka TO parcel;")
            print("Renamed helka to parcel")
            
        if 'subhelka' in columns and 'subparcel' not in columns:
            cursor.execute("ALTER TABLE core_asset RENAME COLUMN subhelka TO subparcel;")
            print("Renamed subhelka to subparcel")
        
        # Handle indexes - remove old ones if they exist, create new ones if they don't
        old_indexes = [
            'core_asset_gush_dc43e9_idx',
            'core_asset_helka_38f908_idx', 
            'core_asset_subhelk_ec1101_idx'  # Note: this is the truncated name
        ]
        
        new_indexes = [
            ('core_asset_block_dc43e9_idx', 'block'),
            ('core_asset_parcel_38f908_idx', 'parcel'),
            ('core_asset_subparcel_ec1101_idx', 'subparcel')
        ]
        
        # Remove old indexes if they exist
        for old_idx in old_indexes:
            if old_idx in indexes:
                cursor.execute(f"DROP INDEX {old_idx}")
                print(f"Removed old index: {old_idx}")
        
        # Create new indexes if they don't exist
        for new_idx_name, field_name in new_indexes:
            if new_idx_name not in indexes:
                cursor.execute(f"CREATE INDEX {new_idx_name} ON core_asset ({field_name})")
                print(f"Created new index: {new_idx_name}")


def reverse_rename_fields(apps, schema_editor):
    """Reverse the field renaming."""
    with connection.cursor() as cursor:
        # Check if new fields exist and rename them back
        cursor.execute("PRAGMA table_info(core_asset);")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'block' in columns and 'gush' not in columns:
            cursor.execute("ALTER TABLE core_asset RENAME COLUMN block TO gush;")
            
        if 'parcel' in columns and 'helka' not in columns:
            cursor.execute("ALTER TABLE core_asset RENAME COLUMN parcel TO helka;")
            
        if 'subparcel' in columns and 'subhelka' not in columns:
            cursor.execute("ALTER TABLE core_asset RENAME COLUMN subparcel TO subhelka;")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_fix_demo_user_plan'),
    ]

    operations = [
        migrations.RunPython(check_and_rename_fields, reverse_rename_fields),
    ]
