#!/bin/bash
#
# Stop the observability server
#

set -e

DATA_DIR="$HOME/.claude-observability"
PID_FILE="$DATA_DIR/server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "✓ Observability server is not running"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! kill -0 "$PID" 2>/dev/null; then
    echo "✓ Server process not found (stale PID file removed)"
    rm -f "$PID_FILE"
    exit 0
fi

# Gracefully stop the server
kill "$PID" 2>/dev/null

# Wait for shutdown
for i in {1..10}; do
    if ! kill -0 "$PID" 2>/dev/null; then
        rm -f "$PID_FILE"
        echo "✓ Observability server stopped"
        exit 0
    fi
    sleep 0.3
done

# Force kill if still running
kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "✓ Observability server forcefully stopped"
