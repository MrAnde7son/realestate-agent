#!/bin/bash

# Pre-commit hook to prevent regressions
# Runs essential checks before allowing commits

echo "🔍 Running pre-commit checks..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Track overall success
overall_success=true

# Check for missing UI components
echo "Checking UI component imports..."
if node scripts/validate-components.js; then
    print_status "Component validation passed"
else
    print_error "Component validation failed"
    overall_success=false
fi

# Check for TypeScript errors
echo "Checking TypeScript..."
cd realestate-broker-ui
if npm run type-check 2>/dev/null || npx tsc --noEmit; then
    print_status "TypeScript check passed"
else
    print_error "TypeScript errors found"
    overall_success=false
fi

# Check for linting errors
echo "Checking ESLint..."
if npm run lint 2>/dev/null || npx eslint . --ext .ts,.tsx; then
    print_status "ESLint check passed"
else
    print_error "Linting errors found"
    overall_success=false
fi

cd ..

# Check Python services
echo "Checking Python services..."
if python scripts/validate-python.py; then
    print_status "Python services validation passed"
else
    print_error "Python services validation failed"
    overall_success=false
fi

# Check Django migrations
echo "Checking Django migrations..."
cd backend-django
if python manage.py check; then
    print_status "Django check passed"
else
    print_error "Django check failed"
    overall_success=false
fi
cd ..

if [ "$overall_success" = true ]; then
    print_status "All pre-commit checks passed! 🎉"
    exit 0
else
    print_error "Some pre-commit checks failed! ❌"
    echo ""
    echo "Please fix the issues above before committing."
    echo "Run './scripts/validate-all.sh' for comprehensive validation."
    exit 1
fi
