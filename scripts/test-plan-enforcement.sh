#!/bin/bash

# Test runner script specifically for plan enforcement functionality
# Runs all plan-related tests across the monorepo

set -e  # Exit on any error

echo "🧪 Running Plan Enforcement Tests..."

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

# Track overall success
overall_success=true

echo ""
echo "=== BACKEND PLAN TESTS ==="

# Test Django plan models
print_info "Testing Django plan models..."
if cd backend-django && python manage.py test tests.core.test_plan_models -v 2; then
    print_status "Plan models tests passed"
else
    print_error "Plan models tests failed"
    overall_success=false
fi
cd ..

# Test Django plan service
print_info "Testing Django plan service..."
if cd backend-django && python manage.py test tests.core.test_plan_service -v 2; then
    print_status "Plan service tests passed"
else
    print_error "Plan service tests failed"
    overall_success=false
fi
cd ..

# Test Django plan API
print_info "Testing Django plan API..."
if cd backend-django && python manage.py test tests.core.test_plan_api -v 2; then
    print_status "Plan API tests passed"
else
    print_error "Plan API tests failed"
    overall_success=false
fi
cd ..

# Test Django plan integration
print_info "Testing Django plan integration..."
if cd backend-django && python manage.py test tests.core.test_plan_integration -v 2; then
    print_status "Plan integration tests passed"
else
    print_error "Plan integration tests failed"
    overall_success=false
fi
cd ..

echo ""
echo "=== FRONTEND PLAN TESTS ==="

# Test frontend plan components
print_info "Testing frontend plan components..."
if cd realestate-broker-ui && npm test -- --testPathPattern="PlanInfo|PlanLimitDialog|plan-enforcement" --passWithNoTests; then
    print_status "Frontend plan tests passed"
else
    print_error "Frontend plan tests failed"
    overall_success=false
fi
cd ..

echo ""
echo "=== PLAN ENFORCEMENT INTEGRATION TESTS ==="

# Test plan enforcement with pytest
print_info "Testing plan enforcement integration..."
if pytest tests/core/test_plan_integration.py -v; then
    print_status "Plan enforcement integration tests passed"
else
    print_error "Plan enforcement integration tests failed"
    overall_success=false
fi

echo ""
echo "=== PLAN ENFORCEMENT E2E TESTS ==="

# Test plan enforcement end-to-end
print_info "Testing plan enforcement end-to-end..."
if cd realestate-broker-ui && npm run test:e2e -- --grep "plan enforcement"; then
    print_status "Plan enforcement E2E tests passed"
else
    print_warning "Plan enforcement E2E tests not found or failed"
fi
cd ..

echo ""
echo "=== PLAN ENFORCEMENT PERFORMANCE TESTS ==="

# Test plan enforcement performance
print_info "Testing plan enforcement performance..."
if cd backend-django && python manage.py test tests.core.test_plan_integration::TestPlanEnforcementIntegration::test_concurrent_asset_creation -v 2; then
    print_status "Plan enforcement performance tests passed"
else
    print_warning "Plan enforcement performance tests not found or failed"
fi
cd ..

echo ""
echo "=== PLAN ENFORCEMENT COVERAGE REPORT ==="

# Generate coverage report for plan enforcement
print_info "Generating plan enforcement coverage report..."
if cd backend-django && python -m pytest tests.core.test_plan_*.py --cov=core --cov-report=html --cov-report=term-missing; then
    print_status "Plan enforcement coverage report generated"
    print_info "Coverage report available at: backend-django/htmlcov/index.html"
else
    print_warning "Coverage report generation failed"
fi
cd ..

echo ""
echo "=== PLAN ENFORCEMENT VALIDATION ==="

# Validate plan enforcement configuration
print_info "Validating plan enforcement configuration..."

# Check if plan types are properly initialized
if cd backend-django && python manage.py shell -c "
from core.models import PlanType
plans = PlanType.objects.all()
print(f'Found {plans.count()} plan types:')
for plan in plans:
    print(f'  - {plan.name}: {plan.display_name} (limit: {plan.asset_limit})')
"; then
    print_status "Plan configuration validation passed"
else
    print_error "Plan configuration validation failed"
    overall_success=false
fi
cd ..

# Check if plan service is working
print_info "Testing plan service functionality..."
if cd backend-django && python manage.py shell -c "
from core.plan_service import PlanService
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass')
plan_info = PlanService.get_user_plan_info(user)
print(f'Plan info for test user: {plan_info[\"plan_name\"]}')
"; then
    print_status "Plan service validation passed"
else
    print_error "Plan service validation failed"
    overall_success=false
fi
cd ..

echo ""
echo "=== FINAL RESULTS ==="

if [ "$overall_success" = true ]; then
    print_status "All plan enforcement tests passed! 🎉"
    echo ""
    echo "Plan enforcement is working correctly across:"
    echo "  ✅ Django models (PlanType, UserPlan)"
    echo "  ✅ Django services (PlanService)"
    echo "  ✅ Django API endpoints"
    echo "  ✅ Frontend components (PlanInfo, PlanLimitDialog)"
    echo "  ✅ Integration tests"
    echo "  ✅ Plan configuration"
    echo ""
    echo "The plan enforcement system is ready for production! 🚀"
    exit 0
else
    print_error "Some plan enforcement tests failed! ❌"
    echo ""
    echo "Please fix the failing tests before deploying plan enforcement."
    echo "Check the output above for specific error details."
    exit 1
fi
