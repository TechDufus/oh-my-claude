"""Tests for precompact_context.py PreCompact hook."""

import json
import subprocess
import sys
from pathlib import Path
import pytest

HOOK_PATH = Path(__file__).parent.parent.parent.parent / "plugins/oh-my-claude/hooks/precompact_context.py"

# Add hooks directory to path for direct imports
sys.path.insert(0, str(HOOK_PATH.parent))

from precompact_context import detect_mode, format_context, get_git_state


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
    """Extract systemMessage from hook output."""
    return output.get("systemMessage", "")


class TestGetGitState:
    """Tests for get_git_state function."""

    def test_get_git_state_returns_branch(self):
        """Git state includes current branch."""
        # Run in current repo which is a git repo
        state = get_git_state()
        assert "branch" in state
        assert isinstance(state["branch"], str)
        assert len(state["branch"]) > 0

    def test_get_git_state_handles_error(self):
        """Graceful degradation if git fails."""
        # Use a non-existent directory to trigger git failure
        state = get_git_state("/nonexistent/path/that/does/not/exist")
        assert state["branch"] == "unknown"
        assert state["uncommitted_changes"] is False
        assert state["staged_files"] == []


class TestDetectMode:
    """Tests for detect_mode function."""

    def test_detect_mode_finds_ultrawork(self):
        """Mode detection catches ultrawork keyword."""
        data = {"session_context": "This is an ultrawork session"}
        assert detect_mode(data) == "ultrawork"

    def test_detect_mode_finds_ulw(self):
        """Mode detection catches ulw shortcut."""
        data = {"session_context": "Running in ulw mode"}
        assert detect_mode(data) == "ultrawork"

    def test_detect_mode_defaults_normal(self):
        """Mode defaults to normal when no keywords found."""
        data = {"session_context": "Just a regular session"}
        assert detect_mode(data) == "normal"

    def test_detect_mode_empty_context(self):
        """Mode defaults to normal with empty session_context."""
        data = {"session_context": ""}
        assert detect_mode(data) == "normal"

    def test_detect_mode_missing_context(self):
        """Mode defaults to normal when session_context missing."""
        data = {}
        assert detect_mode(data) == "normal"

    def test_detect_mode_case_insensitive(self):
        """Mode detection is case insensitive."""
        data = {"session_context": "ULTRAWORK MODE"}
        assert detect_mode(data) == "ultrawork"


class TestFormatContext:
    """Tests for format_context function."""

    def test_format_context_includes_mode(self):
        """Formatted context shows mode."""
        git_state = {"branch": "main", "uncommitted_changes": False, "staged_files": []}
        context = format_context(
            mode="ultrawork",
            git_state=git_state,
            recent_files=[],
            todos=[],
            timestamp="2024-01-01T00:00:00Z"
        )
        assert "Mode: ultrawork" in context

    def test_format_context_handles_empty_todos(self):
        """Empty todos render gracefully."""
        git_state = {"branch": "main", "uncommitted_changes": False, "staged_files": []}
        context = format_context(
            mode="normal",
            git_state=git_state,
            recent_files=["file.py"],
            todos=[],
            timestamp="2024-01-01T00:00:00Z"
        )
        assert "### Active Todos" in context
        assert "(none)" in context

    def test_format_context_handles_empty_files(self):
        """Empty files list renders gracefully."""
        git_state = {"branch": "main", "uncommitted_changes": False, "staged_files": []}
        context = format_context(
            mode="normal",
            git_state=git_state,
            recent_files=[],
            todos=[],
            timestamp="2024-01-01T00:00:00Z"
        )
        assert "### Recent Files Modified" in context
        assert "(none)" in context

    def test_format_context_includes_branch(self):
        """Formatted context includes branch name."""
        git_state = {"branch": "feature-test", "uncommitted_changes": True, "staged_files": ["a.py"]}
        context = format_context(
            mode="normal",
            git_state=git_state,
            recent_files=[],
            todos=[],
            timestamp="2024-01-01T00:00:00Z"
        )
        assert "Branch: feature-test" in context

    def test_format_context_shows_uncommitted_changes(self):
        """Formatted context shows uncommitted changes status."""
        git_state = {"branch": "main", "uncommitted_changes": True, "staged_files": []}
        context = format_context(
            mode="normal",
            git_state=git_state,
            recent_files=[],
            todos=[],
            timestamp="2024-01-01T00:00:00Z"
        )
        assert "Uncommitted Changes: Yes" in context

    def test_format_context_shows_todos(self):
        """Formatted context includes todos when present."""
        git_state = {"branch": "main", "uncommitted_changes": False, "staged_files": []}
        todos = [
            {"status": "pending", "content": "Fix the bug"},
            {"status": "complete", "content": "Write tests"}
        ]
        context = format_context(
            mode="normal",
            git_state=git_state,
            recent_files=[],
            todos=todos,
            timestamp="2024-01-01T00:00:00Z"
        )
        assert "[pending] Fix the bug" in context
        assert "[complete] Write tests" in context


class TestHookIntegration:
    """Integration tests for full hook execution."""

    def test_hook_outputs_context(self):
        """Full hook execution produces valid output."""
        output = run_hook({
            "session_context": "ultrawork mode",
            "cwd": str(Path.cwd())
        })
        context = get_context(output)

        # Should contain context preservation markers
        assert "<context-preservation" in context
        assert "</context-preservation>" in context

        # Should contain key sections
        assert "## Session State Preserved" in context
        assert "Mode:" in context
        assert "Branch:" in context
        assert "### Recent Files Modified" in context
        assert "### Active Todos" in context

        # Should contain the important note
        assert "IMPORTANT:" in context

    def test_hook_handles_empty_input(self):
        """Hook handles empty input gracefully."""
        output = run_hook({})
        context = get_context(output)
        # Empty dict returns empty output (no data to preserve)
        assert context == ""

    def test_hook_with_minimal_input(self):
        """Hook produces output with minimal valid input."""
        output = run_hook({"cwd": str(Path.cwd())})
        context = get_context(output)
        # Should produce output with cwd provided
        assert "<context-preservation" in context

    def test_hook_preserves_todos(self):
        """Hook includes todos in output."""
        output = run_hook({
            "todos": [{"status": "pending", "content": "Test todo item"}]
        })
        context = get_context(output)
        assert "Test todo item" in context
