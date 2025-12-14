---
name: observability-start
description: Start the multi-agent observability server
---

Start the multi-agent observability server if it's not already running.

Execute the following command to start the server:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/start-server.sh
```

After starting, the server will be available at:
- HTTP API: http://localhost:4000
- WebSocket: ws://localhost:4000/stream

To view the dashboard, open http://localhost:4000 in your browser or use `/observability-dashboard`.
