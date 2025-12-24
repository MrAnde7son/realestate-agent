#!/bin/bash

# Cleanup script to remove runtime files from git tracking
# This script removes files that should not be in version control

set -e

echo "🧹 Cleaning up runtime files from git tracking..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f ".gitignore" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Remove dump.rdb files
if git ls-files --error-unmatch dump.rdb backend-django/dump.rdb >/dev/null 2>&1; then
    git rm --cached dump.rdb backend-django/dump.rdb 2>/dev/null || true
    print_status "Removed dump.rdb files from git tracking"
else
    print_warning "dump.rdb files not tracked in git"
fi

# Remove cookies.txt
if git ls-files --error-unmatch backend-django/cookies.txt >/dev/null 2>&1; then
    git rm --cached backend-django/cookies.txt 2>/dev/null || true
    print_status "Removed cookies.txt from git tracking"
else
    print_warning "cookies.txt not tracked in git"
fi

# Remove deal_cache directory
if git ls-files | grep -q "deal_cache"; then
    git rm -r --cached backend-django/deal_cache/ 2>/dev/null || true
    print_status "Removed deal_cache/ from git tracking"
else
    print_warning "deal_cache/ not tracked in git"
fi

# Remove tmp directory
if git ls-files | grep -q "tmp/"; then
    git rm -r --cached backend-django/tmp/ 2>/dev/null || true
    print_status "Removed tmp/ from git tracking"
else
    print_warning "tmp/ not tracked in git"
fi

# Verify .gitignore has the patterns
if grep -q "\.rdb" .gitignore && grep -q "deal_cache" .gitignore && grep -q "cookies\.txt" .gitignore; then
    print_status ".gitignore is properly configured"
else
    print_warning ".gitignore may need updates - check PROJECT_CLEANUP_ANALYSIS.md"
fi

echo ""
print_status "Cleanup complete! 🎉"
echo ""
echo "Note: Files are removed from git tracking but remain on disk."
echo "They will be ignored by git going forward thanks to .gitignore"
echo ""
echo "To commit these changes:"
echo "  git add .gitignore scripts/setup-dev.sh scripts/archive/ backend-django/*/.gitkeep"
echo "  git commit -m 'chore: cleanup runtime files and consolidate setup scripts'"

