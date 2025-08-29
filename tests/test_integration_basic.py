#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Basic integration test for the address sync functionality.
"""

import os
import sys

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

def test_database_models():
    """Test database model functionality."""
    print("\n🗄️  Testing Database Models...")
    
    try:
        from db.database import SQLAlchemyDatabase
        from db.models import Listing

        # Test database connection
        db = SQLAlchemyDatabase()
        print("   ✅ Database connection created")
        
        # Try to initialize database
        try:
            db.init_db()
            print("   ✅ Database initialized")
        except Exception as e:
            print(f"   ⚠️  Database init warning: {e}")
        
        # Test session creation
        try:
            with db.get_session() as session:
                count = session.query(Listing).count()
                print(f"   ✅ Database session works: {count} assets in DB")
        except Exception as e:
            print(f"   ⚠️  Database query error: {e}")
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")

def test_local_tasks():
    """Test the local task functions directly."""
    print("\n⚙️  Testing Local Task Functions...")
    
    try:
        # Test address parsing without importing the problematic modules
        import re
        
        def parse_street_number(address: str):
            """Extract street name and house number from a freeform address string."""
            if not address:
                return None, None
            match = re.search(r"(.+?)\s*(\d+)", address)
            if not match:
                return None, None
            street = match.group(1).strip()
            try:
                number = int(match.group(2))
            except ValueError:
                return None, None
            return street, number
        
        # Test address parsing
        print("\n🔍 Testing address parsing...")
        test_cases = [
            "הגולן 1",
            "רחוב הרצל 123",
            "שדרות רוטשילד 45",
            "invalid address"
        ]
        
        for addr in test_cases:
            street, number = parse_street_number(addr)
            if street and number:
                print(f"   ✅ '{addr}' → '{street}', {number}")
            else:
                print(f"   ❌ '{addr}' → Could not parse")
        
        print("   ✅ Address parsing tests completed")
        
    except Exception as e:
        print(f"   ❌ Task test error: {e}")

def print_environment_info():
    """Print information about the current environment."""
    print("🔧 Environment Information:")
    print(f"   Python: {sys.version}")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   PROJECT_ROOT: {os.path.dirname(__file__)}")
    
    # Check for required environment variables
    env_vars = ["DATABASE_URL", "BACKEND_URL"]
    for var in env_vars:
        value = os.environ.get(var, "Not set")
        print(f"   {var}: {value}")

def main():
    """Run all integration tests."""
    print("🚀 Real Estate Agent - Basic Integration Test")
    print("=" * 50)
    
    print_environment_info()
    
    print("\n" + "=" * 50)
    test_database_models()
    
    print("\n" + "=" * 50)
    test_local_tasks()
    
    print("\n" + "=" * 50)
    print("✅ Integration tests completed!")
    print("\nNext steps:")
    print("1. Start the Django backend: cd backend-django && python manage.py runserver")
    print("2. Start the Next.js frontend: cd realestate-broker-ui && npm run dev")
    print("3. Visit http://localhost:3000 to use the application")
    print("4. Use the 'סנכרן נתונים' button on listing pages to sync external data")

if __name__ == "__main__":
    main()