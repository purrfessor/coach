"""Auto-detect source app from project context."""

import os
import subprocess
from pathlib import Path


def get_source_app() -> str:
    """
    Derive source_app from project directory name or git remote.

    Priority:
    1. Git remote repository name
    2. Directory name of CLAUDE_PROJECT_DIR
    3. Current working directory name
    4. Fallback to 'unknown'
    """
    cwd = os.environ.get('CLAUDE_PROJECT_DIR', os.getcwd())

    # Try git remote first
    try:
        result = subprocess.run(
            ['git', 'remote', 'get-url', 'origin'],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            # Handle both HTTPS and SSH URLs
            # https://github.com/user/repo.git -> repo
            # git@github.com:user/repo.git -> repo
            repo_name = url.split('/')[-1].replace('.git', '')
            if repo_name:
                return repo_name
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    # Fall back to directory name
    if cwd:
        dir_name = os.path.basename(cwd)
        if dir_name:
            return dir_name

    return 'unknown'


def get_truncated_session_id(session_id: str, length: int = 8) -> str:
    """Truncate session ID to specified length for display."""
    if not session_id:
        return 'unknown'
    return session_id[:length]


def get_agent_display_id(source_app: str, session_id: str) -> str:
    """Format agent ID as source_app:session_id (truncated)."""
    truncated = get_truncated_session_id(session_id)
    return f"{source_app}:{truncated}"
