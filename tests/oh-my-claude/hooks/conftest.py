"""Shared fixtures for hook tests."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

# Add hooks directory to path for imports
# Tests are at: tests/oh-my-claude/hooks/
# Hooks are at: plugins/oh-my-claude/hooks/
REPO_ROOT = Path(__file__).parent.parent.parent.parent
HOOKS_DIR = REPO_ROOT / "plugins" / "oh-my-claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


# =============================================================================
# Shared helpers for integration tests
# =============================================================================


def run_hook(hook_path: Path, input_data: dict, env: dict[str, str] | None = None) -> dict:
    """Run a hook script via subprocess and return parsed JSON output.

    Args:
        hook_path: Absolute path to the hook script.
        input_data: Dictionary to pass as JSON on stdin.
        env: Optional environment variables. If None, inherits current env.

    Returns:
        Parsed JSON output, or empty dict if no output.
    """
    result = subprocess.run(
        [sys.executable, str(hook_path)],
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


def get_context(output: dict) -> str:
    """Extract additionalContext from hook output."""
    return output.get("hookSpecificOutput", {}).get("additionalContext", "")


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory for testing."""
    return tmp_path


@pytest.fixture
def nodejs_project(tmp_path):
    """Create a Node.js project structure."""
    (tmp_path / "package.json").write_text('{"name": "test"}')
    return tmp_path


@pytest.fixture
def python_project(tmp_path):
    """Create a Python project structure."""
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"')
    return tmp_path


@pytest.fixture
def go_project(tmp_path):
    """Create a Go project structure."""
    (tmp_path / "go.mod").write_text("module test")
    return tmp_path


@pytest.fixture
def rust_project(tmp_path):
    """Create a Rust project structure."""
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "test"')
    return tmp_path


@pytest.fixture
def makefile_project(tmp_path):
    """Create a Makefile-only project structure."""
    (tmp_path / "Makefile").write_text("test:\n\techo test")
    return tmp_path


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing transcript analysis."""
    return [
        {"role": "user", "content": "Fix the bug"},
        {"role": "assistant", "content": "I'll fix that bug now."},
        {
            "role": "assistant",
            "content": "",
            "tool_use": {"name": "Edit", "input": {"file": "test.py"}},
        },
        {
            "role": "tool_result",
            "content": "File edited successfully",
            "tool_use_id": "1",
        },
        {"role": "assistant", "content": "I've fixed the bug."},
    ]


@pytest.fixture
def sample_todos():
    """Sample todo list for testing."""
    return [
        {"content": "Fix bug", "status": "completed", "activeForm": "Fixing bug"},
        {"content": "Add tests", "status": "in_progress", "activeForm": "Adding tests"},
        {"content": "Update docs", "status": "pending", "activeForm": "Updating docs"},
    ]


# =============================================================================
# Agent Teams fixtures
# =============================================================================


@pytest.fixture
def teams_env(monkeypatch):
    """Enable agent teams via environment variable."""
    monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "1")
    yield
    monkeypatch.delenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", raising=False)


@pytest.fixture
def no_teams_env(monkeypatch):
    """Ensure agent teams is disabled."""
    monkeypatch.delenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", raising=False)


@pytest.fixture
def agent_session_input():
    """Hook input data representing an agent session (subagent or teammate)."""
    return {"agent_type": "oh-my-claude:worker", "session_id": "agent-123"}


@pytest.fixture
def team_lead_input():
    """Hook input data representing a team lead session (no agent_type)."""
    return {"session_id": "lead-456"}
