#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
session_start.py - Check for approved plan marker and inject execution context.

Hook type: SessionStart

When a new session starts, this hook:
1. Checks for ~/.claude/plans/.plan_approved marker existence
2. If found, injects ultrawork plan execution mode
3. Deletes marker (single-use)

Claude Code auto-injects the approved plan content, so the marker is just
a signal that triggers execution mode, not storage for the plan path.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    hook_main,
    log_debug,
    output_context,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)


PLAN_EXECUTION_CONTEXT = """[ULTRAWORK MODE ACTIVE - PLAN EXECUTION]

You have an APPROVED PLAN to execute. The plan content is already in your context.

## EXECUTION PROTOCOL

1. **Create todos** - Convert plan checkboxes to TodoWrite items
2. **Execute in order** - Follow the plan's execution order exactly
3. **Verify each step** - Run validator after each significant change
4. **Do NOT deviate** - The plan was researched and approved. Follow it.

## PLAN COMPLIANCE

| Allowed | NOT Allowed |
|---------|-------------|
| Following plan steps exactly | Adding features not in plan |
| Minor implementation details | Changing architecture decisions |
| Bug fixes discovered during work | Scope expansion |
| Asking about ambiguous plan items | Ignoring plan requirements |

If you discover the plan has a flaw:
1. STOP implementation
2. Explain the issue to the user
3. Get approval before changing approach

## COMPLETION

When ALL plan items are done:
1. Run full validation (tests, lints, type checks)
2. Summarize what was implemented
3. Note any deviations from plan (with reasons)
"""


def check_plan_execution() -> bool:
    """Check for approved plan marker. Returns True if marker exists."""
    marker_path = Path.home() / ".claude" / "plans" / ".plan_approved"

    if not marker_path.exists():
        log_debug("No plan marker found")
        return False

    try:
        # Consume the marker (single-use)
        marker_path.unlink()
        log_debug("Consumed plan marker")
        return True
    except OSError as e:
        log_debug(f"Error deleting marker: {e}")
        return False


@hook_main("SessionStart")
def main() -> None:
    raw = read_stdin_safe()
    _ = parse_hook_input(raw)  # Validate input format, not used for SessionStart

    # Check for plan execution marker
    should_inject = check_plan_execution()

    if not should_inject:
        output_empty()
        return

    # Inject plan execution context
    log_debug("Injecting plan execution context")
    output_context("SessionStart", PLAN_EXECUTION_CONTEXT)
    output_empty()


if __name__ == "__main__":
    main()
