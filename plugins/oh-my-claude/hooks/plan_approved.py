#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
plan_approved.py - Write marker file when plan is approved via ExitPlanMode.

Hook type: PostToolUse (matcher: ExitPlanMode)

When ExitPlanMode is called (plan approved), this hook creates an empty marker
file at ~/.claude/plans/.plan_approved. The next session's SessionStart hook
detects this marker to inject plan execution mode. Claude Code auto-injects
the approved plan content, so the marker is just a signal, not storage.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    hook_main,
    log_debug,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)


@hook_main("PostToolUse")
def main() -> None:
    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        output_empty()
        return

    # Create empty marker file to signal plan was approved
    marker_path = Path.home() / ".claude" / "plans" / ".plan_approved"
    marker_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        marker_path.touch()
        log_debug(f"Created plan marker: {marker_path}")
    except OSError as e:
        log_debug(f"Failed to create marker: {e}")

    output_empty()


if __name__ == "__main__":
    main()
