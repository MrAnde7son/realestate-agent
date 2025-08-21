#!/bin/bash

# Install Core Django Backend Only
# ================================

echo "🚀 Installing Core Django Backend..."

cd backend-django
pip install -r requirements.txt

echo "✅ Core backend installed successfully!"
echo "📁 To run: cd backend-django && python3 manage.py runserver"
