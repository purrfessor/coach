#!/usr/bin/env python3
"""
Send hook events to the observability server.

This script reads hook data from stdin and sends it to the observability
server for real-time monitoring across all Claude Code agents.

Usage:
    echo '{"session_id": "abc123", ...}' | python send_event.py --event-type PreToolUse
"""

import argparse
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.source_app import get_source_app
from scripts.utils.server import send_event, read_stdin_json, check_server_health


def main():
    parser = argparse.ArgumentParser(description='Send hook event to observability server')
    parser.add_argument('--event-type', required=True,
                        help='Hook event type (PreToolUse, PostToolUse, Stop, etc.)')
    parser.add_argument('--source-app', default=None,
                        help='Override auto-detected source app name')
    parser.add_argument('--add-chat', action='store_true',
                        help='Include chat transcript in event')
    parser.add_argument('--summarize', action='store_true',
                        help='Generate AI summary (not implemented in plugin version)')

    args = parser.parse_args()

    # Read hook input from stdin
    hook_data = read_stdin_json()

    if not hook_data:
        # No input data, silently exit (server might not be running)
        sys.exit(0)

    # Get session ID from hook data
    session_id = hook_data.get('session_id', 'unknown')

    # Get source app (auto-detect or from argument)
    source_app = args.source_app if args.source_app else get_source_app()

    # Build payload from hook data
    payload = {}

    # Extract relevant fields based on event type
    if args.event_type in ('PreToolUse', 'PostToolUse'):
        payload['tool_name'] = hook_data.get('tool_name', 'unknown')
        payload['tool_input'] = hook_data.get('tool_input', {})
        if 'tool_result' in hook_data:
            payload['tool_result'] = hook_data.get('tool_result')

    elif args.event_type == 'UserPromptSubmit':
        payload['user_prompt'] = hook_data.get('user_prompt', '')

    elif args.event_type in ('Stop', 'SubagentStop'):
        payload['reason'] = hook_data.get('reason', '')
        payload['stop_type'] = hook_data.get('stop_type', '')

    elif args.event_type == 'Notification':
        payload['message'] = hook_data.get('message', '')
        payload['notification_type'] = hook_data.get('type', '')

    else:
        # For other events, include all hook data as payload
        payload = hook_data

    # Include chat transcript if requested
    chat = None
    if args.add_chat:
        transcript_path = hook_data.get('transcript_path')
        if transcript_path and os.path.exists(transcript_path):
            try:
                chat = []
                with open(transcript_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                chat.append(json.loads(line))
                            except json.JSONDecodeError:
                                pass
            except (IOError, OSError):
                pass

    # Check if server is running before sending
    if not check_server_health():
        # Server not running, silently exit
        # This is expected behavior - the plugin is passive when server is off
        sys.exit(0)

    try:
        result = send_event(
            source_app=source_app,
            session_id=session_id,
            hook_event_type=args.event_type,
            payload=payload,
            chat=chat
        )
        # Success - optionally print result for debugging
        if os.environ.get('OBSERVABILITY_DEBUG'):
            print(json.dumps(result), file=sys.stderr)

    except ConnectionError:
        # Server not reachable, silently continue
        pass
    except ValueError as e:
        # Server error, log but don't fail the hook
        print(f"Warning: Server error: {e}", file=sys.stderr)

    sys.exit(0)


if __name__ == '__main__':
    main()
