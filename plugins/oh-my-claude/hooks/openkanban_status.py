#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""OpenKanban status integration - writes agent status when in OpenKanban terminal."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hook_utils import (
    get_nested,
    hook_main,
    log_debug,
    output_empty,
    parse_hook_input,
    read_stdin_safe,
)

CACHE_DIR = Path.home() / ".cache" / "openkanban-status"


def write_status(session: str, status: str) -> None:
    """Write status to cache file for session. Silent on failure."""
    try:
        status_file = CACHE_DIR / f"{session}.status"
        status_file.parent.mkdir(parents=True, exist_ok=True)
        status_file.write_text(status)
        log_debug(f"wrote status '{status}' to {status_file}")
    except Exception as e:
        log_debug(f"failed to write status: {e}")


def determine_status(data: dict) -> str | None:
    """
    Determine status from hook input data.

    Returns status string or None if no status change needed.
    """
    # SessionStart -> idle
    if "session_id" in data and not data.get("tool_name") and not data.get("prompt"):
        return "idle"

    # UserPromptSubmit -> working
    if "prompt" in data:
        return "working"

    # PreToolUse -> working (has tool_name but no tool_result)
    if "tool_name" in data and "tool_result" not in data:
        return "working"

    # PermissionRequest -> waiting
    if "permission" in data or get_nested(data, "tool_input") is not None:
        # PermissionRequest has tool_input but checking permission field is more explicit
        pass

    # Stop -> idle
    if "stopReason" in data:
        return "idle"

    return None


@hook_main("OpenKanbanStatus")
def main() -> None:
    # Fast path: not in OpenKanban terminal
    session = os.environ.get("OPENKANBAN_SESSION")
    if not session:
        return output_empty()

    raw = read_stdin_safe()
    data = parse_hook_input(raw)

    if not data:
        return output_empty()

    log_debug(f"session={session}, data_keys={list(data.keys())}")

    # Determine status from hook event type
    hook_event = get_nested(data, "hookEventName", default="")

    if hook_event == "SessionStart":
        write_status(session, "idle")
    elif hook_event == "UserPromptSubmit" and "prompt" in data:
        write_status(session, "working")
    elif hook_event == "PreToolUse" and "tool_name" in data and "tool_result" not in data:
        write_status(session, "working")
    elif hook_event == "PermissionRequest":
        write_status(session, "waiting")
    elif hook_event == "Stop" and "stopReason" in data:
        write_status(session, "idle")
    else:
        # Unknown hook type or missing required fields - check by data shape
        status = determine_status(data)
        if status:
            write_status(session, status)

    return output_empty()


if __name__ == "__main__":
    main()
