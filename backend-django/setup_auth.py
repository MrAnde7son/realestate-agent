#!/usr/bin/env python3
"""
Setup script for Django authentication system.
Run this script to initialize the database and create a test user.
"""

import os
import sys
import django

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'broker_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import execute_from_command_line

User = get_user_model()

def setup_database():
    """Set up the database and create initial data."""
    print("Setting up Django database...")
    
    # Run migrations
    print("Running migrations...")
    try:
        execute_from_command_line(['manage.py', 'makemigrations'])
        execute_from_command_line(['manage.py', 'migrate'])
        print("✓ Migrations completed successfully")
    except Exception as e:
        print(f"⚠ Warning: Migration error (this may be normal): {e}")
    
    # Create superuser if it doesn't exist
    if not User.objects.filter(is_superuser=True).exists():
        print("Creating superuser...")
        try:
            user = User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                first_name='מנהל',
                last_name='מערכת',
                company='נדל״נר',
                role='מנהל מערכת'
            )
            print(f"✓ Superuser created: {user.email}")
        except Exception as e:
            print(f"✗ Error creating superuser: {e}")
    
    # Create test user if it doesn't exist
    if not User.objects.filter(email='demo@example.com').exists():
        print("Creating test user...")
        try:
            user = User.objects.create_user(
                username='demo',
                email='demo@example.com',
                password='demo123',
                first_name='משתמש',
                last_name='דמו',
                company='נדל״ן דמו בע״מ',
                role='מתווך נדל״ן'
            )
            print(f"✓ Test user created: {user.email}")
        except Exception as e:
            print(f"✗ Error creating test user: {e}")
    
    print("\n" + "="*50)
    print("Database setup complete!")
    print("="*50)
    print("\nTest accounts:")
    print("Admin: admin@example.com / admin123")
    print("Demo: demo@example.com / demo123")
    print("\nNote: Some features may return dummy data if external")
    print("dependencies are not available. This is normal for testing.")
    print("\nTo start the server:")
    print("python manage.py runserver")

if __name__ == '__main__':
    setup_database()
