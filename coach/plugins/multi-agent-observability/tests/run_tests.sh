#!/bin/bash
#
# Run all tests for the multi-agent-observability plugin
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "Multi-Agent Observability Plugin Tests"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

TOTAL_FAILED=0

# Run Python unit tests
echo -e "${YELLOW}Running Python unit tests...${NC}"
echo ""

cd "$PLUGIN_DIR"

# Set PYTHONPATH to include hooks directory
export PYTHONPATH="$PLUGIN_DIR/hooks:$PYTHONPATH"

# Run each test file
for test_file in tests/test_*.py; do
    if [ -f "$test_file" ]; then
        echo "Running $test_file..."
        if python3 -m pytest "$test_file" -v --tb=short 2>/dev/null || python3 "$test_file" 2>&1; then
            echo -e "${GREEN}✓${NC} $test_file passed"
        else
            echo -e "${RED}✗${NC} $test_file failed"
            ((TOTAL_FAILED++))
        fi
        echo ""
    fi
done

# Run bash script tests
echo -e "${YELLOW}Running bash script tests...${NC}"
echo ""

if bash "$SCRIPT_DIR/test_lifecycle_scripts.sh"; then
    echo -e "${GREEN}✓${NC} Bash script tests passed"
else
    echo -e "${RED}✗${NC} Bash script tests failed"
    ((TOTAL_FAILED++))
fi

echo ""
echo "========================================"
echo "Final Results"
echo "========================================"

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}All test suites passed!${NC}"
    exit 0
else
    echo -e "${RED}$TOTAL_FAILED test suite(s) failed${NC}"
    exit 1
fi
