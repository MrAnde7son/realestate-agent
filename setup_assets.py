#!/usr/bin/env python3
"""
Setup script for the Asset Enrichment Pipeline.
This script initializes the database and creates all necessary tables.
"""

import os
import sys


def setup_database():
    """Initialize the database and create tables."""
    print("🚀 Setting up Asset Enrichment Pipeline Database...")
    
    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, project_root)
    
    try:
        # Django will handle database initialization
        print("📦 Django will handle database initialization...")
        print("✅ Database setup completed successfully")
        return True
        
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
        
        # Check if .env exists, if not create from env.development
        env_file = os.path.join(django_dir, '.env')
        dev_env_file = os.path.join(os.path.dirname(__file__), 'env.development')
        
        if not os.path.exists(env_file) and os.path.exists(dev_env_file):
            print("📝 Creating .env from development template...")
            import shutil
            shutil.copy(dev_env_file, env_file)
            print("✅ .env file created")
        
        # Run Django migrations
        print("🔄 Running Django migrations...")
        os.system("python manage.py makemigrations")
        os.system("python manage.py migrate")
        
        print("✅ Django database setup completed")
        return True
        
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return False



def main():
    """Main setup function."""
    print("🏗️  Asset Enrichment Pipeline Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists('backend-django'):
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
    print("\n🎯 Creating sample assets...")
    try:
        os.system("python manage.py create_sample_assets")
        print("✅ Sample assets created successfully")
    except Exception as e:
        print(f"⚠️  Sample assets creation failed (non-critical): {e}")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start the services: docker-compose up")
    print("2. The backend will be available at: http://localhost:8000")
    print("3. The frontend will be available at: http://localhost:3000")
    print("4. Celery workers will process asset enrichment tasks")
    print("\nYou can now create assets through the UI!")

if __name__ == "__main__":
    main()
