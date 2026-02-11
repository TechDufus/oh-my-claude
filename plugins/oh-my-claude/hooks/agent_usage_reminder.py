#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
agent_usage_reminder.py
PostToolUse hook: Reminds Claude to delegate to agents instead of using
search tools directly. Only triggers once per session.
"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    get_nested,
    hook_main,
    is_agent_session,
    log_debug,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

# Tools that should trigger a reminder when used directly
DIRECT_SEARCH_TOOLS = {"Grep", "Glob"}

# Tools that indicate agent usage (no reminder needed)
AGENT_TOOLS = {"Task"}

# Track sessions where reminder was already shown
_reminded_sessions: set[str] = set()

# Track sessions where an agent has been used
_agent_used_sessions: set[str] = set()

REMINDER_MESSAGE = """[Agent Usage Reminder]

You used a search tool directly. Direct search = context tax. Agent search = parallelizable and context-protected.

| Instead of | Use |
|------------|-----|
| Grep/Glob directly | Explore (built-in agent for finding files/definitions) |
| Reading large files (>500 lines) | Task(subagent_type="oh-my-claude:librarian") |

For large file reads, delegate to librarian — it reads the full file and returns only what matters.

Benefits: Parallel execution, context protection, specialized expertise.

"I know what I'm looking for" → Even focused searches use context. Agents search while you think.
"Grep is faster" → Faster at typing, slower at tokens."""


@hook_main("PostToolUse")
def main() -> None:
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        return output_empty()

    # Skip for agent sessions (subagents and teammates use tools directly)
    if is_agent_session(data):
        return output_empty()

    # Get tool name from hook input
    tool_name = get_nested(data, "tool_name", default="")
    session_id = get_nested(data, "session_id", default="unknown")

    log_debug(f"tool_name={tool_name}, session_id={session_id}")

    # If Task tool was used, mark this session as having used agents
    if tool_name in AGENT_TOOLS:
        _agent_used_sessions.add(session_id)
        log_debug(f"session {session_id} has used agents")
        return output_empty()

    # If this session already got a reminder, don't show again
    if session_id in _reminded_sessions:
        return output_empty()

    # If agents have been used in this session, no reminder needed
    if session_id in _agent_used_sessions:
        return output_empty()

    # Check if a direct search tool was used
    if tool_name in DIRECT_SEARCH_TOOLS:
        _reminded_sessions.add(session_id)
        log_debug(f"showing agent reminder for session {session_id}")
        output_context("PostToolUse", REMINDER_MESSAGE)
    else:
        return output_empty()


if __name__ == "__main__":
    main()
