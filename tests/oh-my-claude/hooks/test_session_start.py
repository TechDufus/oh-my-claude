"""Tests for session_start.py SessionStart hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/session_start.py"


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


def get_context(output: dict) -> str:
    """Extract additionalContext from hook output."""
    return output.get("hookSpecificOutput", {}).get("additionalContext", "")


@pytest.fixture
def marker_home(tmp_path):
    """Create a temporary home directory for marker file tests."""
    claude_dir = tmp_path / ".claude" / "plans"
    claude_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def marker_home_with_marker(marker_home):
    """Create marker home with .plan_approved marker file."""
    marker_path = marker_home / ".claude" / "plans" / ".plan_approved"
    marker_path.touch()
    return marker_home


class TestUltraworkInjection:
    """Tests for ULTRAWORK context injection when marker exists."""

    def test_ultrawork_injected_when_marker_exists(self, marker_home_with_marker):
        """When marker exists, should inject ULTRAWORK context."""
        output = run_hook({}, marker_home_with_marker)
        context = get_context(output)
        assert "ULTRAWORK MODE ACTIVE" in context
        assert "PLAN EXECUTION" in context

    def test_context_includes_execution_protocol(self, marker_home_with_marker):
        """Injected context should include execution protocol."""
        output = run_hook({}, marker_home_with_marker)
        context = get_context(output)
        assert "Create todos" in context
        assert "Execute in order" in context
        assert "Verify each step" in context

    def test_context_includes_compliance_rules(self, marker_home_with_marker):
        """Injected context should include plan compliance rules."""
        output = run_hook({}, marker_home_with_marker)
        context = get_context(output)
        assert "Allowed" in context
        assert "NOT Allowed" in context


class TestMarkerConsumption:
    """Tests for marker consumption after injection."""

    def test_marker_consumed_after_injection(self, marker_home_with_marker):
        """Marker should be deleted after successful injection."""
        marker_path = marker_home_with_marker / ".claude" / "plans" / ".plan_approved"
        assert marker_path.exists(), "Marker should exist before hook runs"

        run_hook({}, marker_home_with_marker)

        assert not marker_path.exists(), "Marker should be consumed (deleted)"

    def test_second_run_returns_empty(self, marker_home_with_marker):
        """Second run after marker consumed should return empty."""
        # First run consumes marker
        run_hook({}, marker_home_with_marker)

        # Second run should return empty
        output = run_hook({}, marker_home_with_marker)
        context = get_context(output)
        assert context == "", "No context after marker consumed"


class TestNoMarkerBehavior:
    """Tests for behavior when no marker exists."""

    def test_no_output_when_no_marker(self, marker_home):
        """When no marker exists, should return empty output."""
        output = run_hook({}, marker_home)
        context = get_context(output)
        assert context == "", "Should return empty when no marker"

    def test_no_crash_when_no_marker(self, marker_home):
        """Hook should exit cleanly when no marker exists."""
        # Should not raise
        output = run_hook({}, marker_home)
        # Either empty dict or empty hookSpecificOutput
        assert output == {} or get_context(output) == ""


class TestEmptyInputHandled:
    """Tests for graceful handling of various input formats."""

    def test_empty_dict_input(self, marker_home_with_marker):
        """Empty input dict should still trigger injection if marker exists."""
        output = run_hook({}, marker_home_with_marker)
        context = get_context(output)
        assert "ULTRAWORK MODE ACTIVE" in context

    def test_input_with_extra_fields(self, marker_home_with_marker):
        """Input with extra fields should still work."""
        output = run_hook({
            "session_id": "test-123",
            "cwd": "/some/path",
            "extra": "data"
        }, marker_home_with_marker)
        context = get_context(output)
        assert "ULTRAWORK MODE ACTIVE" in context
