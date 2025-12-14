#!/bin/bash
#
# Start the observability server
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(dirname "$SCRIPT_DIR")"
SERVER_DIR="$PLUGIN_ROOT/server"
DATA_DIR="$HOME/.claude-observability"
PID_FILE="$DATA_DIR/server.pid"
LOG_FILE="$DATA_DIR/server.log"
PORT="${OBSERVABILITY_PORT:-4000}"

# Ensure data directory exists
mkdir -p "$DATA_DIR"

# Check if server is already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "✓ Observability server already running (PID: $PID)"
        echo "  URL: http://localhost:$PORT"
        exit 0
    else
        # Stale PID file, remove it
        rm -f "$PID_FILE"
    fi
fi

# Check if port is in use
if lsof -i ":$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "⚠ Port $PORT is already in use"
    echo "  Another process may be using this port"
    exit 1
fi

# Check for bun
if ! command -v bun &>/dev/null; then
    echo "✗ Bun is not installed"
    echo "  Install with: curl -fsSL https://bun.sh/install | bash"
    exit 1
fi

# Start server in background
cd "$SERVER_DIR"
nohup bun run index.ts > "$LOG_FILE" 2>&1 &
SERVER_PID=$!

# Save PID
echo "$SERVER_PID" > "$PID_FILE"

# Wait for server to be ready
echo "Starting observability server..."
for i in {1..10}; do
    if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
        echo "✓ Observability server started (PID: $SERVER_PID)"
        echo "  URL: http://localhost:$PORT"
        echo "  WebSocket: ws://localhost:$PORT/stream"
        echo "  Logs: $LOG_FILE"
        exit 0
    fi
    sleep 0.5
done

# Server failed to start
echo "✗ Server failed to start"
echo "  Check logs at: $LOG_FILE"
kill "$SERVER_PID" 2>/dev/null || true
rm -f "$PID_FILE"
exit 1
