"""Validation utilities for pre-tool-use hooks."""

import re
from typing import Optional


# Dangerous patterns for bash commands
DANGEROUS_RM_PATTERNS = [
    r'rm\s+-rf\s+/',           # rm -rf / (root)
    r'rm\s+-rf\s+~',           # rm -rf ~ (home)
    r'rm\s+-rf\s+\*',          # rm -rf * (wildcard)
    r'rm\s+-rf\s+\.\.',        # rm -rf .. (parent)
    r'rm\s+-fr\s+/',           # rm -fr variant
    r'rm\s+-fr\s+~',
    r'rm\s+-fr\s+\*',
    r'rm\s+-fr\s+\.\.',
]

# Directories where rm -rf is allowed (safe sandboxes)
SAFE_RM_DIRECTORIES = [
    r'/tmp/',
    r'/var/tmp/',
    r'trees/',           # Git worktrees
    r'\.cache/',
    r'node_modules/',
    r'__pycache__/',
    r'\.pytest_cache/',
    r'dist/',
    r'build/',
]

# Sensitive file patterns
SENSITIVE_FILE_PATTERNS = [
    r'\.env$',           # .env files (not .env.sample)
    r'\.env\.local$',
    r'\.env\.production$',
    r'credentials\.json$',
    r'secrets\.json$',
    r'\.pem$',
    r'\.key$',
    r'id_rsa',
    r'id_ed25519',
]

# Allowed sensitive file patterns (exceptions)
ALLOWED_SENSITIVE_PATTERNS = [
    r'\.env\.sample$',
    r'\.env\.example$',
    r'\.env\.template$',
]


def is_dangerous_rm_command(command: str) -> tuple[bool, Optional[str]]:
    """
    Check if a bash command contains dangerous rm operations.

    Returns:
        (is_dangerous, reason) tuple
    """
    # Check for dangerous rm patterns
    for pattern in DANGEROUS_RM_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            # Check if it's in a safe directory
            is_safe = False
            for safe_pattern in SAFE_RM_DIRECTORIES:
                if re.search(safe_pattern, command):
                    is_safe = True
                    break

            if not is_safe:
                return True, f"Dangerous rm command detected: matches pattern '{pattern}'"

    return False, None


def is_sensitive_file_access(file_path: str) -> tuple[bool, Optional[str]]:
    """
    Check if a file path points to a sensitive file.

    Returns:
        (is_sensitive, reason) tuple
    """
    # Check if it matches an allowed pattern first
    for pattern in ALLOWED_SENSITIVE_PATTERNS:
        if re.search(pattern, file_path, re.IGNORECASE):
            return False, None

    # Check if it matches a sensitive pattern
    for pattern in SENSITIVE_FILE_PATTERNS:
        if re.search(pattern, file_path, re.IGNORECASE):
            return True, f"Sensitive file access detected: {file_path}"

    return False, None


def validate_tool_use(tool_name: str, tool_input: dict) -> tuple[bool, Optional[str]]:
    """
    Validate a tool use for safety.

    Returns:
        (is_allowed, block_reason) tuple
        - is_allowed=True, block_reason=None: Tool use is safe
        - is_allowed=False, block_reason=str: Tool use should be blocked
    """
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        is_dangerous, reason = is_dangerous_rm_command(command)
        if is_dangerous:
            return False, reason

    if tool_name in ("Read", "Write", "Edit"):
        file_path = tool_input.get("file_path", "")
        is_sensitive, reason = is_sensitive_file_access(file_path)
        if is_sensitive:
            return False, reason

    return True, None
