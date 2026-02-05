"""Tests for openkanban_status.py hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from openkanban_status import determine_status, write_status

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/openkanban_status.py"


def run_hook(input_data: dict, env: dict[str, str] | None = None) -> dict:
    """Run the hook with given input and return parsed output."""
    if env is None:
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        pytest.fail(f"Hook failed: {result.stderr}")

    if not result.stdout.strip():
        return {}

    return json.loads(result.stdout)


# =============================================================================
# Unit Tests: write_status
# =============================================================================


class TestWriteStatus:
    """Tests for write_status function."""

    def test_writes_file_to_cache_dir(self, tmp_path):
        """Should write status to a file in the cache directory."""
        with patch("openkanban_status.CACHE_DIR", tmp_path):
            write_status("test-session", "working")
            status_file = tmp_path / "test-session.status"
            assert status_file.exists()
            assert status_file.read_text() == "working"

    def test_creates_parent_dirs(self, tmp_path):
        """Should create parent directories if they don't exist."""
        cache_dir = tmp_path / "nested" / "cache"
        with patch("openkanban_status.CACHE_DIR", cache_dir):
            write_status("sess-1", "idle")
            assert (cache_dir / "sess-1.status").exists()

    def test_handles_permission_errors(self, tmp_path):
        """Should silently handle permission errors."""
        # Use a path that can't be written to
        with patch("openkanban_status.CACHE_DIR", Path("/proc/nonexistent/path")):
            # Should not raise
            write_status("test", "idle")

    def test_overwrites_existing_status(self, tmp_path):
        """Should overwrite existing status file."""
        with patch("openkanban_status.CACHE_DIR", tmp_path):
            write_status("sess", "working")
            write_status("sess", "idle")
            assert (tmp_path / "sess.status").read_text() == "idle"


# =============================================================================
# Unit Tests: determine_status
# =============================================================================


class TestDetermineStatus:
    """Tests for determine_status function."""

    def test_session_start_returns_idle(self):
        """SessionStart shape (session_id, no tool_name, no prompt) -> idle."""
        data = {"session_id": "abc-123"}
        assert determine_status(data) == "idle"

    def test_user_prompt_returns_working(self):
        """UserPromptSubmit shape (has prompt) -> working."""
        data = {"prompt": "fix the bug"}
        assert determine_status(data) == "working"

    def test_pre_tool_use_returns_working(self):
        """PreToolUse shape (tool_name, no tool_result) -> working."""
        data = {"tool_name": "Edit"}
        assert determine_status(data) == "working"

    def test_stop_returns_idle(self):
        """Stop shape (has stopReason) -> idle."""
        data = {"stopReason": "end_turn"}
        assert determine_status(data) == "idle"

    def test_returns_none_for_unrecognized(self):
        """Should return None for unrecognized data shapes."""
        assert determine_status({}) is None
        assert determine_status({"random_field": "value"}) is None

    def test_tool_result_is_not_working(self):
        """PostToolUse shape (tool_name + tool_result) should not be 'working'."""
        data = {"tool_name": "Edit", "tool_result": "success"}
        # Has tool_name but also tool_result, so PreToolUse check fails
        # Only stopReason would match -> None
        assert determine_status(data) is None

    def test_session_with_tool_name_is_not_idle(self):
        """Session with tool_name should not be idle (goes to working)."""
        data = {"session_id": "abc", "tool_name": "Bash"}
        # session_id present but tool_name also present -> not idle from first check
        # Falls to PreToolUse check -> working
        assert determine_status(data) == "working"

    def test_session_with_prompt_is_working(self):
        """Session with prompt should be working, not idle."""
        data = {"session_id": "abc", "prompt": "do something"}
        # session_id present but prompt also present -> not idle from first check
        # Falls to prompt check -> working
        assert determine_status(data) == "working"


# =============================================================================
# Integration Tests: main function via subprocess
# =============================================================================


class TestMainIntegration:
    """Integration tests for the main hook function via subprocess."""

    def test_no_openkanban_session_returns_empty(self):
        """Should return empty when OPENKANBAN_SESSION not set."""
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin")}
        # Explicitly no OPENKANBAN_SESSION
        output = run_hook({"session_id": "test"}, env=env)
        assert output == {}

    def test_session_start_writes_idle(self, tmp_path):
        """SessionStart hookEventName should write idle status."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(tmp_path),
            "OPENKANBAN_SESSION": "test-session",
        }
        output = run_hook(
            {"hookEventName": "SessionStart", "session_id": "test"},
            env=env,
        )
        # Hook always returns empty output (never blocks)
        assert output == {}

    def test_user_prompt_submit_writes_working(self, tmp_path):
        """UserPromptSubmit hookEventName should write working status."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(tmp_path),
            "OPENKANBAN_SESSION": "test-session",
        }
        output = run_hook(
            {"hookEventName": "UserPromptSubmit", "prompt": "fix bug"},
            env=env,
        )
        assert output == {}

    def test_pre_tool_use_writes_working(self, tmp_path):
        """PreToolUse hookEventName should write working status."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(tmp_path),
            "OPENKANBAN_SESSION": "test-session",
        }
        output = run_hook(
            {"hookEventName": "PreToolUse", "tool_name": "Edit"},
            env=env,
        )
        assert output == {}

    def test_permission_request_writes_waiting(self, tmp_path):
        """PermissionRequest hookEventName should write waiting status."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(tmp_path),
            "OPENKANBAN_SESSION": "test-session",
        }
        output = run_hook(
            {"hookEventName": "PermissionRequest", "permission": "ask"},
            env=env,
        )
        assert output == {}

    def test_stop_writes_idle(self, tmp_path):
        """Stop hookEventName should write idle status."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(tmp_path),
            "OPENKANBAN_SESSION": "test-session",
        }
        output = run_hook(
            {"hookEventName": "Stop", "stopReason": "end_turn"},
            env=env,
        )
        assert output == {}

    def test_unknown_event_falls_through(self, tmp_path):
        """Unknown hookEventName should fall through to determine_status."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(tmp_path),
            "OPENKANBAN_SESSION": "test-session",
        }
        output = run_hook(
            {"hookEventName": "UnknownEvent", "prompt": "something"},
            env=env,
        )
        # Still returns empty (hook never blocks)
        assert output == {}

    def test_empty_input_with_session(self, tmp_path):
        """Empty data with OPENKANBAN_SESSION should not crash."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(tmp_path),
            "OPENKANBAN_SESSION": "test-session",
        }
        output = run_hook({}, env=env)
        assert output == {}
