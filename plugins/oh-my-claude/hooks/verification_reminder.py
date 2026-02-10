#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
verification_reminder.py
PostToolUse hook: Reminds Claude to verify agent claims after Task completion.
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

VERIFICATION_MESSAGE = """[Verification Required]

Agent task completed. VERIFY claims before proceeding:

1. **READ** - Check modified files directly (not just agent summary)
2. **RUN** - Execute tests if applicable
3. **CHECK** - Confirm output matches expected behavior
4. **COMPARE** - Review before/after if relevant

For full verification methodology, invoke the `verification` skill.

## Anti-Rationalization
- "The agent seems confident" → Confidence is not evidence. Read the actual code.
- "I trust subagents" → Trust but verify. Verification takes 2 min, debugging takes 30.

Trust but verify. Agent context is isolated from yours."""


@hook_main("PostToolUse")
def main() -> None:
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        return output_empty()

    # Skip for agent sessions (teammates verify their own work)
    if is_agent_session(data):
        return output_empty()

    tool_name = get_nested(data, "tool_name", default="")

    log_debug(f"tool_name={tool_name}")

    if tool_name == "Task":
        log_debug("Task completed, injecting verification reminder")
        output_context("PostToolUse", VERIFICATION_MESSAGE)
    else:
        return output_empty()


if __name__ == "__main__":
    main()
