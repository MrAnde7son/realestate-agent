#!/bin/bash

echo "🚀 Starting Real Estate Agent in Development Mode"
echo "=================================================="

# Check if we're in the right directory
if [ ! -d "backend-django" ]; then
    echo "❌ Please run this script from the project root directory"
    exit 1
fi

# Setup Django database
echo "📦 Setting up Django database..."
cd backend-django

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from development template..."
    cp ../env.development .env
    echo "✅ .env file created"
fi

# Run migrations
echo "🔄 Running Django migrations..."
python manage.py makemigrations
python manage.py migrate

# Create sample assets
echo "🎯 Creating sample assets..."
python manage.py create_sample_assets

# Start Django server
echo "🌐 Starting Django server..."
echo "Backend will be available at: http://localhost:8000"
echo "Press Ctrl+C to stop"
python manage.py runserver

cd ..
