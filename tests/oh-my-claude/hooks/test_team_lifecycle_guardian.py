"""Tests for team_lifecycle_guardian hook."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "plugins"
    / "oh-my-claude"
    / "hooks"
    / "team_lifecycle_guardian.py"
)


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
        print(f"STDERR: {result.stderr}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


class TestStopEvent:
    """Tests for Stop event handling."""

    def test_stop_without_teams_dir(self, tmp_path):
        """Stop with no teams directory should pass through."""
        input_data = {"event": "Stop"}
        result = run_hook(input_data, tmp_path)

        # No warning when no teams exist
        if "Stop" in result:
            context = result["Stop"].get("additionalContext", "")
            assert "Active team" not in context.lower() or context == ""
        else:
            assert result == {}

    def test_stop_with_active_team(self, tmp_path):
        """Stop with active team should inject warning."""
        # Create a fake team
        teams_dir = tmp_path / ".claude" / "teams" / "my-team"
        teams_dir.mkdir(parents=True)
        (teams_dir / "config.json").write_text("{}")

        input_data = {"event": "Stop"}
        result = run_hook(input_data, tmp_path)

        # Should warn about active team
        assert "Stop" in result
        context = result["Stop"].get("additionalContext", "")
        assert "Active" in context or "team" in context.lower()

    def test_stop_with_empty_teams_dir(self, tmp_path):
        """Stop with empty teams directory should not warn."""
        teams_dir = tmp_path / ".claude" / "teams"
        teams_dir.mkdir(parents=True)
        # No team subdirectories

        input_data = {"event": "Stop"}
        result = run_hook(input_data, tmp_path)

        # No warning for empty teams dir
        if "Stop" in result:
            context = result["Stop"].get("additionalContext", "")
            assert "Active" not in context


class TestPostToolUseEvent:
    """Tests for PostToolUse Teammate handling."""

    def test_teammate_cleanup_with_active_teams(self, tmp_path):
        """Cleanup with active teams should remind about shutdown."""
        # Create a fake team
        teams_dir = tmp_path / ".claude" / "teams" / "my-team"
        teams_dir.mkdir(parents=True)
        (teams_dir / "config.json").write_text("{}")

        input_data = {
            "event": "PostToolUse",
            "tool_name": "Teammate",
            "tool_input": {"operation": "cleanup"},
        }
        result = run_hook(input_data, tmp_path)

        # Should remind about proper shutdown
        assert "PostToolUse" in result
        context = result["PostToolUse"].get("additionalContext", "")
        assert "shutdown" in context.lower() or "Cleanup" in context

    def test_teammate_cleanup_without_active_teams(self, tmp_path):
        """Cleanup without active teams should pass through."""
        input_data = {
            "event": "PostToolUse",
            "tool_name": "Teammate",
            "tool_input": {"operation": "cleanup"},
        }
        result = run_hook(input_data, tmp_path)

        # Should pass through without warning
        assert result == {} or "PostToolUse" not in result

    def test_teammate_other_operation(self, tmp_path):
        """Non-cleanup Teammate operations should pass through."""
        input_data = {
            "event": "PostToolUse",
            "tool_name": "Teammate",
            "tool_input": {"operation": "spawnTeam", "team_name": "test"},
        }
        result = run_hook(input_data, tmp_path)

        # Should pass through
        assert result == {} or "additionalContext" not in result.get("PostToolUse", {})


class TestEdgeCases:
    """Edge case tests."""

    def test_empty_input(self, tmp_path):
        """Empty input should return empty output."""
        result = run_hook({}, tmp_path)
        assert result == {}

    def test_invalid_json_handling(self, tmp_path):
        """Invalid JSON should not crash."""
        env = {"HOME": str(tmp_path), "PATH": "/usr/bin:/bin"}
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not valid json",
            capture_output=True,
            text=True,
            env=env,
        )
        # Should not crash
        assert result.returncode == 0

    def test_missing_event_field(self, tmp_path):
        """Missing event field should pass through."""
        result = run_hook({"some": "data"}, tmp_path)
        assert result == {}
