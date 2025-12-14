#!/bin/bash
#
# Check the status of the observability server
#

DATA_DIR="$HOME/.claude-observability"
PID_FILE="$DATA_DIR/server.pid"
PORT="${OBSERVABILITY_PORT:-4000}"

echo "Observability Server Status"
echo "============================"
echo ""

# Check PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Status:    ✓ Running (PID: $PID)"
    else
        echo "Status:    ✗ Not running (stale PID file)"
    fi
else
    echo "Status:    ✗ Not running"
fi

# Check health endpoint
if curl -s "http://localhost:$PORT/health" >/dev/null 2>&1; then
    echo "Health:    ✓ Healthy"

    # Get event count
    COUNT=$(curl -s "http://localhost:$PORT/events/count" 2>/dev/null | grep -o '"count":[0-9]*' | cut -d: -f2)
    if [ -n "$COUNT" ]; then
        echo "Events:    $COUNT events stored"
    fi
else
    echo "Health:    ✗ Not responding"
fi

echo ""
echo "Configuration"
echo "-------------"
echo "Port:      $PORT"
echo "URL:       http://localhost:$PORT"
echo "WebSocket: ws://localhost:$PORT/stream"
echo "Data Dir:  $DATA_DIR"

if [ -f "$DATA_DIR/events.db" ]; then
    DB_SIZE=$(du -h "$DATA_DIR/events.db" 2>/dev/null | cut -f1)
    echo "DB Size:   $DB_SIZE"
fi
