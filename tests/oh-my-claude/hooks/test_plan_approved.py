"""Tests for plan_approved.py PostToolUse hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/plan_approved.py"


def run_hook(input_data: dict, marker_dir: Path) -> dict:
    """Run the hook with given input and return parsed output."""
    env = {
        "HOME": str(marker_dir),
        "PATH": "/usr/bin:/bin",
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


@pytest.fixture
def marker_home(tmp_path):
    """Create a temporary home directory for marker file tests."""
    claude_dir = tmp_path / ".claude" / "plans"
    claude_dir.mkdir(parents=True)
    return tmp_path


class TestMarkerCreation:
    """Tests for marker file creation."""

    def test_marker_created_on_valid_input(self, marker_home):
        """When hook receives valid input, marker file should be created."""
        run_hook({"tool_name": "ExitPlanMode"}, marker_home)
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved"
        assert marker_path.exists(), "Marker file should be created"

    def test_marker_created_with_empty_tool_input(self, marker_home):
        """Marker should be created even with minimal input."""
        run_hook({"tool_name": "ExitPlanMode", "tool_input": {}}, marker_home)
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved"
        assert marker_path.exists(), "Marker file should be created"

    def test_marker_is_empty_file(self, marker_home):
        """Marker file should be empty (just a signal, not storage)."""
        run_hook({"tool_name": "ExitPlanMode"}, marker_home)
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved"
        # touch() creates empty file
        assert marker_path.stat().st_size == 0, "Marker should be empty"


class TestNoMarkerOnEmptyInput:
    """Tests for graceful handling of empty/malformed input."""

    def test_no_marker_on_empty_dict(self, marker_home):
        """Empty input dict should not create marker."""
        run_hook({}, marker_home)
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved"
        assert not marker_path.exists(), "Marker should NOT be created for empty input"

    def test_no_crash_on_empty_input(self, marker_home):
        """Hook should exit cleanly on empty input."""
        # Should not raise
        output = run_hook({}, marker_home)
        assert output == {} or output == {"hookSpecificOutput": {}}


class TestHookReturnsEmpty:
    """Tests for hook output format."""

    def test_returns_empty_on_success(self, marker_home):
        """Hook should return empty output (no additional context needed)."""
        output = run_hook({"tool_name": "ExitPlanMode"}, marker_home)
        # Empty output or empty hookSpecificOutput
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert context == "", "Hook should return empty context"


class TestMarkerDirectory:
    """Tests for marker directory creation."""

    def test_creates_parent_directories(self, tmp_path):
        """Hook should create ~/.claude/plans/ if it doesn't exist."""
        # Don't create the directory beforehand
        run_hook({"tool_name": "ExitPlanMode"}, tmp_path)
        marker_path = tmp_path / ".claude" / "plans" / ".plan_approved"
        assert marker_path.exists(), "Marker and parent directories should be created"


class TestIdempotency:
    """Tests for idempotent marker creation."""

    def test_marker_idempotent_skip_if_exists(self, marker_home):
        """Second call should skip marker creation if it already exists."""
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved"

        # First call creates marker
        run_hook({"tool_name": "ExitPlanMode"}, marker_home)
        assert marker_path.exists(), "Marker should exist after first call"
        first_stat = marker_path.stat()

        # Second call should skip (marker already exists)
        run_hook({"tool_name": "ExitPlanMode"}, marker_home)
        assert marker_path.exists(), "Marker should still exist"
        second_stat = marker_path.stat()

        # mtime should be unchanged (file not recreated)
        assert first_stat.st_mtime == second_stat.st_mtime, "Idempotent: marker unchanged"
