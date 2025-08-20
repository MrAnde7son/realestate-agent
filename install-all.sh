#!/bin/bash

# Install All Real Estate Agent Modules
# ====================================

echo "🏗️  Installing Real Estate Agent - Complete Edition..."

# Install core backend
echo "📦 Installing Core Backend..."
cd backend-django
pip install -r requirements.txt
cd ..

# Install government modules
echo "🏛️  Installing Government Data Modules..."
cd gov
pip install -r requirements.txt
cd ..

# Install GIS module
echo "🗺️  Installing GIS Module..."
cd gis
pip install -r requirements.txt
cd ..

# Install Yad2 module
echo "🏠 Installing Yad2 Real Estate Module..."
cd yad2
pip install -r requirements.txt
cd ..

# Install RAMI module
echo "📊 Installing RAMI Module..."
cd rami
pip install -r requirements.txt
cd ..

# Install global dependencies
echo "🌍 Installing Global Dependencies..."
pip install -r requirements.txt

echo "🎉 All modules installed successfully!"
echo "🚀 To run core backend: cd backend-django && python3 manage.py runserver"
echo "📚 Check individual module READMEs for specific usage instructions"
