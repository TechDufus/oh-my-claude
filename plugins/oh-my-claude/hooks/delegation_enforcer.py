#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
delegation_enforcer.py - Context guidance for delegation in execution mode.

Hook type: PreToolUse on Edit|Write
Provides context reminder (not hard block) encouraging delegation to subagents.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    get_nested,
    get_session_context,
    hook_main,
    is_agent_session,
    log_debug,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# Patterns that indicate execution mode
EXECUTION_MARKERS = [
    "plan execution",
    "ultrawork",
    "ulw",
    "implement the following plan",
]

# Escape hatch marker
DIRECT_MARKER = "[direct]"

# Threshold for "short" file changes (lines)
SHORT_CHANGE_THRESHOLD = 20

DELEGATION_REMINDER = """[DELEGATION REMINDER] You're editing directly in main context. Consider delegating to:
- Task(subagent_type='oh-my-claude:general-purpose', prompt='...')
- Task(subagent_type='general-purpose', prompt='...')

Add [DIRECT] to proceed without delegation."""

TEAM_LEAD_REMINDER = """[DELEGATION REMINDER] You're editing directly in main context. Consider delegating via teammates or subagents:
- Task(subagent_type='oh-my-claude:general-purpose', prompt='...')
- Task(subagent_type='general-purpose', prompt='...')
- Or delegate via teammates for parallel collaboration

Add [DIRECT] to proceed without delegation."""


def has_direct_marker(tool_input: dict) -> bool:
    """Check if [DIRECT] escape hatch is present in tool input."""
    # Check various fields that might contain the marker
    for field in ["old_string", "new_string", "content", "file_path"]:
        value = tool_input.get(field, "")
        if isinstance(value, str) and DIRECT_MARKER in value.lower():
            return True
    return False


def is_short_change(tool_input: dict) -> bool:
    """Check if the change is under the threshold (lightweight edit)."""
    # For Edit tool, check new_string length
    new_string = tool_input.get("new_string", "")
    if new_string:
        line_count = new_string.count("\n") + 1
        if line_count < SHORT_CHANGE_THRESHOLD:
            log_debug(f"short change detected: {line_count} lines")
            return True

    # For Write tool, check content length
    content = tool_input.get("content", "")
    if content:
        line_count = content.count("\n") + 1
        if line_count < SHORT_CHANGE_THRESHOLD:
            log_debug(f"short write detected: {line_count} lines")
            return True

    return False


def is_execution_mode(data: dict) -> bool:
    """Detect if we're in execution mode based on context signals."""
    # Check recent context/conversation for execution markers
    # The hook input may include transcript or context hints
    transcript = get_nested(data, "transcript", default="")
    prompt = get_nested(data, "prompt", default="")

    # Combine available text sources
    context_text = f"{transcript} {prompt}".lower()

    for marker in EXECUTION_MARKERS:
        if marker in context_text:
            log_debug(f"execution mode detected via marker: {marker}")
            return True

    # Check if there are pending tasks (indicates active task tracking)
    # Note: We can't directly query TaskList from a hook, but the presence
    # of task-related context in the input might indicate this
    if "tasklist" in context_text or "pending task" in context_text:
        log_debug("execution mode detected via task references")
        return True

    return False


@hook_main("PreToolUse")
def main() -> None:
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        output_empty()
        return

    # Skip for agent sessions (subagents and teammates implement freely)
    if is_agent_session(data):
        return output_empty()

    tool_name = get_nested(data, "tool_name", default="")
    tool_input = get_nested(data, "tool_input", default={})

    log_debug(f"tool_name={tool_name}")

    # Only process Edit and Write tools
    if tool_name not in ("Edit", "Write"):
        output_empty()
        return

    # Escape hatch: [DIRECT] marker present
    if has_direct_marker(tool_input):
        log_debug("direct marker found, skipping reminder")
        output_empty()
        return

    # Escape hatch: short changes get no guidance
    if is_short_change(tool_input):
        log_debug("short change, skipping reminder")
        output_empty()
        return

    # Only show reminder in execution mode
    if not is_execution_mode(data):
        log_debug("not in execution mode, skipping reminder")
        output_empty()
        return

    # Output context reminder (continue, not block)
    # Team leads get a softer message mentioning teammate delegation
    session_ctx = get_session_context(data)
    reminder = TEAM_LEAD_REMINDER if session_ctx == "team_lead" else DELEGATION_REMINDER
    log_debug(f"showing delegation reminder (session_context={session_ctx})")
    output_context("PreToolUse", reminder)


if __name__ == "__main__":
    main()
