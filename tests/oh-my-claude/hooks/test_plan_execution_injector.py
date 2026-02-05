"""Tests for plan_execution_injector.py PostToolUse hook."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "plugins/oh-my-claude/hooks/plan_execution_injector.py"
)


def run_hook(input_data: dict, env: dict | None = None) -> dict:
    """Run the hook with given input and return parsed output.

    Args:
        input_data: Hook input payload.
        env: Optional environment dict for subprocess. If None, inherits current env.
    """
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


class TestExecutionContext:
    """Tests for execution context injection."""

    def test_context_when_no_tool_input(self):
        """PostToolUse without tool_input returns execution context."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "READY FOR EXECUTION" in context

    def test_context_includes_agent_table(self):
        """Execution context should include agent delegation table."""
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

    def test_context_includes_plan_compliance(self):
        """Execution context should include plan compliance section."""
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {},
        }
        result = run_hook(input_data)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "PLAN COMPLIANCE" in context
        assert "STATE TRACKING" in context


class TestAgentTeamsContext:
    """Tests for Agent Teams section based on env var."""

    def _base_env(self) -> dict:
        """Base env dict with required PATH for subprocess."""
        return {
            "HOME": os.environ.get("HOME", "/tmp"),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        }

    def test_agent_teams_section_when_env_enabled(self):
        """Agent Teams section appears when env var is set to '1'."""
        env = self._base_env()
        env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {},
        }
        result = run_hook(input_data, env=env)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "AGENT TEAMS (Available)" in context
        assert "READY FOR EXECUTION" in context

    def test_agent_teams_section_when_env_true(self):
        """Agent Teams section appears when env var is set to 'true'."""
        env = self._base_env()
        env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "true"
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {},
        }
        result = run_hook(input_data, env=env)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "AGENT TEAMS (Available)" in context

    def test_no_agent_teams_when_env_disabled(self):
        """No Agent Teams section when env var is absent."""
        env = self._base_env()
        # Explicitly do NOT include CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {},
        }
        result = run_hook(input_data, env=env)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "AGENT TEAMS" not in context
        assert "READY FOR EXECUTION" in context

    def test_no_agent_teams_when_env_zero(self):
        """No Agent Teams section when env var is '0'."""
        env = self._base_env()
        env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "0"
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {},
        }
        result = run_hook(input_data, env=env)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "AGENT TEAMS" not in context

    def test_no_fake_teammatetool_references(self):
        """Ensure no fake TeammateTool API references exist."""
        env = self._base_env()
        env["CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"] = "1"
        input_data = {
            "tool_name": "ExitPlanMode",
            "tool_result": {},
            "tool_input": {},
        }
        result = run_hook(input_data, env=env)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        for fake_ref in ["TeammateTool", "spawnTeam", "discoverTeams", "requestJoin", "launchSwarm"]:
            assert fake_ref not in context, f"Found fake API reference: {fake_ref}"


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
            "tool_input": {},
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
        # Should return execution context (default when no tool_input)
        context = result.get("hookSpecificOutput", {}).get("additionalContext", "")
        assert "READY FOR EXECUTION" in context
