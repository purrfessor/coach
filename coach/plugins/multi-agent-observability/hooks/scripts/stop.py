#!/usr/bin/env python3
"""
Stop hook - called when Claude finishes responding.

This script sends a stop event to the observability server,
optionally including the chat transcript.
"""

import argparse
import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.source_app import get_source_app
from scripts.utils.server import send_event, read_stdin_json, check_server_health


def read_chat_transcript(transcript_path: str) -> list[dict]:
    """Read chat transcript from JSONL file."""
    chat = []
    if transcript_path and os.path.exists(transcript_path):
        try:
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
    return chat


def main():
    parser = argparse.ArgumentParser(description='Send stop event to observability server')
    parser.add_argument('--add-chat', action='store_true',
                        help='Include chat transcript in event')

    args = parser.parse_args()

    # Read hook input from stdin
    hook_data = read_stdin_json()

    if not hook_data:
        sys.exit(0)

    session_id = hook_data.get('session_id', 'unknown')
    source_app = get_source_app()

    # Check if server is available
    if not check_server_health():
        sys.exit(0)

    # Build payload
    payload = {
        "reason": hook_data.get('reason', ''),
        "stop_type": hook_data.get('stop_type', 'end_turn')
    }

    # Read chat transcript if requested
    chat = None
    if args.add_chat:
        transcript_path = hook_data.get('transcript_path')
        chat = read_chat_transcript(transcript_path) if transcript_path else None

    try:
        send_event(
            source_app=source_app,
            session_id=session_id,
            hook_event_type='Stop',
            payload=payload,
            chat=chat
        )
    except (ConnectionError, ValueError):
        pass

    sys.exit(0)


if __name__ == '__main__':
    main()
