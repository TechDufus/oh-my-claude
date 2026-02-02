"""Tests for agent_usage_reminder.py PostToolUse hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/agent_usage_reminder.py"


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


class TestGrepTriggersReminder:
    """Tests for Grep tool triggering agent usage reminder."""

    def test_grep_triggers_reminder(self):
        """When tool_name is Grep, should output reminder context."""
        output = run_hook({"tool_name": "Grep", "session_id": "test-grep-1"})
        context = get_context(output)
        assert "Agent Usage Reminder" in context

    def test_grep_includes_scout_suggestion(self):
        """Reminder should suggest using scout agent for Grep."""
        output = run_hook({"tool_name": "Grep", "session_id": "test-grep-2"})
        context = get_context(output)
        assert "Explore" in context

    def test_grep_mentions_benefits(self):
        """Reminder should mention benefits of agent delegation."""
        output = run_hook({"tool_name": "Grep", "session_id": "test-grep-3"})
        context = get_context(output)
        assert "Parallel execution" in context
        assert "context protection" in context

    def test_grep_with_session_id(self):
        """Grep with session_id should trigger reminder."""
        output = run_hook({"tool_name": "Grep", "session_id": "session-123"})
        context = get_context(output)
        assert "Agent Usage Reminder" in context


class TestGlobTriggersReminder:
    """Tests for Glob tool triggering agent usage reminder."""

    def test_glob_triggers_reminder(self):
        """When tool_name is Glob, should output reminder context."""
        output = run_hook({"tool_name": "Glob", "session_id": "test-glob-1"})
        context = get_context(output)
        assert "Agent Usage Reminder" in context

    def test_glob_includes_scout_suggestion(self):
        """Reminder should suggest using scout agent for Glob."""
        output = run_hook({"tool_name": "Glob", "session_id": "test-glob-2"})
        context = get_context(output)
        assert "Explore" in context

    def test_glob_mentions_benefits(self):
        """Reminder should mention benefits of agent delegation."""
        output = run_hook({"tool_name": "Glob", "session_id": "test-glob-3"})
        context = get_context(output)
        assert "Parallel execution" in context
        assert "context protection" in context

    def test_glob_with_session_id(self):
        """Glob with session_id should trigger reminder."""
        output = run_hook({"tool_name": "Glob", "session_id": "session-456"})
        context = get_context(output)
        assert "Agent Usage Reminder" in context


class TestTaskSuppressesReminder:
    """Tests for Task tool marking session as agent-user (no reminder)."""

    def test_task_tool_no_output(self):
        """Task tool should return empty output (marks session as agent-user)."""
        output = run_hook({"tool_name": "Task", "session_id": "test-task-1"})
        context = get_context(output)
        assert context == ""

    def test_task_tool_empty_response(self):
        """Task tool should not include reminder message."""
        output = run_hook({"tool_name": "Task", "session_id": "test-task-2"})
        context = get_context(output)
        assert "Agent Usage Reminder" not in context

    def test_task_with_additional_fields(self):
        """Task tool with other fields should still suppress reminder."""
        output = run_hook({
            "tool_name": "Task",
            "session_id": "test-task-3",
            "tool_input": {"prompt": "test prompt"},
            "tool_result": "completed"
        })
        context = get_context(output)
        assert context == ""


class TestSessionTracking:
    """Tests for session tracking behavior."""

    def test_different_sessions_handled(self):
        """Different session IDs should be tracked independently."""
        output1 = run_hook({"tool_name": "Grep", "session_id": "session-a"})
        output2 = run_hook({"tool_name": "Grep", "session_id": "session-b"})
        # Each subprocess is isolated, so both should get reminder
        assert "Agent Usage Reminder" in get_context(output1)
        assert "Agent Usage Reminder" in get_context(output2)

    def test_session_id_unknown_default(self):
        """Missing session_id should default to 'unknown'."""
        output = run_hook({"tool_name": "Grep"})
        context = get_context(output)
        assert "Agent Usage Reminder" in context

    def test_session_id_with_grep(self):
        """Session ID is processed correctly with Grep tool."""
        output = run_hook({"tool_name": "Grep", "session_id": "unique-session-1"})
        context = get_context(output)
        assert "Agent Usage Reminder" in context

    def test_session_id_with_glob(self):
        """Session ID is processed correctly with Glob tool."""
        output = run_hook({"tool_name": "Glob", "session_id": "unique-session-2"})
        context = get_context(output)
        assert "Agent Usage Reminder" in context

    def test_empty_session_id(self):
        """Empty session_id should still allow hook to function."""
        output = run_hook({"tool_name": "Grep", "session_id": ""})
        context = get_context(output)
        assert "Agent Usage Reminder" in context


class TestOtherToolsNoReminder:
    """Tests for other tools not triggering reminder."""

    def test_read_tool_no_output(self):
        """Read tool should return empty output."""
        output = run_hook({"tool_name": "Read", "session_id": "test-read"})
        context = get_context(output)
        assert context == ""

    def test_bash_tool_no_output(self):
        """Bash tool should return empty output."""
        output = run_hook({"tool_name": "Bash", "session_id": "test-bash"})
        context = get_context(output)
        assert context == ""

    def test_edit_tool_no_output(self):
        """Edit tool should return empty output."""
        output = run_hook({"tool_name": "Edit", "session_id": "test-edit"})
        context = get_context(output)
        assert context == ""

    def test_write_tool_no_output(self):
        """Write tool should return empty output."""
        output = run_hook({"tool_name": "Write", "session_id": "test-write"})
        context = get_context(output)
        assert context == ""

    def test_todowrite_tool_no_output(self):
        """TodoWrite tool should return empty output."""
        output = run_hook({"tool_name": "TodoWrite", "session_id": "test-todo"})
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
        """Grep tool with other fields should still trigger reminder."""
        output = run_hook({
            "tool_name": "Grep",
            "session_id": "test-other-fields",
            "tool_input": {"pattern": "test"},
            "tool_result": "found matches"
        })
        context = get_context(output)
        assert "Agent Usage Reminder" in context

    def test_only_session_id_no_tool(self):
        """Only session_id without tool_name should return empty."""
        output = run_hook({"session_id": "lonely-session"})
        context = get_context(output)
        assert context == ""
