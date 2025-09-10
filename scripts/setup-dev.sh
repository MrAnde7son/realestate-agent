#!/bin/bash

# Development setup script for the monorepo
# Sets up the development environment with all dependencies

set -e  # Exit on any error

echo "🚀 Setting up development environment for Real Estate Agent monorepo..."

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

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ] || [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    print_status "Python $python_version is compatible"
else
    print_error "Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

# Check Node.js version
print_info "Checking Node.js version..."
if command -v node >/dev/null 2>&1; then
    node_version=$(node --version | cut -d'v' -f2)
    print_status "Node.js $node_version found"
else
    print_error "Node.js is required but not installed"
    exit 1
fi

# Check npm/pnpm
print_info "Checking package manager..."
if command -v pnpm >/dev/null 2>&1; then
    print_status "pnpm found"
    PACKAGE_MANAGER="pnpm"
elif command -v npm >/dev/null 2>&1; then
    print_status "npm found"
    PACKAGE_MANAGER="npm"
else
    print_error "npm or pnpm is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
print_info "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_status "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip
pip install -e .

# Install development dependencies
print_info "Installing development dependencies..."
pip install pytest pytest-cov black flake8

# Install service-specific dependencies
services=("backend-django" "yad2" "gov" "mavat" "rami" "gis" "orchestration" "db" "utils")

for service in "${services[@]}"; do
    if [ -d "$service" ] && [ -f "$service/requirements.txt" ]; then
        print_info "Installing dependencies for $service..."
        pip install -r "$service/requirements.txt"
    fi
done

# Setup frontend
print_info "Setting up frontend..."
cd realestate-broker-ui

if [ "$PACKAGE_MANAGER" = "pnpm" ]; then
    pnpm install
else
    npm install
fi

cd ..

# Setup database
print_info "Setting up database..."
cd backend-django

# Create database if it doesn't exist
if [ ! -f "db.sqlite3" ]; then
    print_info "Creating database..."
    python manage.py migrate
    print_status "Database created"
else
    print_status "Database already exists"
fi

# Initialize plan types
print_info "Initializing plan types..."
python manage.py init_plans

cd ..

# Setup Docker (optional)
print_info "Checking Docker setup..."
if command -v docker >/dev/null 2>&1 && command -v docker-compose >/dev/null 2>&1; then
    print_status "Docker and Docker Compose found"
    
    # Validate docker-compose file
    if docker-compose config >/dev/null 2>&1; then
        print_status "Docker Compose configuration is valid"
    else
        print_warning "Docker Compose configuration has issues"
    fi
else
    print_warning "Docker not found - some features may not work"
fi

# Run initial validation
print_info "Running initial validation..."
if ./scripts/pre-commit.sh; then
    print_status "Initial validation passed"
else
    print_warning "Initial validation had some issues - check the output above"
fi

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    print_info "Creating .env file from template..."
    if [ -f "env.example" ]; then
        cp env.example .env
        print_status ".env file created from template"
        print_warning "Please update .env with your actual configuration"
    else
        print_warning "No env.example found - you may need to create .env manually"
    fi
fi

echo ""
print_status "Development environment setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run './scripts/validate-all.sh' to verify everything is working"
echo "3. Start development with './run_all.sh' or individual services"
echo ""
echo "Useful commands:"
echo "  ./scripts/validate-all.sh          # Run all validation checks"
echo "  ./scripts/validate-service.sh <service>  # Validate specific service"
echo "  ./scripts/pre-commit.sh            # Run pre-commit checks"
echo "  ./run_all.sh                       # Start all services"
echo "  ./health-check.sh                  # Check service health"
echo ""
echo "Happy coding! 🚀"
