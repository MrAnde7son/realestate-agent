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
        print("✓ Initial users created automatically by migration (if database was empty)")
    except Exception as e:
        print(f"⚠ Warning: Migration error (this may be normal): {e}")
    
    # Check if users exist
    admin_exists = User.objects.filter(email='admin@example.com').exists()
    demo_exists = User.objects.filter(email='demo@example.com').exists()
    
    print("\n" + "="*50)
    print("Database setup complete!")
    print("="*50)
    print("\nUser status:")
    print(f"Admin user: {'✓ Exists' if admin_exists else '✗ Missing'}")
    print(f"Demo user: {'✓ Exists' if demo_exists else '✗ Missing'}")
    
    if admin_exists and demo_exists:
        print("\nTest accounts:")
        print("Admin: admin@example.com / admin123")
        print("Demo: demo@example.com / demo123")
    else:
        print("\n⚠ Some users are missing. Check the migration output above.")
    
    print("\nNote: Users are now created automatically by migrations.")
    print("This ensures they exist after every deployment without conflicts.")
    print("\nTo start the server:")
    print("python manage.py runserver")

if __name__ == '__main__':
    setup_database()
