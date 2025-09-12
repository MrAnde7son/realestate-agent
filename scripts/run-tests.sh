#!/bin/bash

# Test running script with different strategies
# Usage: ./scripts/run-tests.sh [strategy]
# Strategies: unit, integration, ci, all

set -e

STRATEGY=${1:-"unit"}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Running tests with strategy: $STRATEGY"
echo "Project root: $PROJECT_ROOT"

case $STRATEGY in
    "unit")
        echo "Running unit tests only (fast, no external dependencies)..."
        python3 -m pytest tests/ -v -m "not integration and not slow and not external_service" --tb=short
        ;;
    "integration")
        echo "Running integration tests (includes external services)..."
        python3 -m pytest tests/ -v -m "integration" --tb=short
        ;;
    "ci")
        echo "Running CI-optimized tests (skips slow/external service tests)..."
        python3 -m pytest -c pytest-ci.ini tests/
        ;;
    "all")
        echo "Running all tests..."
        python3 -m pytest tests/ -v --tb=short
        ;;
    "mavat")
        echo "Running Mavat tests only..."
        python3 -m pytest tests/ -v -m "mavat" --tb=short
        ;;
    "yad2")
        echo "Running Yad2 tests only..."
        python3 -m pytest tests/ -v -m "yad2" --tb=short
        ;;
    "nadlan")
        echo "Running Nadlan tests only..."
        python3 -m pytest tests/ -v -m "nadlan" --tb=short
        ;;
    "decisive")
        echo "Running Decisive tests only..."
        python3 -m pytest tests/ -v -m "decisive" --tb=short
        ;;
    *)
        echo "Unknown strategy: $STRATEGY"
        echo "Available strategies: unit, integration, ci, all, mavat, yad2, nadlan, decisive"
        exit 1
        ;;
esac

echo "Test run completed with strategy: $STRATEGY"
