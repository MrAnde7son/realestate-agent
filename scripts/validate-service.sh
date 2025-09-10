#!/bin/bash

# Service-specific validation script
# Usage: ./scripts/validate-service.sh <service-name>
# Example: ./scripts/validate-service.sh yad2

if [ $# -eq 0 ]; then
    echo "Usage: $0 <service-name>"
    echo "Available services: yad2, gov, mavat, rami, gis, orchestration, db, utils, backend-django"
    exit 1
fi

SERVICE_NAME="$1"
SERVICE_DIR="$SERVICE_NAME"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "🔍 Validating service: $SERVICE_NAME"

if [ ! -d "$SERVICE_DIR" ]; then
    print_error "Service directory '$SERVICE_DIR' not found"
    exit 1
fi

overall_success=true

# Check if it's a Python service
if [ -f "$SERVICE_DIR/__init__.py" ] || [ -f "$SERVICE_DIR/requirements.txt" ]; then
    print_info "Python service detected"
    
    # Check requirements.txt
    if [ -f "$SERVICE_DIR/requirements.txt" ]; then
        print_status "requirements.txt found"
        
        # Check if requirements.txt is empty
        if [ ! -s "$SERVICE_DIR/requirements.txt" ]; then
            print_warning "requirements.txt is empty"
        fi
    else
        print_warning "requirements.txt not found"
    fi
    
    # Check for __init__.py
    if [ -f "$SERVICE_DIR/__init__.py" ]; then
        print_status "__init__.py found"
    else
        print_warning "__init__.py not found"
    fi
    
    # Check for test files
    test_files=$(find "$SERVICE_DIR" -name "test_*.py" -o -name "*_test.py" | wc -l)
    if [ "$test_files" -gt 0 ]; then
        print_status "Found $test_files test files"
    else
        print_warning "No test files found"
    fi
    
    # Check for Python syntax errors
    print_info "Checking Python syntax..."
    python_files=$(find "$SERVICE_DIR" -name "*.py" -not -path "*/__pycache__/*")
    syntax_errors=0
    
    for file in $python_files; do
        if ! python -m py_compile "$file" 2>/dev/null; then
            print_error "Syntax error in $file"
            syntax_errors=$((syntax_errors + 1))
        fi
    done
    
    if [ $syntax_errors -eq 0 ]; then
        print_status "No syntax errors found"
    else
        print_error "Found $syntax_errors syntax errors"
        overall_success=false
    fi
    
    # Run specific service tests if they exist
    if [ -d "tests/$SERVICE_NAME" ]; then
        print_info "Running service-specific tests..."
        if pytest "tests/$SERVICE_NAME/" -v; then
            print_status "Service tests passed"
        else
            print_error "Service tests failed"
            overall_success=false
        fi
    else
        print_warning "No service-specific tests found in tests/$SERVICE_NAME/"
    fi

# Check if it's the Django backend
elif [ "$SERVICE_NAME" = "backend-django" ]; then
    print_info "Django backend detected"
    
    cd "$SERVICE_DIR"
    
    # Check Django settings
    if python manage.py check; then
        print_status "Django check passed"
    else
        print_error "Django check failed"
        overall_success=false
    fi
    
    # Check for pending migrations
    pending_migrations=$(python manage.py showmigrations --plan | grep -c '\[ \]' || true)
    if [ "$pending_migrations" -eq 0 ]; then
        print_status "No pending migrations"
    else
        print_warning "Found $pending_migrations pending migrations"
    fi
    
    # Run Django tests
    if python manage.py test; then
        print_status "Django tests passed"
    else
        print_error "Django tests failed"
        overall_success=false
    fi
    
    cd ..

# Check if it's the frontend
elif [ "$SERVICE_NAME" = "realestate-broker-ui" ]; then
    print_info "Frontend service detected"
    
    cd "$SERVICE_DIR"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        print_warning "node_modules not found, installing dependencies..."
        npm install
    fi
    
    # TypeScript check
    if npm run type-check; then
        print_status "TypeScript check passed"
    else
        print_error "TypeScript check failed"
        overall_success=false
    fi
    
    # Linting
    if npm run lint; then
        print_status "Linting passed"
    else
        print_error "Linting failed"
        overall_success=false
    fi
    
    # Unit tests
    if npm run test; then
        print_status "Unit tests passed"
    else
        print_error "Unit tests failed"
        overall_success=false
    fi
    
    cd ..

else
    print_warning "Unknown service type"
fi

# Check for README
if [ -f "$SERVICE_DIR/README.md" ]; then
    print_status "README.md found"
else
    print_warning "README.md not found"
fi

# Check for configuration files
config_files=("config.py" "settings.py" "config.json" "config.yaml" "config.yml")
for config in "${config_files[@]}"; do
    if [ -f "$SERVICE_DIR/$config" ]; then
        print_status "Configuration file $config found"
    fi
done

echo ""
if [ "$overall_success" = true ]; then
    print_status "Service '$SERVICE_NAME' validation passed! 🎉"
    exit 0
else
    print_error "Service '$SERVICE_NAME' validation failed! ❌"
    exit 1
fi
