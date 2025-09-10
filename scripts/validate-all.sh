#!/bin/bash

# Comprehensive validation script for the entire monorepo
# Runs all validation checks for frontend, backend, and data services

set -e  # Exit on any error

echo "🚀 Starting comprehensive monorepo validation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to run command and check result
run_check() {
    local check_name="$1"
    local command="$2"
    
    echo "🔍 Running: $check_name"
    if eval "$command"; then
        print_status "$check_name passed"
        return 0
    else
        print_error "$check_name failed"
        return 1
    fi
}

# Track overall success
overall_success=true

echo ""
echo "=== FRONTEND VALIDATION ==="

# Frontend checks
if [ -d "realestate-broker-ui" ]; then
    cd realestate-broker-ui
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "node_modules not found, installing dependencies..."
        npm install
    fi
    
    # Component validation
    if ! run_check "Component validation" "cd .. && node scripts/validate-components.js"; then
        overall_success=false
    fi
    
    # TypeScript check
    if ! run_check "TypeScript compilation" "npm run type-check"; then
        overall_success=false
    fi
    
    # Linting
    if ! run_check "ESLint" "npm run lint"; then
        overall_success=false
    fi
    
    # Unit tests
    if ! run_check "Unit tests" "npm run test"; then
        overall_success=false
    fi
    
    cd ..
else
    print_warning "Frontend directory not found, skipping frontend checks"
fi

echo ""
echo "=== BACKEND VALIDATION ==="

# Backend checks
if [ -d "backend-django" ]; then
    cd backend-django
    
    # Check if virtual environment is activated
    if [ -z "$VIRTUAL_ENV" ]; then
        print_warning "Virtual environment not activated, using system Python"
    fi
    
    # Django tests
    if ! run_check "Django tests" "python manage.py test"; then
        overall_success=false
    fi
    
    # Check migrations
    if ! run_check "Migration check" "python manage.py check"; then
        overall_success=false
    fi
    
    # Check for pending migrations
    if ! run_check "Pending migrations check" "python manage.py showmigrations --plan | grep -q '\\[ \\]' && echo 'Pending migrations found' || echo 'No pending migrations'"; then
        print_warning "There are pending migrations"
    fi
    
    cd ..
else
    print_warning "Backend directory not found, skipping backend checks"
fi

echo ""
echo "=== PYTHON SERVICES VALIDATION ==="

# Python services validation
if ! run_check "Python services validation" "python scripts/validate-python.py"; then
    overall_success=false
fi

echo ""
echo "=== DATA SERVICES VALIDATION ==="

# Check each data service
services=("yad2" "gov" "mavat" "rami" "gis" "orchestration" "db" "utils")

for service in "${services[@]}"; do
    if [ -d "$service" ]; then
        echo "🔍 Checking $service service..."
        
        # Check if requirements.txt exists
        if [ -f "$service/requirements.txt" ]; then
            print_status "$service has requirements.txt"
        else
            print_warning "$service missing requirements.txt"
        fi
        
        # Check for __init__.py files
        if [ -f "$service/__init__.py" ]; then
            print_status "$service has __init__.py"
        else
            print_warning "$service missing __init__.py"
        fi
        
        # Check for test files
        if find "$service" -name "test_*.py" -o -name "*_test.py" | grep -q .; then
            print_status "$service has test files"
        else
            print_warning "$service has no test files"
        fi
    else
        print_warning "$service directory not found"
    fi
done

echo ""
echo "=== INTEGRATION TESTS ==="

# Run integration tests if available
if [ -d "tests" ]; then
    if ! run_check "Integration tests" "pytest tests/ -v"; then
        overall_success=false
    fi
else
    print_warning "No tests directory found"
fi

echo ""
echo "=== DOCKER VALIDATION ==="

# Check Docker files
if [ -f "docker-compose.yml" ]; then
    print_status "docker-compose.yml found"
    
    # Check if Docker is running
    if docker info >/dev/null 2>&1; then
        print_status "Docker is running"
        
        # Validate docker-compose file
        if ! run_check "Docker Compose validation" "docker-compose config"; then
            overall_success=false
        fi
    else
        print_warning "Docker is not running"
    fi
else
    print_warning "docker-compose.yml not found"
fi

echo ""
echo "=== ENVIRONMENT VALIDATION ==="

# Check environment files
if [ -f "env.example" ]; then
    print_status "env.example found"
else
    print_warning "env.example not found"
fi

if [ -f "env.development" ]; then
    print_status "env.development found"
else
    print_warning "env.development not found"
fi

echo ""
echo "=== DOCUMENTATION VALIDATION ==="

# Check documentation files
docs=("README.md" "DEVELOPMENT_CHECKLIST.md" "PRD.md")

for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        print_status "$doc found"
    else
        print_warning "$doc not found"
    fi
done

echo ""
echo "=== FINAL RESULTS ==="

if [ "$overall_success" = true ]; then
    print_status "All validation checks passed! 🎉"
    echo ""
    echo "The monorepo is ready for development and deployment."
    exit 0
else
    print_error "Some validation checks failed! ❌"
    echo ""
    echo "Please fix the issues above before proceeding."
    echo "Refer to DEVELOPMENT_CHECKLIST.md for guidance."
    exit 1
fi
