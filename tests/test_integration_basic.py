#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple integration test for the address sync functionality.
"""

import sys
import os
import json

# Add project root to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_local_tasks():
    """Test the local task functions directly."""
    print("Testing Local Task Functions...")
    
    try:
        from backend_django.core.tasks import _parse_street_number
        
        # Test address parsing
        print("\nTesting address parsing...")
        test_cases = [
            "הגולן 1",
            "רחוב הרצל 123", 
            "שדרות רוטשילד 45",
            "invalid address"
        ]
        
        for addr in test_cases:
            try:
                street, number = _parse_street_number(addr)
                if street and number:
                    print(f"   SUCCESS: '{addr}' -> '{street}', {number}")
                else:
                    print(f"   FAILED: '{addr}' -> Could not parse")
            except Exception as e:
                print(f"   ERROR: '{addr}' -> {e}")
        
    except ImportError as e:
        print(f"   Import error: {e}")
        print("   Make sure you're in the project root directory")


def test_database_models():
    """Test database model functionality."""
    print("\nTesting Database Models...")
    
    try:
        from db.database import SQLAlchemyDatabase
        from db.models import Listing
        
        # Test database connection
        db = SQLAlchemyDatabase()
        print("   SUCCESS: Database connection created")
        
        # Try to initialize database
        try:
            db.init_db()
            print("   SUCCESS: Database initialized")
        except Exception as e:
            print(f"   WARNING: Database init issue: {e}")
        
        # Test session creation
        try:
            with db.get_session() as session:
                count = session.query(Listing).count()
                print(f"   SUCCESS: Database session works: {count} listings in DB")
        except Exception as e:
            print(f"   WARNING: Database query issue: {e}")
        
    except ImportError as e:
        print(f"   Import error: {e}")


def print_environment_info():
    """Print information about the current environment."""
    print("Environment Information:")
    print(f"   Python: {sys.version}")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Script Location: {os.path.dirname(__file__)}")
    
    # Check for required environment variables
    env_vars = ["DATABASE_URL", "BACKEND_URL"]
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        print(f"   {var}: {value}")


def main():
    """Run basic integration tests."""
    print("Real Estate Agent - Basic Integration Test")
    print("=" * 50)
    
    print_environment_info()
    
    print("\n" + "=" * 50)
    test_database_models()
    
    print("\n" + "=" * 50)
    test_local_tasks()
    
    print("\n" + "=" * 50)
    print("Basic tests completed!")
    print("\nTo test the full system:")
    print("1. Start Django backend: cd backend-django && python manage.py runserver")
    print("2. Start Next.js frontend: cd realestate-broker-ui && npm run dev")
    print("3. Visit http://localhost:3000")


if __name__ == "__main__":
    main()
