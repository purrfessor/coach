#!/bin/bash
#
# Ensure the observability server is running (for auto-start on SessionStart)
#
# This script is designed to be called silently from hooks.
# It checks if the server is running and starts it if not.
#

DATA_DIR="$HOME/.claude-observability"
PID_FILE="$DATA_DIR/server.pid"
PORT="${OBSERVABILITY_PORT:-4000}"

# Quick health check first (fastest path)
if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
    exit 0
fi

# Check PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        # Process exists but not responding, wait a bit
        sleep 1
        if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
            exit 0
        fi
    fi
fi

# Server not running, start it
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/start-server.sh" >/dev/null 2>&1
