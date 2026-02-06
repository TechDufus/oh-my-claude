"""Tests for verification_reminder.py PostToolUse hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/verification_reminder.py"


def run_hook(input_data: dict) -> dict:
    """Run the hook with given input and return parsed output."""
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"Hook failed: {result.stderr}")

    if not result.stdout.strip():
        return {}

    return json.loads(result.stdout)


def get_context(output: dict) -> str:
    """Extract additionalContext from hook output."""
    return output.get("hookSpecificOutput", {}).get("additionalContext", "")


class TestTaskTriggersReminder:
    """Tests for Task tool triggering verification reminder."""

    def test_task_triggers_reminder(self):
        """When tool_name is Task, should output verification context."""
        output = run_hook({"tool_name": "Task"})
        context = get_context(output)
        assert "Verification Required" in context

    def test_task_includes_verification_steps(self):
        """Verification reminder should include all verification steps."""
        output = run_hook({"tool_name": "Task"})
        context = get_context(output)
        assert "READ" in context
        assert "RUN" in context
        assert "CHECK" in context
        assert "COMPARE" in context

    def test_task_mentions_agent_context(self):
        """Verification reminder should mention agent context isolation."""
        output = run_hook({"tool_name": "Task"})
        context = get_context(output)
        assert "Agent context is isolated" in context


class TestNonTaskToolsNoOp:
    """Tests for non-Task tools returning empty."""

    def test_read_tool_no_output(self):
        """Read tool should return empty output."""
        output = run_hook({"tool_name": "Read"})
        context = get_context(output)
        assert context == ""

    def test_bash_tool_no_output(self):
        """Bash tool should return empty output."""
        output = run_hook({"tool_name": "Bash"})
        context = get_context(output)
        assert context == ""

    def test_edit_tool_no_output(self):
        """Edit tool should return empty output."""
        output = run_hook({"tool_name": "Edit"})
        context = get_context(output)
        assert context == ""

    def test_write_tool_no_output(self):
        """Write tool should return empty output."""
        output = run_hook({"tool_name": "Write"})
        context = get_context(output)
        assert context == ""

    def test_glob_tool_no_output(self):
        """Glob tool should return empty output."""
        output = run_hook({"tool_name": "Glob"})
        context = get_context(output)
        assert context == ""

    def test_grep_tool_no_output(self):
        """Grep tool should return empty output."""
        output = run_hook({"tool_name": "Grep"})
        context = get_context(output)
        assert context == ""

    def test_todowrite_tool_no_output(self):
        """TodoWrite tool should return empty output."""
        output = run_hook({"tool_name": "TodoWrite"})
        context = get_context(output)
        assert context == ""


class TestEmptyInputHandled:
    """Tests for graceful handling of empty/malformed input."""

    def test_empty_dict_returns_empty(self):
        """Empty input dict should return empty output."""
        output = run_hook({})
        context = get_context(output)
        assert context == ""

    def test_missing_tool_name_returns_empty(self):
        """Missing tool_name should return empty output."""
        output = run_hook({"other_field": "value"})
        context = get_context(output)
        assert context == ""

    def test_null_tool_name_returns_empty(self):
        """Null tool_name should return empty output."""
        output = run_hook({"tool_name": None})
        context = get_context(output)
        assert context == ""

    def test_empty_string_tool_name_returns_empty(self):
        """Empty string tool_name should return empty output."""
        output = run_hook({"tool_name": ""})
        context = get_context(output)
        assert context == ""

    def test_tool_name_with_other_fields(self):
        """Task tool with other fields should still trigger reminder."""
        output = run_hook({
            "tool_name": "Task",
            "tool_input": {"prompt": "test"},
            "tool_result": "completed"
        })
        context = get_context(output)
        assert "Verification Required" in context


class TestAgentSessionSkip:
    """Tests for agent sessions skipping verification reminder."""

    def test_agent_session_skips_task_reminder(self):
        """Agent sessions should skip verification reminder for Task tool."""
        output = run_hook({
            "tool_name": "Task",
            "agent_type": "oh-my-claude:critic",
            "session_id": "agent-test",
        })
        context = get_context(output)
        assert context == ""

    def test_no_agent_type_still_triggers(self):
        """Regular sessions without agent_type should still get reminder."""
        output = run_hook({
            "tool_name": "Task",
            "session_id": "agent-test",
        })
        context = get_context(output)
        assert "Verification Required" in context
