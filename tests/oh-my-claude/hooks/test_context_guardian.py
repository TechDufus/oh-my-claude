"""Tests for context_guardian.py SessionStart hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/context_guardian.py"


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


class TestMainSessionBehavior:
    """Tests for main session (no agent_type) behavior."""

    def test_main_session_gets_sop(self):
        """Main session should receive full SOP context."""
        output = run_hook({})
        context = get_context(output)
        assert "Context Protection ACTIVE" in context

    def test_main_session_includes_specialized_agents(self):
        """SOP should include specialized agents instructions."""
        output = run_hook({})
        context = get_context(output)
        assert "advisor" in context
        assert "librarian" in context
        assert "validator" in context

    def test_main_session_includes_file_protocol(self):
        """SOP should include delegation protocol."""
        output = run_hook({})
        context = get_context(output)
        assert "Delegation Protocol" in context

    def test_empty_input_treated_as_main_session(self):
        """Empty input should be treated as main session."""
        output = run_hook({})
        context = get_context(output)
        assert len(context) > 100  # SOP is substantial


class TestSubagentBehavior:
    """Tests for subagent (agent_type set) behavior."""

    def test_subagent_skips_sop(self):
        """Subagents should not receive SOP."""
        output = run_hook({"agent_type": "librarian"})
        context = get_context(output)
        assert context == ""

    def test_scout_agent_skips_sop(self):
        """Scout agent should skip SOP."""
        output = run_hook({"agent_type": "scout"})
        context = get_context(output)
        assert "Context Protection ACTIVE" not in context

    def test_worker_agent_skips_sop(self):
        """Worker agent should skip SOP."""
        output = run_hook({"agent_type": "worker"})
        context = get_context(output)
        assert "Context Protection ACTIVE" not in context

    def test_validator_agent_skips_sop(self):
        """Validator agent should skip SOP."""
        output = run_hook({"agent_type": "validator"})
        context = get_context(output)
        assert "Context Protection ACTIVE" not in context

    def test_architect_agent_skips_sop(self):
        """Architect agent should skip SOP."""
        output = run_hook({"agent_type": "architect"})
        context = get_context(output)
        assert "Context Protection ACTIVE" not in context

    def test_scribe_agent_skips_sop(self):
        """Scribe agent should skip SOP."""
        output = run_hook({"agent_type": "scribe"})
        context = get_context(output)
        assert "Context Protection ACTIVE" not in context

    def test_custom_agent_type_skips_sop(self):
        """Any agent_type value should skip SOP."""
        output = run_hook({"agent_type": "custom-agent"})
        context = get_context(output)
        assert "Context Protection ACTIVE" not in context


class TestEdgeCases:
    """Edge case tests."""

    def test_null_agent_type_treated_as_main(self):
        """Explicit null agent_type should be treated as main session."""
        output = run_hook({"agent_type": None})
        context = get_context(output)
        assert "Context Protection ACTIVE" in context

    def test_empty_string_agent_type_treated_as_main(self):
        """Empty string agent_type should be treated as main session."""
        output = run_hook({"agent_type": ""})
        context = get_context(output)
        # Empty string is falsy, so treated as main session
        assert "Context Protection ACTIVE" in context

    def test_other_fields_dont_affect_detection(self):
        """Other input fields shouldn't affect agent_type detection."""
        output = run_hook({
            "session_id": "test-123",
            "cwd": "/some/path",
            "other_field": "value"
        })
        context = get_context(output)
        # No agent_type, so main session
        assert "Context Protection ACTIVE" in context

    def test_agent_type_with_other_fields(self):
        """agent_type detection works with other fields present."""
        output = run_hook({
            "session_id": "test-123",
            "agent_type": "librarian",
            "cwd": "/some/path"
        })
        context = get_context(output)
        assert "Context Protection ACTIVE" not in context
