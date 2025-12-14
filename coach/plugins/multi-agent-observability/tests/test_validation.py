#!/usr/bin/env python3
"""Tests for validation utility module."""

import os
import sys
import unittest

# Add the hooks/scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'hooks'))

from scripts.utils.validation import (
    is_dangerous_rm_command,
    is_sensitive_file_access,
    validate_tool_use
)


class TestIsDangerousRmCommand(unittest.TestCase):
    """Tests for is_dangerous_rm_command function."""

    def test_detects_rm_rf_root(self):
        """Should detect rm -rf /."""
        is_dangerous, reason = is_dangerous_rm_command('rm -rf /')
        self.assertTrue(is_dangerous)
        self.assertIn('Dangerous', reason)

    def test_detects_rm_rf_home(self):
        """Should detect rm -rf ~."""
        is_dangerous, reason = is_dangerous_rm_command('rm -rf ~')
        self.assertTrue(is_dangerous)

    def test_detects_rm_rf_wildcard(self):
        """Should detect rm -rf *."""
        is_dangerous, reason = is_dangerous_rm_command('rm -rf *')
        self.assertTrue(is_dangerous)

    def test_detects_rm_rf_parent(self):
        """Should detect rm -rf .."""
        is_dangerous, reason = is_dangerous_rm_command('rm -rf ..')
        self.assertTrue(is_dangerous)

    def test_detects_rm_fr_variant(self):
        """Should detect rm -fr variant."""
        is_dangerous, reason = is_dangerous_rm_command('rm -fr /')
        self.assertTrue(is_dangerous)

    def test_allows_safe_rm_in_tmp(self):
        """Should allow rm -rf in /tmp/."""
        is_dangerous, reason = is_dangerous_rm_command('rm -rf /tmp/test')
        self.assertFalse(is_dangerous)
        self.assertIsNone(reason)

    def test_allows_safe_rm_in_node_modules(self):
        """Should allow rm -rf in node_modules/."""
        is_dangerous, reason = is_dangerous_rm_command('rm -rf node_modules/')
        self.assertFalse(is_dangerous)

    def test_allows_safe_rm_in_trees(self):
        """Should allow rm -rf in trees/ (worktrees)."""
        is_dangerous, reason = is_dangerous_rm_command('rm -rf trees/my-worktree')
        self.assertFalse(is_dangerous)

    def test_allows_normal_rm(self):
        """Should allow normal rm without -rf."""
        is_dangerous, reason = is_dangerous_rm_command('rm file.txt')
        self.assertFalse(is_dangerous)

    def test_allows_unrelated_commands(self):
        """Should allow unrelated commands."""
        is_dangerous, reason = is_dangerous_rm_command('ls -la')
        self.assertFalse(is_dangerous)

        is_dangerous, reason = is_dangerous_rm_command('git status')
        self.assertFalse(is_dangerous)


class TestIsSensitiveFileAccess(unittest.TestCase):
    """Tests for is_sensitive_file_access function."""

    def test_detects_env_file(self):
        """Should detect .env file."""
        is_sensitive, reason = is_sensitive_file_access('/project/.env')
        self.assertTrue(is_sensitive)
        self.assertIn('Sensitive', reason)

    def test_detects_env_local(self):
        """Should detect .env.local file."""
        is_sensitive, reason = is_sensitive_file_access('.env.local')
        self.assertTrue(is_sensitive)

    def test_detects_env_production(self):
        """Should detect .env.production file."""
        is_sensitive, reason = is_sensitive_file_access('/app/.env.production')
        self.assertTrue(is_sensitive)

    def test_detects_credentials_json(self):
        """Should detect credentials.json."""
        is_sensitive, reason = is_sensitive_file_access('credentials.json')
        self.assertTrue(is_sensitive)

    def test_detects_pem_files(self):
        """Should detect .pem files."""
        is_sensitive, reason = is_sensitive_file_access('server.pem')
        self.assertTrue(is_sensitive)

    def test_detects_key_files(self):
        """Should detect .key files."""
        is_sensitive, reason = is_sensitive_file_access('private.key')
        self.assertTrue(is_sensitive)

    def test_detects_ssh_keys(self):
        """Should detect SSH keys."""
        is_sensitive, reason = is_sensitive_file_access('~/.ssh/id_rsa')
        self.assertTrue(is_sensitive)

        is_sensitive, reason = is_sensitive_file_access('~/.ssh/id_ed25519')
        self.assertTrue(is_sensitive)

    def test_allows_env_sample(self):
        """Should allow .env.sample."""
        is_sensitive, reason = is_sensitive_file_access('.env.sample')
        self.assertFalse(is_sensitive)
        self.assertIsNone(reason)

    def test_allows_env_example(self):
        """Should allow .env.example."""
        is_sensitive, reason = is_sensitive_file_access('.env.example')
        self.assertFalse(is_sensitive)

    def test_allows_env_template(self):
        """Should allow .env.template."""
        is_sensitive, reason = is_sensitive_file_access('.env.template')
        self.assertFalse(is_sensitive)

    def test_allows_normal_files(self):
        """Should allow normal files."""
        is_sensitive, reason = is_sensitive_file_access('index.ts')
        self.assertFalse(is_sensitive)

        is_sensitive, reason = is_sensitive_file_access('package.json')
        self.assertFalse(is_sensitive)


class TestValidateToolUse(unittest.TestCase):
    """Tests for validate_tool_use function."""

    def test_blocks_dangerous_bash(self):
        """Should block dangerous Bash commands."""
        is_allowed, reason = validate_tool_use('Bash', {'command': 'rm -rf /'})
        self.assertFalse(is_allowed)
        self.assertIn('Dangerous', reason)

    def test_allows_safe_bash(self):
        """Should allow safe Bash commands."""
        is_allowed, reason = validate_tool_use('Bash', {'command': 'ls -la'})
        self.assertTrue(is_allowed)
        self.assertIsNone(reason)

    def test_blocks_sensitive_read(self):
        """Should block reading sensitive files."""
        is_allowed, reason = validate_tool_use('Read', {'file_path': '.env'})
        self.assertFalse(is_allowed)
        self.assertIn('Sensitive', reason)

    def test_allows_safe_read(self):
        """Should allow reading normal files."""
        is_allowed, reason = validate_tool_use('Read', {'file_path': 'index.ts'})
        self.assertTrue(is_allowed)
        self.assertIsNone(reason)

    def test_blocks_sensitive_write(self):
        """Should block writing sensitive files."""
        is_allowed, reason = validate_tool_use('Write', {'file_path': '.env'})
        self.assertFalse(is_allowed)

    def test_allows_safe_write(self):
        """Should allow writing normal files."""
        is_allowed, reason = validate_tool_use('Write', {'file_path': 'src/app.ts'})
        self.assertTrue(is_allowed)

    def test_blocks_sensitive_edit(self):
        """Should block editing sensitive files."""
        is_allowed, reason = validate_tool_use('Edit', {'file_path': 'credentials.json'})
        self.assertFalse(is_allowed)

    def test_allows_other_tools(self):
        """Should allow other tools by default."""
        is_allowed, reason = validate_tool_use('Grep', {'pattern': 'foo'})
        self.assertTrue(is_allowed)

        is_allowed, reason = validate_tool_use('Glob', {'pattern': '*.ts'})
        self.assertTrue(is_allowed)


if __name__ == '__main__':
    unittest.main()
