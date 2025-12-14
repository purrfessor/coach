#!/usr/bin/env python3
"""Tests for source_app utility module."""

import os
import sys
import tempfile
import subprocess
import unittest
from unittest.mock import patch, MagicMock

# Add the hooks/scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hooks'))

from scripts.utils.source_app import (
    get_source_app,
    get_truncated_session_id,
    get_agent_display_id
)


class TestGetSourceApp(unittest.TestCase):
    """Tests for get_source_app function."""

    @patch('subprocess.run')
    @patch.dict(os.environ, {'CLAUDE_PROJECT_DIR': '/test/project'})
    def test_returns_git_repo_name_https(self, mock_run):
        """Should return repo name from HTTPS git URL."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='https://github.com/user/my-awesome-repo.git\n'
        )
        result = get_source_app()
        self.assertEqual(result, 'my-awesome-repo')

    @patch('subprocess.run')
    @patch.dict(os.environ, {'CLAUDE_PROJECT_DIR': '/test/project'})
    def test_returns_git_repo_name_ssh(self, mock_run):
        """Should return repo name from SSH git URL."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='git@github.com:user/another-repo.git\n'
        )
        result = get_source_app()
        self.assertEqual(result, 'another-repo')

    @patch('subprocess.run')
    @patch.dict(os.environ, {'CLAUDE_PROJECT_DIR': '/test/my-project'})
    def test_falls_back_to_directory_name(self, mock_run):
        """Should fall back to directory name when git fails."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=''
        )
        result = get_source_app()
        self.assertEqual(result, 'my-project')

    @patch('subprocess.run')
    @patch.dict(os.environ, {}, clear=True)
    def test_falls_back_to_cwd(self, mock_run):
        """Should fall back to current working directory."""
        mock_run.return_value = MagicMock(returncode=1, stdout='')
        # This will use os.getcwd() which should give a valid directory name
        result = get_source_app()
        self.assertIsInstance(result, str)
        self.assertNotEqual(result, '')

    @patch('subprocess.run')
    @patch.dict(os.environ, {'CLAUDE_PROJECT_DIR': '/test/project'})
    def test_handles_git_timeout(self, mock_run):
        """Should handle git command timeout gracefully."""
        mock_run.side_effect = subprocess.TimeoutExpired(cmd='git', timeout=5)
        result = get_source_app()
        self.assertEqual(result, 'project')


class TestGetTruncatedSessionId(unittest.TestCase):
    """Tests for get_truncated_session_id function."""

    def test_truncates_to_default_length(self):
        """Should truncate to 8 characters by default."""
        result = get_truncated_session_id('abcdefghijklmnop')
        self.assertEqual(result, 'abcdefgh')
        self.assertEqual(len(result), 8)

    def test_truncates_to_custom_length(self):
        """Should truncate to specified length."""
        result = get_truncated_session_id('abcdefghijklmnop', length=4)
        self.assertEqual(result, 'abcd')

    def test_handles_short_input(self):
        """Should handle input shorter than truncation length."""
        result = get_truncated_session_id('abc')
        self.assertEqual(result, 'abc')

    def test_handles_empty_input(self):
        """Should return 'unknown' for empty input."""
        result = get_truncated_session_id('')
        self.assertEqual(result, 'unknown')

    def test_handles_none_input(self):
        """Should return 'unknown' for None input."""
        result = get_truncated_session_id(None)
        self.assertEqual(result, 'unknown')


class TestGetAgentDisplayId(unittest.TestCase):
    """Tests for get_agent_display_id function."""

    def test_formats_correctly(self):
        """Should format as source_app:truncated_session_id."""
        result = get_agent_display_id('my-app', 'session123456789')
        self.assertEqual(result, 'my-app:session1')  # 8 chars = 'session1'

    def test_handles_short_session_id(self):
        """Should handle short session IDs."""
        result = get_agent_display_id('my-app', 'abc')
        self.assertEqual(result, 'my-app:abc')


if __name__ == '__main__':
    unittest.main()
