#!/bin/bash
#
# Tests for lifecycle bash scripts
#
# These tests verify the behavior of start-server.sh, stop-server.sh,
# check-status.sh, and ensure-server.sh
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_DIR="$(dirname "$SCRIPT_DIR")"
SCRIPTS_DIR="$PLUGIN_DIR/scripts"

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Test helper functions
pass() {
    ((TESTS_PASSED++))
    echo -e "${GREEN}✓${NC} $1"
}

fail() {
    ((TESTS_FAILED++))
    echo -e "${RED}✗${NC} $1"
}

test_case() {
    ((TESTS_RUN++))
    echo "Running: $1"
}

# Cleanup any existing server before tests
cleanup() {
    DATA_DIR="$HOME/.claude-observability"
    PID_FILE="$DATA_DIR/server.pid"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null || true
        rm -f "$PID_FILE"
    fi
}

# ============================================
# Test: Scripts exist and are executable
# ============================================
test_case "Scripts exist and are executable"

if [ -x "$SCRIPTS_DIR/start-server.sh" ]; then
    pass "start-server.sh is executable"
else
    fail "start-server.sh is not executable"
fi

if [ -x "$SCRIPTS_DIR/stop-server.sh" ]; then
    pass "stop-server.sh is executable"
else
    fail "stop-server.sh is not executable"
fi

if [ -x "$SCRIPTS_DIR/check-status.sh" ]; then
    pass "check-status.sh is executable"
else
    fail "check-status.sh is not executable"
fi

if [ -x "$SCRIPTS_DIR/ensure-server.sh" ]; then
    pass "ensure-server.sh is executable"
else
    fail "ensure-server.sh is not executable"
fi

# ============================================
# Test: stop-server.sh handles no running server
# ============================================
test_case "stop-server.sh handles no running server gracefully"

cleanup
OUTPUT=$("$SCRIPTS_DIR/stop-server.sh" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    pass "stop-server.sh exits 0 when no server running"
else
    fail "stop-server.sh should exit 0 when no server running (got $EXIT_CODE)"
fi

if echo "$OUTPUT" | grep -q "not running"; then
    pass "stop-server.sh reports server not running"
else
    fail "stop-server.sh should report server not running"
fi

# ============================================
# Test: check-status.sh works without server
# ============================================
test_case "check-status.sh works without server running"

cleanup
OUTPUT=$("$SCRIPTS_DIR/check-status.sh" 2>&1)
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    pass "check-status.sh exits 0"
else
    fail "check-status.sh should exit 0 (got $EXIT_CODE)"
fi

if echo "$OUTPUT" | grep -qi "status"; then
    pass "check-status.sh shows status information"
else
    fail "check-status.sh should show status information"
fi

if echo "$OUTPUT" | grep -qi "not running\|Not responding"; then
    pass "check-status.sh indicates server not running"
else
    fail "check-status.sh should indicate server not running"
fi

# ============================================
# Test: start-server.sh requires bun
# ============================================
test_case "start-server.sh checks for bun"

# This test just verifies the script has bun checking logic
if grep -q "command -v bun" "$SCRIPTS_DIR/start-server.sh"; then
    pass "start-server.sh checks for bun installation"
else
    fail "start-server.sh should check for bun installation"
fi

# ============================================
# Test: Scripts use correct data directory
# ============================================
test_case "Scripts use ~/.claude-observability data directory"

if grep -q '\.claude-observability' "$SCRIPTS_DIR/start-server.sh"; then
    pass "start-server.sh uses correct data directory"
else
    fail "start-server.sh should use ~/.claude-observability"
fi

if grep -q '\.claude-observability' "$SCRIPTS_DIR/stop-server.sh"; then
    pass "stop-server.sh uses correct data directory"
else
    fail "stop-server.sh should use ~/.claude-observability"
fi

if grep -q '\.claude-observability' "$SCRIPTS_DIR/check-status.sh"; then
    pass "check-status.sh uses correct data directory"
else
    fail "check-status.sh should use ~/.claude-observability"
fi

# ============================================
# Test: ensure-server.sh has health check
# ============================================
test_case "ensure-server.sh performs health check first"

if grep -q "health" "$SCRIPTS_DIR/ensure-server.sh"; then
    pass "ensure-server.sh checks health endpoint"
else
    fail "ensure-server.sh should check health endpoint"
fi

# ============================================
# Test: Default port is 4000
# ============================================
test_case "Scripts default to port 4000"

if grep -q "4000" "$SCRIPTS_DIR/start-server.sh"; then
    pass "start-server.sh defaults to port 4000"
else
    fail "start-server.sh should default to port 4000"
fi

if grep -q "4000" "$SCRIPTS_DIR/check-status.sh"; then
    pass "check-status.sh defaults to port 4000"
else
    fail "check-status.sh should default to port 4000"
fi

# ============================================
# Summary
# ============================================
echo ""
echo "========================================"
echo "Test Summary"
echo "========================================"
echo "Tests run: $TESTS_RUN"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed.${NC}"
    exit 1
fi
