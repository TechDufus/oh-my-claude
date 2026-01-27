#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Team Lifecycle Guardian Hook

Warns about active teams before session ends.
Events: Stop, PostToolUse (Teammate)
"""

import json
import sys
from pathlib import Path

# Hook utilities - inline to avoid external dependencies
def read_stdin_safe() -> str:
    """Read stdin safely."""
    try:
        return sys.stdin.read()
    except Exception:
        return ""

def output_empty():
    """Output empty response (continue normally)."""
    print(json.dumps({}))

def output_context(event: str, context: str):
    """Output context to inject."""
    print(json.dumps({
        event: {
            "additionalContext": context
        }
    }))

def log_debug(msg: str):
    """Log debug message to stderr."""
    import os
    if os.environ.get("HOOK_DEBUG") == "1":
        print(f"[team_lifecycle_guardian] {msg}", file=sys.stderr)


TEAMS_DIR = Path.home() / ".claude" / "teams"

ACTIVE_TEAM_WARNING = """[oh-my-claude: Active Team Detected]

You have active teammates. Consider graceful shutdown before ending:

1. `Teammate(operation="requestShutdown", team_name="...", target="...")` for each
2. Wait for `shutdown_approved` in inbox
3. `Teammate(operation="cleanup")`

Orphaned teammates may persist in ~/.claude/teams/
"""

CLEANUP_REMINDER = """[oh-my-claude: Teammate Cleanup]

Cleanup requested. Ensure all teammates have acknowledged shutdown first.
Check inbox for pending `shutdown_approved` messages.
"""


def get_active_teams() -> list[str]:
    """Find active teams by checking for config files."""
    if not TEAMS_DIR.exists():
        return []

    active = []
    for team_dir in TEAMS_DIR.iterdir():
        if team_dir.is_dir():
            config = team_dir / "config.json"
            if config.exists():
                active.append(team_dir.name)
    return active


def main():
    """Main hook entry point."""
    raw = read_stdin_safe()
    if not raw.strip():
        output_empty()
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        output_empty()
        return

    event = data.get("event", "")
    log_debug(f"Event: {event}")

    # Handle Stop event - warn about active teams
    if event == "Stop":
        active_teams = get_active_teams()
        if active_teams:
            log_debug(f"Active teams found: {active_teams}")
            output_context("Stop", ACTIVE_TEAM_WARNING)
            return

    # Handle PostToolUse for Teammate cleanup operation
    if event == "PostToolUse":
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})

        if tool_name == "Teammate":
            operation = tool_input.get("operation", "")
            if operation == "cleanup":
                # Remind about proper shutdown sequence
                active_teams = get_active_teams()
                if active_teams:
                    log_debug("Cleanup with active teams - reminding about shutdown")
                    output_context("PostToolUse", CLEANUP_REMINDER)
                    return

    output_empty()


if __name__ == "__main__":
    main()
