#!/usr/bin/env python3
"""Tests for server utility module."""

import io
import json
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add the hooks/scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hooks'))

from scripts.utils.server import (
    get_server_url,
    read_stdin_json,
    check_server_health
)


class TestGetServerUrl(unittest.TestCase):
    """Tests for get_server_url function."""

    def test_returns_default_url(self):
        """Should return default URL when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            # Clear any existing env var
            os.environ.pop('OBSERVABILITY_SERVER_URL', None)
            result = get_server_url()
            self.assertEqual(result, 'http://localhost:4000')

    def test_returns_custom_url(self):
        """Should return custom URL from environment."""
        with patch.dict(os.environ, {'OBSERVABILITY_SERVER_URL': 'http://custom:8000'}):
            result = get_server_url()
            self.assertEqual(result, 'http://custom:8000')


class TestReadStdinJson(unittest.TestCase):
    """Tests for read_stdin_json function."""

    def test_parses_valid_json(self):
        """Should parse valid JSON from stdin."""
        test_data = {'key': 'value', 'number': 42}
        with patch('sys.stdin', io.StringIO(json.dumps(test_data))):
            result = read_stdin_json()
            self.assertEqual(result, test_data)

    def test_returns_empty_dict_for_empty_input(self):
        """Should return empty dict for empty stdin."""
        with patch('sys.stdin', io.StringIO('')):
            result = read_stdin_json()
            self.assertEqual(result, {})

    def test_returns_empty_dict_for_whitespace(self):
        """Should return empty dict for whitespace-only stdin."""
        with patch('sys.stdin', io.StringIO('   \n  ')):
            result = read_stdin_json()
            self.assertEqual(result, {})

    def test_returns_empty_dict_for_invalid_json(self):
        """Should return empty dict for invalid JSON."""
        with patch('sys.stdin', io.StringIO('not valid json {')):
            result = read_stdin_json()
            self.assertEqual(result, {})


class TestCheckServerHealth(unittest.TestCase):
    """Tests for check_server_health function."""

    @patch('urllib.request.urlopen')
    def test_returns_true_when_server_healthy(self, mock_urlopen):
        """Should return True when server responds with 200."""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = lambda s: mock_response
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = check_server_health()
        self.assertTrue(result)

    @patch('urllib.request.urlopen')
    def test_returns_false_when_server_down(self, mock_urlopen):
        """Should return False when server is not reachable."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError('Connection refused')

        result = check_server_health()
        self.assertFalse(result)

    @patch('urllib.request.urlopen')
    def test_returns_false_on_http_error(self, mock_urlopen):
        """Should return False on HTTP error."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url='http://localhost:4000/health',
            code=500,
            msg='Internal Server Error',
            hdrs={},
            fp=None
        )

        result = check_server_health()
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()
