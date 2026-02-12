#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
PreToolUse hook that warns on risky Bash patterns (e.g., curl piped to shell).

Catastrophic command blocking has moved to safe_permissions.py (PermissionRequest).
This hook now only handles warnings via additionalContext.

Environment Variable: OMC_DANGER_BLOCK - default "1" (enabled). Set to "0" to disable.
"""

import json
import re
import sys
from pathlib import Path

# Add parent for hook_utils
sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import hook_main, log_debug, output_empty, parse_bool_env, parse_hook_input, read_stdin_safe

# Warn patterns - warn via additionalContext but allow
WARN_PATTERNS = [
    (r'\bcurl\s+.*\|\s*(ba)?sh', "piping curl to shell executes remote code. Safe alternative: download first, inspect, then run"),
    (r'\bwget\s+.*\|\s*(ba)?sh', "piping wget to shell executes remote code. Safe alternative: download first, inspect, then run"),
    (r'\bwget\s+.*&&\s*(ba)?sh', "wget followed by shell execution of downloaded content. Safe alternative: download first, inspect, then run"),
    (r'\bcurl\s+.*\|\s*base64\s+-d\s*\|\s*(ba)?sh', "piping curl through base64 decode to shell is obfuscated remote code execution. Safe alternative: download first, inspect, then run"),
]


def output_warn(message: str) -> None:
    """Warn but allow - injects warning into Claude's context."""
    response = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": f"WARNING: SECURITY WARNING: {message}. Proceed with caution."
        }
    }
    print(json.dumps(response))
    sys.exit(0)


@hook_main("PreToolUse")
def main() -> None:
    # Check if disabled
    if not parse_bool_env("OMC_DANGER_BLOCK", default=True):
        log_debug("Danger blocker disabled via OMC_DANGER_BLOCK")
        output_empty()
        return

    data = parse_hook_input(read_stdin_safe())
    if not data:
        output_empty()
        return

    tool_name = data.get("tool_name", "")
    if tool_name != "Bash":
        output_empty()
        return

    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    if not command:
        output_empty()
        return

    log_debug(f"Checking command: {command[:100]}...")

    # Check warn patterns (allow with warning)
    for pattern, reason in WARN_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_debug(f"WARNING: {reason}")
            output_warn(reason)
            return

    # Safe - allow through
    output_empty()


if __name__ == "__main__":
    main()  # pyright: ignore[reportCallIssue]
