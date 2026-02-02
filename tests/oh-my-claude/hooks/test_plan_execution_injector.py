"""Tests for plan_execution_injector.py PostToolUse hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "plugins/oh-my-claude/hooks/plan_execution_injector.py"
)


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


class TestSwarmExecutionContext:
    """Tests for swarm execution context injection."""

    def test_swarm_context_when_launch_swarm_true(self):
        """PostToolUse with launchSwarm=true returns swarm context."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {"launchSwarm": True, "teammateCount": 3},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "SWARM EXECUTION ACTIVE" in context
        assert "3 parallel workers" in context

    def test_swarm_context_with_different_teammate_count(self):
        """Swarm context should reflect actual teammate count."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {"launchSwarm": True, "teammateCount": 5},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "5 parallel workers" in context

    def test_swarm_context_includes_coordination_protocol(self):
        """Swarm context should include coordination guidance."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {"launchSwarm": True, "teammateCount": 3},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "SWARM COORDINATION PROTOCOL" in context
        assert "TaskList" in context


class TestManualExecutionContext:
    """Tests for manual execution context injection."""

    def test_manual_context_when_no_swarm(self):
        """PostToolUse without launchSwarm returns manual context."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "READY FOR EXECUTION" in context

    def test_manual_context_when_launch_swarm_false(self):
        """Explicit launchSwarm=false returns manual context."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {"launchSwarm": False},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "READY FOR EXECUTION" in context

    def test_manual_context_when_teammate_count_zero(self):
        """launchSwarm=true but teammateCount=0 returns manual context."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {"launchSwarm": True, "teammateCount": 0},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "READY FOR EXECUTION" in context

    def test_manual_context_includes_agent_table(self):
        """Manual context should include agent delegation table."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "AGENT DELEGATION TABLE" in context
        assert "Explore" in context
        assert "general-purpose" in context


class TestPreToolUseIgnored:
    """Tests for PreToolUse/PermissionRequest handling."""

    def test_pretooluse_returns_empty(self):
        """PreToolUse (no tool_result) returns empty output."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_input": {},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert context == ""

    def test_permission_request_returns_empty(self):
        """PermissionRequest (no tool_result) returns empty output."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_input": {"launchSwarm": True, "teammateCount": 3},
            # No tool_result - this is PermissionRequest phase
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert context == ""


class TestEmptyInput:
    """Tests for graceful handling of empty/malformed input."""

    def test_empty_dict_returns_empty(self):
        """Empty input dict should return empty output."""
        result = run_hook({})
        assert result == {} or result.get("hookSpecificOutput", {}).get("additionalContext", "") == ""

    def test_no_crash_on_empty_input(self):
        """Hook should exit cleanly on empty input."""
        # Should not raise
        run_hook({})

    def test_no_crash_on_missing_tool_input(self):
        """Hook should handle missing tool_input gracefully."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            # No tool_input key
        }
        result = run_hook(input_data)
        # Should return manual context (default when no swarm params)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "READY FOR EXECUTION" in context
