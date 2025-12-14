#!/usr/bin/env python3
"""
Session start hook.

This script runs when a Claude Code session starts. It:
1. Ensures the observability server is running (optional auto-start)
2. Sends a session start event to the server
"""

import json
import os
import subprocess
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.source_app import get_source_app
from scripts.utils.server import send_event, read_stdin_json, check_server_health


def ensure_server_running() -> bool:
    """
    Ensure the observability server is running.

    Returns True if server is running (or was started), False otherwise.
    """
    # Check if server is already running
    if check_server_health():
        return True

    # Get plugin root from environment
    plugin_root = os.environ.get('CLAUDE_PLUGIN_ROOT', '')
    if not plugin_root:
        return False

    # Try to start the server
    ensure_script = os.path.join(plugin_root, 'scripts', 'ensure-server.sh')
    if os.path.exists(ensure_script):
        try:
            result = subprocess.run(
                ['bash', ensure_script],
                capture_output=True,
                timeout=10
            )
            # Give server time to start
            time.sleep(1)
            return check_server_health()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass

    return False


def main():
    # Read hook input from stdin
    hook_data = read_stdin_json()

    session_id = hook_data.get('session_id', 'unknown')
    source_app = get_source_app()

    # Optionally ensure server is running (controlled by env var)
    auto_start = os.environ.get('OBSERVABILITY_AUTO_START', 'false').lower() == 'true'
    if auto_start:
        ensure_server_running()

    # Check if server is available
    if not check_server_health():
        # Server not running, output a message but don't fail
        print(json.dumps({
            "systemMessage": "Observability server not running. Use /observability-start to enable monitoring."
        }))
        sys.exit(0)

    # Send session start event
    try:
        payload = {
            "cwd": hook_data.get('cwd', os.getcwd()),
            "permission_mode": hook_data.get('permission_mode', 'unknown')
        }

        send_event(
            source_app=source_app,
            session_id=session_id,
            hook_event_type='SessionStart',
            payload=payload
        )

        # Output success message
        print(json.dumps({
            "systemMessage": f"Observability: Session {session_id[:8]} started for {source_app}"
        }))

    except (ConnectionError, ValueError):
        # Server communication failed, continue silently
        pass

    sys.exit(0)


if __name__ == '__main__':
    main()
