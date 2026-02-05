"""Tests for notification_alert.py hook."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from notification_alert import get_notifier_command, send_notification

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/notification_alert.py"


def run_hook(input_data: dict, env: dict[str, str] | None = None) -> dict:
    """Run the hook with given input and return parsed output."""
    if env is None:
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
        }
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
# Unit Tests: get_notifier_command
# =============================================================================


class TestGetNotifierCommand:
    """Tests for get_notifier_command function."""

    def test_macos_returns_osascript(self):
        """Should return osascript command on macOS."""
        with patch("notification_alert.sys") as mock_sys:
            mock_sys.platform = "darwin"
            cmd = get_notifier_command("Title", "Message")
            assert cmd is not None
            assert cmd[0] == "osascript"
            assert "Title" in cmd[2]
            assert "Message" in cmd[2]

    def test_windows_returns_powershell(self):
        """Should return powershell command on Windows."""
        with patch("notification_alert.sys") as mock_sys:
            mock_sys.platform = "win32"
            cmd = get_notifier_command("Title", "Message")
            assert cmd is not None
            assert cmd[0] == "powershell"

    def test_linux_notify_send(self):
        """Should return notify-send on Linux when available."""
        with patch("notification_alert.sys") as mock_sys, \
             patch("notification_alert.shutil.which") as mock_which, \
             patch("notification_alert.Path") as mock_path_cls:
            mock_sys.platform = "linux"
            # Make /proc/version read fail (not WSL)
            mock_path_cls.return_value.read_text.side_effect = FileNotFoundError
            mock_which.return_value = "/usr/bin/notify-send"
            cmd = get_notifier_command("Title", "Message")
            assert cmd is not None
            assert cmd[0] == "notify-send"
            assert cmd[1] == "Title"
            assert cmd[2] == "Message"

    def test_linux_no_notifier_returns_none(self):
        """Should return None on Linux when no notifier available."""
        with patch("notification_alert.sys") as mock_sys, \
             patch("notification_alert.shutil.which", return_value=None), \
             patch("notification_alert.Path") as mock_path_cls:
            mock_sys.platform = "linux"
            mock_path_cls.return_value.read_text.side_effect = FileNotFoundError
            cmd = get_notifier_command("Title", "Message")
            assert cmd is None


# =============================================================================
# Unit Tests: send_notification
# =============================================================================


class TestSendNotification:
    """Tests for send_notification function."""

    def test_returns_true_on_success(self):
        """Should return True when notification command succeeds."""
        with patch("notification_alert.get_notifier_command", return_value=["echo", "test"]), \
             patch("notification_alert.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            assert send_notification("Title", "Message") is True

    def test_returns_false_on_timeout(self):
        """Should return False when notification command times out."""
        with patch("notification_alert.get_notifier_command", return_value=["slow", "cmd"]), \
             patch("notification_alert.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="slow", timeout=10)
            assert send_notification("Title", "Message") is False

    def test_returns_false_on_error(self):
        """Should return False when notification command raises exception."""
        with patch("notification_alert.get_notifier_command", return_value=["bad", "cmd"]), \
             patch("notification_alert.subprocess.run") as mock_run:
            mock_run.side_effect = OSError("command not found")
            assert send_notification("Title", "Message") is False

    def test_returns_false_when_no_notifier(self):
        """Should return False when no notifier command is available."""
        with patch("notification_alert.get_notifier_command", return_value=None):
            assert send_notification("Title", "Message") is False


# =============================================================================
# Integration Tests: main function via subprocess
# =============================================================================


class TestMainIntegration:
    """Integration tests for the main hook function via subprocess."""

    def test_disabled_by_default(self):
        """Should return empty when OMC_NOTIFICATIONS is not set."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
        }
        output = run_hook({"hook_event_name": "Stop", "stopReason": "end_turn"}, env=env)
        assert output == {}

    def test_disabled_when_zero(self):
        """Should return empty when OMC_NOTIFICATIONS=0."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
            "OMC_NOTIFICATIONS": "0",
        }
        output = run_hook({"hook_event_name": "Stop", "stopReason": "end_turn"}, env=env)
        assert output == {}

    def test_enabled_with_stop_event(self):
        """Should process Stop event when OMC_NOTIFICATIONS=1."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
            "OMC_NOTIFICATIONS": "1",
        }
        # Hook sends notification and returns empty (never blocks)
        output = run_hook({"hook_event_name": "Stop", "stopReason": "end_turn"}, env=env)
        assert output == {}

    def test_enabled_with_notification_event(self):
        """Should process Notification event when OMC_NOTIFICATIONS=1."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
            "OMC_NOTIFICATIONS": "1",
        }
        output = run_hook(
            {"hook_event_name": "Notification", "notification_type": "review needed"},
            env=env,
        )
        assert output == {}

    def test_empty_input_when_enabled(self):
        """Should handle empty input when enabled."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
            "OMC_NOTIFICATIONS": "1",
        }
        output = run_hook({}, env=env)
        assert output == {}

    def test_malformed_input_when_enabled(self):
        """Should handle malformed input when enabled."""
        env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": os.environ.get("HOME", "/tmp"),
            "OMC_NOTIFICATIONS": "1",
        }
        output = run_hook({"hook_event_name": "UnknownEvent"}, env=env)
        assert output == {}
