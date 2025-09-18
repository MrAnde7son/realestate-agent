#!/bin/bash
# -*- coding: utf-8 -*-
"""
Script to run Nadlan.gov.il E2E tests

This script runs the integration tests specifically for Nadlan.gov.il
functionality, including transaction data collection and comparison.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 Running Nadlan.gov.il E2E Tests${NC}"
echo "=================================="
echo "Project Root: $PROJECT_ROOT"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  No virtual environment found, using system Python${NC}"
fi

# Install dependencies if needed
echo -e "${YELLOW}📦 Installing Nadlan E2E test dependencies...${NC}"
pip install -q -r tests/e2e/requirements_nadlan.txt

# Set environment variables
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
export HEADLESS=true

echo -e "${BLUE}🧪 Running Nadlan Integration Tests...${NC}"
echo ""

# Run the specific Nadlan integration tests
python -m pytest tests/e2e/test_nadlan_integration.py \
    -v \
    --tb=short \
    --durations=10 \
    -m "nadlan and integration" \
    --timeout=300 \
    --maxfail=3

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Nadlan Integration Tests Passed!${NC}"
else
    echo -e "${RED}❌ Nadlan Integration Tests Failed!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🧪 Running Nadlan Collector Tests...${NC}"
echo ""

# Run the collector integration tests with Nadlan focus
python -m pytest tests/e2e/test_collectors_integration.py \
    -v \
    --tb=short \
    --durations=10 \
    -m "nadlan and integration" \
    --timeout=300 \
    --maxfail=3

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Nadlan Collector Tests Passed!${NC}"
else
    echo -e "${RED}❌ Nadlan Collector Tests Failed!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🧪 Running Pipeline Tests with Nadlan...${NC}"
echo ""

# Run the pipeline tests with Nadlan focus
python -m pytest tests/e2e/test_pipeline_optimized_e2e.py \
    -v \
    --tb=short \
    --durations=10 \
    -k "nadlan or transaction" \
    --timeout=300 \
    --maxfail=3

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Pipeline Tests with Nadlan Passed!${NC}"
else
    echo -e "${RED}❌ Pipeline Tests with Nadlan Failed!${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}🧪 Running Transaction Comparison Tests...${NC}"
echo ""

# Run the transaction comparison tests
python -m pytest tests/e2e/test_transaction_comparison.py \
    -v \
    --tb=short \
    --durations=10 \
    -m "nadlan and integration" \
    --timeout=300 \
    --maxfail=3

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Transaction Comparison Tests Passed!${NC}"
else
    echo -e "${RED}❌ Transaction Comparison Tests Failed!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 All Nadlan E2E Tests Completed Successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Test Summary:${NC}"
echo "  ✅ Nadlan Integration Tests"
echo "  ✅ Nadlan Collector Tests" 
echo "  ✅ Pipeline Tests with Nadlan"
echo "  ✅ Transaction Comparison Tests"
echo ""
echo -e "${YELLOW}💡 Next Steps:${NC}"
echo "  1. Check the test results above for any warnings"
echo "  2. Review transaction data quality and structure"
echo "  3. Verify price analysis functionality"
echo "  4. Test with different addresses if needed"
