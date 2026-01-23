"""Tests for plan_approved.py PostToolUse hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "plugins/oh-my-claude/hooks/plan_approved.py"
)


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
    """Tests for session-specific marker file creation."""

    def test_marker_created_on_post_tool_use(self, marker_home):
        """PostToolUse with tool_result creates session-specific marker."""
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": "test-session-123",
            },
            marker_home,
        )
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved_test-session-123"
        assert marker_path.exists(), "Session-specific marker should be created"

    def test_marker_uses_session_id(self, marker_home):
        """Marker filename should include session ID."""
        session_id = "unique-session-abc"
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": session_id,
            },
            marker_home,
        )
        marker_path = marker_home / ".claude" / "plans" / f".plan_approved_{session_id}"
        assert marker_path.exists(), f"Marker should use session ID: {session_id}"

    def test_marker_is_empty_file(self, marker_home):
        """Marker file should be empty (just a signal, not storage)."""
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": "test",
            },
            marker_home,
        )
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved_test"
        assert marker_path.stat().st_size == 0, "Marker should be empty"

    def test_default_session_id_when_missing(self, marker_home):
        """Uses 'unknown' as default session ID if not provided."""
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
            },
            marker_home,
        )
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved_unknown"
        assert marker_path.exists(), "Should use 'unknown' as default session ID"


class TestPostToolUseOnly:
    """Tests that marker is only created on PostToolUse (with tool_result)."""

    def test_no_marker_without_tool_result(self, marker_home):
        """PreToolUse/PermissionRequest (no tool_result) should NOT create marker."""
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_input": {},
                "session_id": "test-session",
            },
            marker_home,
        )
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved_test-session"
        assert not marker_path.exists(), "Marker should NOT be created without tool_result"

    def test_marker_created_with_tool_result(self, marker_home):
        """PostToolUse (with tool_result) SHOULD create marker."""
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": "test-session",
            },
            marker_home,
        )
        marker_path = marker_home / ".claude" / "plans" / ".plan_approved_test-session"
        assert marker_path.exists(), "Marker SHOULD be created with tool_result"


class TestNoMarkerOnEmptyInput:
    """Tests for graceful handling of empty/malformed input."""

    def test_no_marker_on_empty_dict(self, marker_home):
        """Empty input dict should not create any marker."""
        run_hook({}, marker_home)
        # Check no markers created
        plans_dir = marker_home / ".claude" / "plans"
        markers = list(plans_dir.glob(".plan_approved_*"))
        assert len(markers) == 0, "No markers should be created for empty input"

    def test_no_crash_on_empty_input(self, marker_home):
        """Hook should exit cleanly on empty input."""
        output = run_hook({}, marker_home)
        assert output == {} or output == {"hookSpecificOutput": {}}


class TestHookReturnsEmpty:
    """Tests for hook output format."""

    def test_returns_empty_on_success(self, marker_home):
        """Hook should return empty output (no additional context needed)."""
        output = run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": "test",
            },
            marker_home,
        )
        context = output.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert context == "", "Hook should return empty context"


class TestMarkerDirectory:
    """Tests for marker directory creation."""

    def test_creates_parent_directories(self, tmp_path):
        """Hook should create ~/.claude/plans/ if it doesn't exist."""
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": "test",
            },
            tmp_path,
        )
        marker_path = tmp_path / ".claude" / "plans" / ".plan_approved_test"
        assert marker_path.exists(), "Marker and parent directories should be created"


class TestIdempotency:
    """Tests for idempotent marker creation."""

    def test_marker_idempotent_skip_if_exists(self, marker_home):
        """Second call should skip marker creation if it already exists."""
        session_id = "test-session"
        marker_path = marker_home / ".claude" / "plans" / f".plan_approved_{session_id}"
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "session_id": session_id,
        }

        # First call creates marker
        run_hook(input_data, marker_home)
        assert marker_path.exists(), "Marker should exist after first call"
        first_stat = marker_path.stat()

        # Second call should skip (marker already exists)
        run_hook(input_data, marker_home)
        assert marker_path.exists(), "Marker should still exist"
        second_stat = marker_path.stat()

        # mtime should be unchanged (file not recreated)
        assert first_stat.st_mtime == second_stat.st_mtime, "Idempotent: marker unchanged"


class TestSessionIsolation:
    """Tests for session-specific marker isolation."""

    def test_different_sessions_different_markers(self, marker_home):
        """Different sessions should create different markers."""
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": "session-1",
            },
            marker_home,
        )
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": "session-2",
            },
            marker_home,
        )

        marker_1 = marker_home / ".claude" / "plans" / ".plan_approved_session-1"
        marker_2 = marker_home / ".claude" / "plans" / ".plan_approved_session-2"

        assert marker_1.exists(), "Session 1 marker should exist"
        assert marker_2.exists(), "Session 2 marker should exist"

    def test_sessions_do_not_interfere(self, marker_home):
        """Deleting one session's marker doesn't affect another."""
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": "session-a",
            },
            marker_home,
        )
        run_hook(
            {
                "tool_name": "ExitPlanMode",
                "tool_result": {},
                "session_id": "session-b",
            },
            marker_home,
        )

        marker_a = marker_home / ".claude" / "plans" / ".plan_approved_session-a"
        marker_b = marker_home / ".claude" / "plans" / ".plan_approved_session-b"

        # Delete marker A
        marker_a.unlink()

        # Marker B should be unaffected
        assert not marker_a.exists(), "Marker A should be deleted"
        assert marker_b.exists(), "Marker B should still exist"
