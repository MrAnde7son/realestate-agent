from django.contrib.auth.hashers import make_password
from django.db import migrations


def create_initial_users(apps, schema_editor):
    User = apps.get_model('core', 'User')
    
    # Only create users if this is a completely fresh database
    # Check if there are ANY users in the system
    if User.objects.count() == 0:
        # Create admin user
        User.objects.create(
            username='admin',
            email='admin@example.com',
            password=make_password('admin123'),
            first_name='מנהל',
            last_name='מערכת',
            company='נדל״נר',
            role='מנהל מערכת',
            is_superuser=True,
            is_staff=True,
            is_active=True
        )
        
        # Create demo user
        User.objects.create(
            username='demo',
            email='demo@example.com',
            password=make_password('demo123'),
            first_name='משתמש',
            last_name='דמו',
            company='נדל״ן דמו בע״מ',
            role='מתווך נדל״ן',
            is_active=True
        )
        print("✓ Initial users created for fresh database")
    else:
        print("✓ Database has existing users, skipping initial user creation")

def reverse_create_initial_users(apps, schema_editor):
    # Don't delete users in reverse migration - this protects existing data
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0002_asset_sourcerecord_realestatetransaction_and_more'),
    ]

    operations = [
        migrations.RunPython(create_initial_users, reverse_create_initial_users),
    ]
