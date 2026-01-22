#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
plan_approved.py - Write marker file when plan is approved via ExitPlanMode.

Hook types: PostToolUse, PermissionRequest (matcher: ExitPlanMode)

When ExitPlanMode is called (plan approved), this hook creates an empty marker
file at ~/.claude/plans/.plan_approved. The next session's SessionStart hook
detects this marker to inject plan execution mode.

Claude Code auto-injects the approved plan content on "Accept and clear",
so we just need the marker as a signal - not to store the plan path.

Idempotent: If marker already exists, skips creation (safe for both hooks to fire).
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


@hook_main("ExitPlanMode")
def main() -> None:
    log_debug("=== plan_approved.py ENTRY ===")
    raw = read_stdin_safe()
    log_debug(f"Raw input length: {len(raw)}")

    data = parse_hook_input(raw)
    log_debug(f"Parsed data keys: {list(data.keys()) if data else 'EMPTY'}")
    log_debug(f"tool_name: {data.get('tool_name', 'N/A') if data else 'N/A'}")
    hook_event = data.get("hook_event_name", "unknown") if data else "unknown"
    log_debug(f"hook_event_name: {hook_event}")

    if not data:
        log_debug("No data, exiting early")
        output_empty()
        return

    # Marker file path
    marker_path = Path.home() / ".claude" / "plans" / ".plan_approved"
    log_debug(f"Marker path: {marker_path}")

    # Idempotent: skip if marker already exists (safe for both hooks to fire)
    if marker_path.exists():
        log_debug("Marker already exists, skipping (idempotent)")
        output_empty()
        return

    marker_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        marker_path.touch()
        log_debug(f"Created plan marker via {hook_event}")
        log_debug(f"Marker exists after: {marker_path.exists()}")
    except OSError as e:
        log_debug(f"Failed to create marker: {e}")

    log_debug("=== plan_approved.py EXIT ===")
    output_empty()


if __name__ == "__main__":
    main()
