#!/bin/bash
#
# Test Runner Script
# Runs automated tests with coverage reporting
#

set -e

echo "=============================================="
echo "🧪 Running Automated Tests"
echo "=============================================="
echo

# Ensure we're in the python_backend directory
cd "$(dirname "$0")/python_backend"

# Check if pytest is installed
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "❌ pytest not installed"
    echo "   Installing test dependencies..."
    pip3 install pytest pytest-asyncio pytest-cov
fi

echo "📦 Test dependencies OK"
echo

# Run tests with coverage
echo "🔄 Running tests..."
echo

python3 -m pytest tests/ \
    -v \
    --tb=short \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=html:../coverage_html \
    "$@"

RESULT=$?

echo
if [ $RESULT -eq 0 ]; then
    echo "=============================================="
    echo "✅ All tests passed!"
    echo "=============================================="
    echo
    echo "📊 Coverage report: ../coverage_html/index.html"
else
    echo "=============================================="
    echo "❌ Some tests failed"
    echo "=============================================="
fi

exit $RESULT

