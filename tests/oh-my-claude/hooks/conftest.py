"""Shared fixtures for hook tests."""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path for imports
# Tests are at: tests/oh-my-claude/hooks/
# Hooks are at: plugins/oh-my-claude/hooks/
REPO_ROOT = Path(__file__).parent.parent.parent.parent
HOOKS_DIR = REPO_ROOT / "plugins" / "oh-my-claude" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))


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
