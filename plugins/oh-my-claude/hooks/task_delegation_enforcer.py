#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Task Delegation Enforcer Hook

Enforces that TaskCreate descriptions include a Task() delegation instruction.
This enforces the PATTERN - the agent is expected to execute the Task() call.
Also suggests team formation when 3+ tasks are created.
"""

import json
import os
import sys
from pathlib import Path


def get_session_state_file() -> Path:
    """Get session state file path, respecting OMC_SESSION_STATE_DIR for testing."""
    state_dir = os.environ.get("OMC_SESSION_STATE_DIR")
    if state_dir:
        return Path(state_dir) / "session_state.json"
    return Path.home() / ".claude" / "oh-my-claude" / "session_state.json"


def get_task_create_count() -> int:
    """Track TaskCreate calls in current session."""
    state_file = get_session_state_file()
    if not state_file.exists():
        return 0
    try:
        state = json.loads(state_file.read_text())
        return state.get("task_create_count", 0)
    except (json.JSONDecodeError, IOError):
        return 0


def increment_task_create_count() -> int:
    """Increment and return new count."""
    state_file = get_session_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    count = get_task_create_count() + 1
    state_file.write_text(json.dumps({"task_create_count": count}))
    return count


TEAM_SUGGESTION_CONTEXT = """[oh-my-claude: Team Formation Suggestion]

You've created 3+ tasks. Consider using Team formation for parallel execution:

```
Teammate(operation="spawnTeam", team_name="project-team")
# Then spawn teammates with your tasks
```

Benefits: Persistent workers, inbox communication, automatic unblocking.

Continue with subagents if tasks are sequential or simple.
"""


def output_deny(reason: str) -> None:
    print(json.dumps({"result": "deny", "reason": reason}))


def output_continue() -> None:
    print(json.dumps({"result": "continue"}))


def output_context(hook_event: str, context: str) -> None:
    """Output hook response with additional context."""
    response = {
        "hookSpecificOutput": {
            "hookEventName": hook_event,
            "additionalContext": context,
        }
    }
    print(json.dumps(response))


def has_delegation_pattern(text: str) -> bool:
    """Check for Task(subagent_type=...) or team pattern using simple substring matching.

    Avoids regex fragility with nested parentheses.
    """
    text_lower = text.lower()
    # Check for valid delegation pattern - subagent OR team
    has_subagent = "task(" in text_lower and "subagent_type" in text_lower
    has_team = "team_name" in text_lower and "name" in text_lower
    return has_subagent or has_team


def has_no_delegate_tag(text: str) -> bool:
    """Check for [NO-DELEGATE] escape hatch (case-insensitive)."""
    return "[no-delegate]" in text.lower()


def main():
    hook_input = json.loads(sys.stdin.read())
    tool_input = hook_input.get("tool_input", {})
    description = tool_input.get("description", "")
    text_lower = description.lower()

    # Skip if escape hatch present
    if has_no_delegate_tag(description):
        output_continue()
        return

    # Check for delegation pattern
    if not has_delegation_pattern(description):
        output_deny(
            "Add [NO-DELEGATE] to skip, or include delegation instruction:\n\n"
            "TaskCreate(\n"
            "  subject='Task title',\n"
            "  description='''\n"
            "    Task(subagent_type=\"oh-my-claude:worker\", prompt=\"...\")\n"
            "  '''\n"
            ")\n\n"
            "Tasks should be small and atomic (one file, one concern).\n"
            "If task is large, split into smaller dependent tasks first.\n\n"
            "After creating, execute the Task() call to delegate the work."
        )
        return

    # Track task creation and suggest team formation if 3+
    count = increment_task_create_count()
    if count >= 3:
        # Check if team is active (team_name in description suggests team usage)
        if "team_name" not in text_lower:
            output_context("PreToolUse", TEAM_SUGGESTION_CONTEXT)
            return

    output_continue()


if __name__ == "__main__":
    main()
