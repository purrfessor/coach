# Multi-Agent Observability Plugin

Real-time monitoring dashboard for Claude Code agents across all projects.

## Features

- **Zero-config observability** - Install once, works with all Claude Code sessions
- **Auto-detected source apps** - Projects identified from git remotes or directory names
- **Real-time event streaming** - WebSocket-based live updates to the dashboard
- **Security validation** - Blocks dangerous rm commands and sensitive file access
- **Centralized data storage** - All events stored in `~/.claude-observability/events.db`

## Installation

```bash
# From Claude Code
/plugin install path/to/multi-agent-observability
```

## Usage

### Starting the Server

Use the slash command to start the observability server:

```
/observability-start
```

Or manually:

```bash
bash ~/.claude/plugins/multi-agent-observability/scripts/start-server.sh
```

### Viewing Status

```
/observability-status
```

### Stopping the Server

```
/observability-stop
```

## Configuration

### Environment Variables

- `OBSERVABILITY_PORT` - Server port (default: 4000)
- `OBSERVABILITY_SERVER_URL` - Custom server URL
- `OBSERVABILITY_AUTO_START` - Set to "true" to auto-start server on session start
- `OBSERVABILITY_DEBUG` - Enable debug logging

## Architecture

```
Claude Code Sessions
        │
        ▼
Python Hook Scripts (validation + event capture)
        │
        ▼
Bun HTTP/WebSocket Server (port 4000)
        │
        ▼
SQLite Database (~/.claude-observability/events.db)
        │
        ▼
WebSocket Clients (dashboard)
```

## Hook Events Captured

| Event | Description |
|-------|-------------|
| SessionStart | Session begins |
| PreToolUse | Before tool execution (with validation) |
| PostToolUse | After tool completes |
| Stop | Agent finishes responding |
| SubagentStop | Subagent task completes |
| UserPromptSubmit | User submits prompt |
| Notification | User interaction events |

## API Endpoints

- `GET /health` - Health check
- `POST /events` - Submit an event
- `GET /events/recent?limit=N` - Get recent events
- `GET /events/filter-options` - Get filter dropdown options
- `GET /events/count` - Get total event count
- `DELETE /events` - Clear all events
- `WS /stream` - WebSocket for real-time events

## Running Tests

```bash
cd plugins/multi-agent-observability
bash tests/run_tests.sh
```

## Requirements

- Python 3.10+
- Bun (for the server)
- Claude Code with plugin support
