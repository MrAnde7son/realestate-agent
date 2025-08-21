#!/usr/bin/env python3
"""
Setup script for the Asset Enrichment Pipeline.
This script initializes the database and creates all necessary tables.
"""

import os
import sys
import time

def setup_database():
    """Initialize the database and create tables."""
    print("🚀 Setting up Asset Enrichment Pipeline Database...")
    
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    try:
        # Initialize SQLAlchemy database
        print("📦 Initializing SQLAlchemy database...")
        from db.database import SQLAlchemyDatabase
        
        db = SQLAlchemyDatabase()
        if db.init_db():
            print("✅ SQLAlchemy database initialized successfully")
        else:
            print("❌ Failed to initialize SQLAlchemy database")
            return False
        
        # Create tables
        print("🏗️  Creating database tables...")
        if db.create_tables():
            print("✅ Database tables created successfully")
        else:
            print("❌ Failed to create database tables")
            return False
        
        # Test database connection
        print("🔍 Testing database connection...")
        try:
            with db.get_session() as session:
                # Test query
                result = session.execute("SELECT 1")
                print("✅ Database connection test successful")
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False
        
        db.close()
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def setup_django():
    """Setup Django database."""
    print("\n🐍 Setting up Django database...")
    
    try:
        # Change to Django directory
        django_dir = os.path.join(os.path.dirname(__file__), 'backend-django')
        os.chdir(django_dir)
        
        # Run Django migrations
        print("🔄 Running Django migrations...")
        os.system("python manage.py makemigrations")
        os.system("python manage.py migrate")
        
        print("✅ Django database setup completed")
        return True
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False

def create_sample_assets():
    """Create sample assets for testing."""
    print("\n🎯 Creating sample assets...")
    
    try:
        from db.database import SQLAlchemyDatabase
        from db.models import Asset
        
        db = SQLAlchemyDatabase()
        
        # Sample assets
        sample_assets = [
            {
                'scope_type': 'neighborhood',
                'city': 'תל אביב',
                'neighborhood': 'רמת החייל',
                'status': 'ready',
                'meta': {
                    'scope': {'type': 'neighborhood', 'value': 'רמת החייל', 'city': 'תל אביב'},
                    'radius': 250
                }
            },
            {
                'scope_type': 'address',
                'city': 'תל אביב',
                'street': 'הגולן',
                'number': 32,
                'status': 'ready',
                'meta': {
                    'scope': {'type': 'address', 'value': 'הגולן 32, תל אביב', 'city': 'תל אביב'},
                    'radius': 150
                }
            }
        ]
        
        with db.get_session() as session:
            for asset_data in sample_assets:
                asset = Asset(**asset_data)
                session.add(asset)
            
            session.commit()
            print(f"✅ Created {len(sample_assets)} sample assets")
            session.close()
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create sample assets: {e}")
        return False

def main():
    """Main setup function."""
    print("🏗️  Asset Enrichment Pipeline Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('db') or not os.path.exists('backend-django'):
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("❌ Database setup failed")
        sys.exit(1)
    
    # Setup Django
    if not setup_django():
        print("❌ Django setup failed")
        sys.exit(1)
    
    # Create sample assets
    if not create_sample_assets():
        print("⚠️  Sample assets creation failed (non-critical)")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the services: docker-compose up")
    print("2. The backend will be available at: http://localhost:8000")
    print("3. The frontend will be available at: http://localhost:3000")
    print("4. Celery workers will process asset enrichment tasks")
    print("\nYou can now create assets through the UI!")

if __name__ == "__main__":
    main()
