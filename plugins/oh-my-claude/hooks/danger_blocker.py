#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
PreToolUse hook that blocks catastrophic Bash commands and warns on risky ones.

Environment Variable: OMC_DANGER_BLOCK - default "1" (enabled). Set to "0" to disable.
"""

import json
import re
import sys
from pathlib import Path

# Add parent for hook_utils
sys.path.insert(0, str(Path(__file__).parent))
from hook_utils import hook_main, log_debug, output_empty, parse_bool_env, parse_hook_input, read_stdin_safe

# Catastrophic patterns - must block with JSON deny
CATASTROPHIC_PATTERNS = [
    # Mass delete at root or home (NOT subdirectories)
    # Matches: rm with -r flag, targeting exactly / or ~ (optionally quoted), with optional trailing flags
    (r'\brm\s+(-[a-zA-Z]+\s+)*["\']?/["\']?(\s|$)', "Blocks deletion of entire filesystem"),
    (r'\brm\s+(-[a-zA-Z]+\s+)*["\']?~["\']?(\s|$)', "Blocks deletion of entire home directory"),

    # sudo rm -rf anywhere (too dangerous even with paths)
    (r'\bsudo\s+rm\s+.*-[a-zA-Z]*r[a-zA-Z]*', "sudo rm -rf is blocked for safety"),

    # Fork bomb patterns
    (r':\(\)\s*\{.*:\s*\|.*\}', "Fork bomb detected"),
    (r':\s*\(\s*\)\s*\{', "Potential fork bomb"),

    # Disk destruction
    (r'\bdd\s+.*of=/dev/(sd|hd|nvme|vd)', "Blocks disk overwrite"),
    (r'\bmkfs\.\w+\s+/dev/', "Blocks filesystem creation on devices"),

    # System destruction
    (r'>\s*/dev/(sd|hd|nvme)', "Blocks writing directly to disk devices"),
]

# Warn patterns - warn via additionalContext but allow
WARN_PATTERNS = [
    (r'\bcurl\s+.*\|\s*(ba)?sh', "piping curl to shell executes remote code"),
    (r'\bwget\s+.*\|\s*(ba)?sh', "piping wget to shell executes remote code"),
]


def output_deny(reason: str) -> None:
    """Output denial response for PreToolUse hook."""
    response = {"decision": "deny", "reason": reason}
    print(json.dumps(response))
    sys.exit(0)


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

    # Check catastrophic patterns (block)
    for pattern, reason in CATASTROPHIC_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            log_debug(f"BLOCKED: {reason}")
            output_deny(f"CATASTROPHIC COMMAND BLOCKED: {reason}")
            return

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
