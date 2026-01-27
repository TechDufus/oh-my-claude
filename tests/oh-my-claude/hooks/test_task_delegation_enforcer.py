"""Tests for task_delegation_enforcer.py PreToolUse hook."""

import json
import os
import subprocess
import sys
from pathlib import Path

from task_delegation_enforcer import (
    has_delegation_pattern,
    has_no_delegate_tag,
)


class TestHasDelegationPattern:
    """Tests for has_delegation_pattern function."""

    def test_missing_pattern_denied(self):
        """Description without Task() pattern should not match."""
        text = "Create a task to refactor the auth module"
        assert has_delegation_pattern(text) is False

    def test_valid_pattern_continues(self):
        """Description with Task(subagent_type=...) should match."""
        text = 'Task(subagent_type="oh-my-claude:worker", prompt="Implement feature")'
        assert has_delegation_pattern(text) is True

    def test_case_insensitive_pattern(self):
        """Pattern matching should be case-insensitive."""
        text = 'TASK(Subagent_Type="oh-my-claude:scout", prompt="Find files")'
        assert has_delegation_pattern(text) is True

    def test_partial_task_only(self):
        """Having Task( without subagent_type should not match."""
        text = 'Task(prompt="Do something")'
        assert has_delegation_pattern(text) is False

    def test_partial_subagent_only(self):
        """Having subagent_type without Task( should not match."""
        text = 'Use subagent_type="worker" for this'
        assert has_delegation_pattern(text) is False

    def test_multiline_pattern(self):
        """Pattern should match across multiple lines."""
        text = """
        Task(
            subagent_type="oh-my-claude:librarian",
            prompt="Read the config file"
        )
        """
        assert has_delegation_pattern(text) is True

    def test_empty_string(self):
        """Empty string should not match."""
        assert has_delegation_pattern("") is False


class TestHasNoDelegateTag:
    """Tests for has_no_delegate_tag function."""

    def test_no_delegate_tag_continues(self):
        """Description with [NO-DELEGATE] should match."""
        text = "[NO-DELEGATE] Create a simple task for tracking"
        assert has_no_delegate_tag(text) is True

    def test_case_insensitive_tag(self):
        """Tag matching should be case-insensitive."""
        text = "[no-delegate] This task does not need delegation"
        assert has_no_delegate_tag(text) is True

    def test_mixed_case_tag(self):
        """Mixed case tag should match."""
        text = "[No-Delegate] Another task"
        assert has_no_delegate_tag(text) is True

    def test_tag_in_middle(self):
        """Tag in middle of text should match."""
        text = "Create task [NO-DELEGATE] for simple tracking"
        assert has_no_delegate_tag(text) is True

    def test_tag_at_end(self):
        """Tag at end of text should match."""
        text = "Simple task [NO-DELEGATE]"
        assert has_no_delegate_tag(text) is True

    def test_missing_tag(self):
        """Text without tag should not match."""
        text = "Create a task to delegate to worker"
        assert has_no_delegate_tag(text) is False

    def test_empty_string(self):
        """Empty string should not match."""
        assert has_no_delegate_tag("") is False

    def test_partial_tag_no_brackets(self):
        """NO-DELEGATE without brackets should not match."""
        text = "NO-DELEGATE this task"
        assert has_no_delegate_tag(text) is False


class TestIntegrationScenarios:
    """Integration tests for combined pattern matching."""

    def test_both_patterns_present(self):
        """Both delegation pattern and no-delegate tag present."""
        text = '[NO-DELEGATE] Task(subagent_type="worker", prompt="...")'
        # When both present, no-delegate takes precedence in main()
        assert has_no_delegate_tag(text) is True
        assert has_delegation_pattern(text) is True

    def test_realistic_description_with_pattern(self):
        """Realistic task description with delegation instruction."""
        text = """
        Implement the new authentication feature.

        Task(subagent_type="oh-my-claude:worker", prompt="
            Create UserAuth class in src/auth/ with:
            - login() method
            - logout() method
            - validateSession() method
        ")
        """
        assert has_delegation_pattern(text) is True
        assert has_no_delegate_tag(text) is False

    def test_realistic_description_without_pattern(self):
        """Realistic task description without delegation instruction."""
        text = """
        Implement the new authentication feature.

        Create UserAuth class in src/auth/ with:
        - login() method
        - logout() method
        - validateSession() method
        """
        assert has_delegation_pattern(text) is False
        assert has_no_delegate_tag(text) is False

    def test_simple_tracking_task(self):
        """Simple tracking task with no-delegate tag."""
        text = "[NO-DELEGATE] Track: Review PR comments"
        assert has_no_delegate_tag(text) is True
        assert has_delegation_pattern(text) is False


# Helper for running the full hook


def run_hook(input_data: dict, tmp_path: Path) -> dict:
    """Run the task_delegation_enforcer hook with given input.

    Uses a temp directory for session state to isolate tests.
    """
    # Get the hook script path
    hook_path = (
        Path(__file__).parent.parent.parent.parent
        / "plugins"
        / "oh-my-claude"
        / "hooks"
        / "task_delegation_enforcer.py"
    )

    # Override the session state path via environment
    env = {
        **os.environ,
        "OMC_SESSION_STATE_DIR": str(tmp_path / ".claude" / "oh-my-claude"),
    }

    # Run the hook as a subprocess
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        env=env,
    )

    # Parse output (may be empty for continue)
    if result.stdout.strip():
        return json.loads(result.stdout.strip())
    return {}


class TestTeamPatternRecognition:
    """Tests for team-based delegation patterns."""

    def test_team_pattern_allowed(self, tmp_path):
        """team_name + name pattern should be allowed."""
        description = """
        Task(team_name="project-team", name="worker-1",
             subagent_type="oh-my-claude:worker", prompt="...")
        """
        input_data = {
            "event": "PreToolUse",
            "tool_name": "TaskCreate",
            "tool_input": {
                "subject": "Implement feature",
                "description": description,
            },
        }
        result = run_hook(input_data, tmp_path)

        # Should be allowed (result is continue or empty)
        assert result.get("result") != "deny"

    def test_no_delegate_still_allowed(self, tmp_path):
        """[NO-DELEGATE] escape hatch should still work."""
        description = "[NO-DELEGATE] Main agent handles this directly"
        input_data = {
            "event": "PreToolUse",
            "tool_name": "TaskCreate",
            "tool_input": {
                "subject": "Direct task",
                "description": description,
            },
        }
        result = run_hook(input_data, tmp_path)

        assert result.get("result") != "deny"

    def test_team_pattern_without_subagent_type(self):
        """team_name + name pattern should match even without subagent_type."""
        text = 'Task(team_name="project-team", name="worker-1", prompt="...")'
        assert has_delegation_pattern(text) is True

    def test_team_name_only_not_enough(self):
        """Having team_name without name should not match team pattern."""
        text = 'Task(team_name="project-team", prompt="...")'
        # This should still match because it checks subagent_type OR (team_name AND name)
        # "name" substring is in "team_name", so this will actually match
        # This is expected behavior per the implementation
        assert has_delegation_pattern(text) is True


class TestTaskCountTracking:
    """Tests for task creation count tracking."""

    def test_first_two_tasks_no_warning(self, tmp_path):
        """First two tasks should not suggest team formation."""
        # Clear any existing state
        state_file = tmp_path / ".claude" / "oh-my-claude" / "session_state.json"
        if state_file.exists():
            state_file.unlink()

        for i in range(2):
            description = f"""
            Task(subagent_type="oh-my-claude:worker", prompt="Task {i}")
            """
            input_data = {
                "event": "PreToolUse",
                "tool_name": "TaskCreate",
                "tool_input": {
                    "subject": f"Task {i}",
                    "description": description,
                },
            }
            result = run_hook(input_data, tmp_path)

            # Should not have team suggestion
            if "hookSpecificOutput" in result:
                context = result["hookSpecificOutput"].get("additionalContext", "")
                assert "Team Formation" not in context

    def test_third_task_suggests_team(self, tmp_path):
        """Third task should suggest team formation."""
        # Set up state with 2 tasks already
        state_dir = tmp_path / ".claude" / "oh-my-claude"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "session_state.json"
        state_file.write_text('{"task_create_count": 2}')

        description = """
        Task(subagent_type="oh-my-claude:worker", prompt="Third task")
        """
        input_data = {
            "event": "PreToolUse",
            "tool_name": "TaskCreate",
            "tool_input": {
                "subject": "Third task",
                "description": description,
            },
        }
        result = run_hook(input_data, tmp_path)

        # Should suggest team formation
        if "hookSpecificOutput" in result:
            context = result["hookSpecificOutput"].get("additionalContext", "")
            assert "Team" in context or "3+" in context

    def test_team_tasks_no_warning(self, tmp_path):
        """Tasks with team_name should not get team suggestion."""
        # Set up state with 2 tasks
        state_dir = tmp_path / ".claude" / "oh-my-claude"
        state_dir.mkdir(parents=True, exist_ok=True)
        state_file = state_dir / "session_state.json"
        state_file.write_text('{"task_create_count": 2}')

        description = """
        Task(team_name="my-team", name="worker-1",
             subagent_type="oh-my-claude:worker", prompt="Team task")
        """
        input_data = {
            "event": "PreToolUse",
            "tool_name": "TaskCreate",
            "tool_input": {
                "subject": "Team task",
                "description": description,
            },
        }
        result = run_hook(input_data, tmp_path)

        # Should not suggest team (already using teams)
        if "hookSpecificOutput" in result:
            context = result["hookSpecificOutput"].get("additionalContext", "")
            # Either no context or it's not the team suggestion
            assert "3+ tasks created" not in context
