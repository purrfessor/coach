#!/usr/bin/env python3
"""
Pre-tool-use validation hook.

This script validates tool usage before execution and can block
dangerous operations like destructive rm commands or sensitive file access.

Exit codes:
    0 - Allow the tool use
    2 - Block the tool use (stderr message fed back to Claude)
"""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.server import read_stdin_json
from scripts.utils.validation import validate_tool_use


def main():
    # Read hook input from stdin
    hook_data = read_stdin_json()

    if not hook_data:
        # No input, allow by default
        sys.exit(0)

    tool_name = hook_data.get('tool_name', '')
    tool_input = hook_data.get('tool_input', {})

    # Validate the tool use
    is_allowed, block_reason = validate_tool_use(tool_name, tool_input)

    if not is_allowed:
        # Output block reason to stderr (will be fed back to Claude)
        error_response = {
            "decision": "deny",
            "reason": block_reason,
            "systemMessage": f"Tool use blocked by observability plugin: {block_reason}"
        }
        print(json.dumps(error_response), file=sys.stderr)
        sys.exit(2)

    # Tool use is allowed
    sys.exit(0)


if __name__ == '__main__':
    main()
