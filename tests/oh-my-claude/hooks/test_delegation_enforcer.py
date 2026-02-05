"""Tests for delegation_enforcer.py hook."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from delegation_enforcer import (
    DELEGATION_REMINDER,
    DIRECT_MARKER,
    EXECUTION_MARKERS,
    SHORT_CHANGE_THRESHOLD,
    has_direct_marker,
    is_execution_mode,
    is_short_change,
)

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/delegation_enforcer.py"


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


# =============================================================================
# Unit Tests: has_direct_marker
# =============================================================================


class TestHasDirectMarker:
    """Tests for has_direct_marker function."""

    def test_finds_marker_in_old_string(self):
        """Should find [direct] in old_string field."""
        assert has_direct_marker({"old_string": "some code [direct]"}) is True

    def test_finds_marker_in_new_string(self):
        """Should find [direct] in new_string field."""
        assert has_direct_marker({"new_string": "[direct] new code"}) is True

    def test_finds_marker_in_content(self):
        """Should find [direct] in content field."""
        assert has_direct_marker({"content": "writing [direct] content"}) is True

    def test_finds_marker_in_file_path(self):
        """Should find [direct] in file_path field."""
        assert has_direct_marker({"file_path": "/path/[direct]/file.py"}) is True

    def test_case_insensitive(self):
        """Should match [DIRECT] case-insensitively."""
        assert has_direct_marker({"new_string": "[DIRECT] code"}) is True
        assert has_direct_marker({"new_string": "[Direct] code"}) is True
        assert has_direct_marker({"new_string": "[dIrEcT] code"}) is True

    def test_returns_false_when_absent(self):
        """Should return False when no marker is present."""
        assert has_direct_marker({"new_string": "normal code change"}) is False

    def test_returns_false_for_empty_dict(self):
        """Should return False for empty tool input."""
        assert has_direct_marker({}) is False

    def test_returns_false_for_non_string_values(self):
        """Should handle non-string values gracefully."""
        assert has_direct_marker({"new_string": 42}) is False
        assert has_direct_marker({"content": None}) is False
        assert has_direct_marker({"old_string": ["list"]}) is False


# =============================================================================
# Unit Tests: is_short_change
# =============================================================================


class TestIsShortChange:
    """Tests for is_short_change function."""

    def test_short_new_string(self):
        """Should return True for new_string under threshold."""
        lines = "\n".join(f"line {i}" for i in range(5))
        assert is_short_change({"new_string": lines}) is True

    def test_long_new_string(self):
        """Should return False for new_string at or over threshold."""
        lines = "\n".join(f"line {i}" for i in range(SHORT_CHANGE_THRESHOLD))
        assert is_short_change({"new_string": lines}) is False

    def test_short_content_write_tool(self):
        """Should return True for short content (Write tool)."""
        content = "short file\nwith a few lines"
        assert is_short_change({"content": content}) is True

    def test_long_content_write_tool(self):
        """Should return False for long content (Write tool)."""
        content = "\n".join(f"line {i}" for i in range(SHORT_CHANGE_THRESHOLD))
        assert is_short_change({"content": content}) is False

    def test_returns_false_no_new_string_or_content(self):
        """Should return False when neither new_string nor content present."""
        assert is_short_change({}) is False
        assert is_short_change({"old_string": "something"}) is False

    def test_empty_new_string(self):
        """Empty new_string (falsy) should return False."""
        assert is_short_change({"new_string": ""}) is False

    def test_single_line_is_short(self):
        """A single line should be short."""
        assert is_short_change({"new_string": "one line"}) is True

    def test_exactly_threshold_minus_one(self):
        """Exactly threshold-1 lines should be short."""
        lines = "\n".join(f"line {i}" for i in range(SHORT_CHANGE_THRESHOLD - 1))
        assert is_short_change({"new_string": lines}) is True

    def test_new_string_takes_precedence(self):
        """When new_string is present and short, content is not checked."""
        short_new = "short"
        long_content = "\n".join(f"line {i}" for i in range(50))
        assert is_short_change({"new_string": short_new, "content": long_content}) is True


# =============================================================================
# Unit Tests: is_execution_mode
# =============================================================================


class TestIsExecutionMode:
    """Tests for is_execution_mode function."""

    @pytest.mark.parametrize("marker", EXECUTION_MARKERS)
    def test_detects_each_execution_marker(self, marker):
        """Each EXECUTION_MARKERS keyword should be detected."""
        data = {"prompt": f"here is the {marker} command"}
        assert is_execution_mode(data) is True

    def test_detects_marker_in_transcript(self):
        """Should detect markers in the transcript field."""
        data = {"transcript": "starting plan execution now"}
        assert is_execution_mode(data) is True

    def test_detects_tasklist_reference(self):
        """Should detect tasklist references as execution mode."""
        data = {"prompt": "check the tasklist for next items"}
        assert is_execution_mode(data) is True

    def test_detects_pending_task_reference(self):
        """Should detect pending task references as execution mode."""
        data = {"prompt": "there is a pending task to complete"}
        assert is_execution_mode(data) is True

    def test_returns_false_for_normal_mode(self):
        """Should return False for prompts without execution markers."""
        data = {"prompt": "please help me fix a bug"}
        assert is_execution_mode(data) is False

    def test_returns_false_for_empty_data(self):
        """Should return False for empty data."""
        assert is_execution_mode({}) is False

    def test_case_insensitive_detection(self):
        """Markers should match case-insensitively (prompt is lowered)."""
        data = {"prompt": "running ULTRAWORK mode now"}
        assert is_execution_mode(data) is True

    def test_combined_transcript_and_prompt(self):
        """Should check both transcript and prompt fields."""
        # Marker only in transcript
        data = {"transcript": "ulw detected", "prompt": "normal prompt"}
        assert is_execution_mode(data) is True

        # Marker only in prompt
        data = {"transcript": "normal context", "prompt": "ulw fix bugs"}
        assert is_execution_mode(data) is True


# =============================================================================
# Integration Tests: main function via subprocess
# =============================================================================


class TestMainIntegration:
    """Integration tests for the main hook function via subprocess."""

    def test_passes_through_non_edit_write_tools(self):
        """Non-Edit/Write tools should pass through with no output."""
        output = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "ls"},
        })
        assert output == {}

    def test_passes_through_read_tool(self):
        """Read tool should pass through."""
        output = run_hook({
            "tool_name": "Read",
            "tool_input": {"file_path": "/some/file"},
        })
        assert output == {}

    def test_skips_when_direct_marker_found(self):
        """Should skip reminder when [DIRECT] marker is present."""
        output = run_hook({
            "tool_name": "Edit",
            "tool_input": {
                "new_string": "[DIRECT] large change\n" * 30,
            },
            "prompt": "ultrawork fix all the bugs",
        })
        assert output == {}

    def test_skips_for_short_changes(self):
        """Should skip reminder for short changes even in execution mode."""
        output = run_hook({
            "tool_name": "Edit",
            "tool_input": {"new_string": "one line fix"},
            "prompt": "ultrawork fix bugs",
        })
        assert output == {}

    def test_skips_when_not_execution_mode(self):
        """Should skip reminder when not in execution mode."""
        long_content = "\n".join(f"line {i}" for i in range(30))
        output = run_hook({
            "tool_name": "Edit",
            "tool_input": {"new_string": long_content},
            "prompt": "please help me fix a bug",
        })
        assert output == {}

    def test_outputs_reminder_when_all_conditions_met(self):
        """Should output delegation reminder when all conditions are met."""
        long_content = "\n".join(f"line {i}" for i in range(30))
        output = run_hook({
            "tool_name": "Edit",
            "tool_input": {"new_string": long_content},
            "prompt": "ultrawork implement the feature",
        })
        context = get_context(output)
        assert "DELEGATION REMINDER" in context

    def test_reminder_for_write_tool(self):
        """Should also trigger for Write tool with long content in execution mode."""
        long_content = "\n".join(f"line {i}" for i in range(30))
        output = run_hook({
            "tool_name": "Write",
            "tool_input": {"content": long_content},
            "prompt": "plan execution in progress",
        })
        context = get_context(output)
        assert "DELEGATION REMINDER" in context

    def test_empty_input(self):
        """Should handle empty input gracefully."""
        output = run_hook({})
        assert output == {}

    def test_malformed_tool_input(self):
        """Should handle missing tool_input gracefully."""
        output = run_hook({
            "tool_name": "Edit",
        })
        assert output == {}
