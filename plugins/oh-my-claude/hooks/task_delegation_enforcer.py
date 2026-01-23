#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Task Delegation Enforcer Hook

Enforces that TaskCreate descriptions include a Task() delegation instruction.
This enforces the PATTERN - the agent is expected to execute the Task() call.
"""

import json
import sys


def output_deny(reason: str) -> None:
    print(json.dumps({"result": "deny", "reason": reason}))


def output_continue() -> None:
    print(json.dumps({"result": "continue"}))


def has_delegation_pattern(text: str) -> bool:
    """Check for Task(subagent_type=...) pattern using simple substring matching.

    Avoids regex fragility with nested parentheses.
    """
    text_lower = text.lower()
    return "task(" in text_lower and "subagent_type" in text_lower


def has_no_delegate_tag(text: str) -> bool:
    """Check for [NO-DELEGATE] escape hatch (case-insensitive)."""
    return "[no-delegate]" in text.lower()


def main():
    hook_input = json.loads(sys.stdin.read())
    tool_input = hook_input.get("tool_input", {})
    description = tool_input.get("description", "")

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
            "After creating, execute the Task() call to delegate the work."
        )
        return

    output_continue()


if __name__ == "__main__":
    main()
