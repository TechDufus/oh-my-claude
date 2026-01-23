"""Tests for task_delegation_enforcer.py PreToolUse hook."""

import pytest

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
