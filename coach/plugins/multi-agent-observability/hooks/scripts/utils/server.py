"""Server communication utilities."""

import json
import os
import sys
import urllib.request
import urllib.error
from typing import Any, Optional


DEFAULT_SERVER_URL = "http://localhost:4000"
DEFAULT_TIMEOUT = 5


def get_server_url() -> str:
    """Get the observability server URL from environment or default."""
    return os.environ.get('OBSERVABILITY_SERVER_URL', DEFAULT_SERVER_URL)


def send_event(
    source_app: str,
    session_id: str,
    hook_event_type: str,
    payload: dict[str, Any],
    chat: Optional[list[dict]] = None,
    summary: Optional[str] = None,
    model_name: Optional[str] = None
) -> dict[str, Any]:
    """
    Send an event to the observability server.

    Args:
        source_app: The application/project identifier
        session_id: The Claude Code session ID
        hook_event_type: Type of hook event (PreToolUse, PostToolUse, etc.)
        payload: The event payload data
        chat: Optional chat transcript
        summary: Optional AI-generated summary
        model_name: Optional model name

    Returns:
        The server response as a dict

    Raises:
        ConnectionError: If server is not reachable
        ValueError: If server returns an error
    """
    server_url = get_server_url()

    event_data = {
        "source_app": source_app,
        "session_id": session_id,
        "hook_event_type": hook_event_type,
        "payload": payload
    }

    if chat is not None:
        event_data["chat"] = chat
    if summary is not None:
        event_data["summary"] = summary
    if model_name is not None:
        event_data["model_name"] = model_name

    json_data = json.dumps(event_data).encode('utf-8')

    request = urllib.request.Request(
        f"{server_url}/events",
        data=json_data,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        method='POST'
    )

    try:
        with urllib.request.urlopen(request, timeout=DEFAULT_TIMEOUT) as response:
            response_data = response.read().decode('utf-8')
            return json.loads(response_data)
    except urllib.error.URLError as e:
        raise ConnectionError(f"Failed to connect to server at {server_url}: {e}")
    except urllib.error.HTTPError as e:
        raise ValueError(f"Server returned error {e.code}: {e.read().decode('utf-8')}")


def check_server_health() -> bool:
    """Check if the observability server is running and healthy."""
    server_url = get_server_url()

    try:
        request = urllib.request.Request(
            f"{server_url}/health",
            method='GET'
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status == 200
    except (urllib.error.URLError, urllib.error.HTTPError):
        return False


def read_stdin_json() -> dict[str, Any]:
    """Read and parse JSON from stdin (Claude Code hook input)."""
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            return {}
        return json.loads(input_data)
    except json.JSONDecodeError as e:
        print(f"Warning: Failed to parse stdin JSON: {e}", file=sys.stderr)
        return {}
