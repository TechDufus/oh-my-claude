#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
precompact_context.py
PreCompact hook: Preserves critical context before compaction.

Captures:
- Current mode (ultrawork/normal)
- Git state (branch, uncommitted changes)
- Recent files modified
"""

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

import json

from hook_utils import (
    get_nested,
    hook_main,
    log_debug,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)


def get_git_state(cwd: str | None = None) -> dict:
    """Get current git branch and uncommitted changes status."""
    try:
        # Get current branch
        branch_result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"

        # Check for uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        has_changes = bool(status_result.stdout.strip()) if status_result.returncode == 0 else False

        # Get staged files
        staged_result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        staged_files = staged_result.stdout.strip().split("\n") if staged_result.stdout.strip() else []

        return {
            "branch": branch,
            "uncommitted_changes": has_changes,
            "staged_files": staged_files[:10]
        }
    except Exception as e:
        log_debug(f"get_git_state failed: {e}")
        return {
            "branch": "unknown",
            "uncommitted_changes": False,
            "staged_files": []
        }


def get_recent_files(cwd: str | None = None, limit: int = 10) -> list[str]:
    """Get recently modified files from git."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~5"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().split("\n")
            return files[:limit]
        return []
    except Exception as e:
        log_debug(f"get_recent_files failed: {e}")
        return []


def detect_mode(data: dict) -> str:
    """Detect if ultrawork mode is active from session context."""
    session_context = get_nested(data, "session_context", default="")
    if "ultrawork" in session_context.lower() or "ulw" in session_context.lower():
        return "ultrawork"
    return "normal"


def format_context(
    mode: str,
    git_state: dict,
    recent_files: list[str],
    todos: list[dict],
    timestamp: str
) -> str:
    """Format preserved context for injection."""
    files_str = "\n".join(f"  - {f}" for f in recent_files) if recent_files else "  (none)"

    todo_str = ""
    if todos:
        for todo in todos[:5]:
            status = todo.get("status", "pending")
            content = todo.get("content", "")[:80]
            todo_str += f"  - [{status}] {content}\n"
    else:
        todo_str = "  (none)\n"

    staged_str = ", ".join(git_state.get("staged_files", [])[:5]) or "(none)"

    return f"""<context-preservation timestamp="{timestamp}">
## Session State Preserved

Mode: {mode}
Branch: {git_state.get('branch', 'unknown')}
Uncommitted Changes: {'Yes' if git_state.get('uncommitted_changes') else 'No'}
Staged Files: {staged_str}

### Recent Files Modified
{files_str}

### Active Todos
{todo_str}
</context-preservation>

IMPORTANT: This context was preserved before compaction. Resume work from this state."""


def output_system_message(message: str) -> None:
    """
    Output a system message for PreCompact hook.

    PreCompact hooks should use systemMessage at the top level,
    not hookSpecificOutput (which only supports PreToolUse,
    UserPromptSubmit, and PostToolUse).
    """
    response = {"systemMessage": message}
    print(json.dumps(response))


@hook_main("PreCompact")
def main() -> None:
    """Preserve critical context before compaction."""
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        log_debug("no valid input data")
        return output_empty()

    cwd = get_nested(data, "cwd", default=os.getcwd())

    mode = detect_mode(data)
    git_state = get_git_state(cwd)
    recent_files = get_recent_files(cwd)
    todos = get_nested(data, "todos", default=[])

    timestamp = datetime.now(timezone.utc).isoformat()

    context = format_context(mode, git_state, recent_files, todos, timestamp)
    log_debug(f"preserving context: mode={mode}, branch={git_state.get('branch')}")
    output_system_message(context)


if __name__ == "__main__":
    main()
